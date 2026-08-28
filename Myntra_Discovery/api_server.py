"""Live Discovery API: cached extract on GET, live Play/App Store scrape on POST.

Serves the static findings page from /discovery as well, so one process is enough:

    venv\\Scripts\\python.exe api_server.py
    open http://127.0.0.1:8000/
"""

from __future__ import annotations

import csv
import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from paths import (
    CLASSIFIED_MERGED,
    DISCOVERY_DIR,
    ENV_PATH,
    EXTRACT_PATH,
    ROOT,
    SNAPSHOT_PATH,
    SNAPSHOT_TMP,
)

os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ENV_PATH)

from pipeline import classify_relevance as C  # noqa: E402
from pipeline.build_extract import build_extract  # noqa: E402
from pipeline.build_snapshot import _write_json, assemble_snapshot  # noqa: E402
from scrapers import appstore, playstore  # noqa: E402

LIVE_PLAYSTORE = 200
LIVE_APPSTORE = 200
MIN_TEXT_LEN = 15

app = FastAPI(title="Myntra Discovery API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()
SCRAPE_LOCK = threading.Lock()
ACTIVE_JOB_ID: str | None = None

CLASSIFIED_COLUMNS = [
    "source", "id", "date", "text", "engagement_score",
    "rating_if_available", "relevant", "category", "key_phrase",
]


def _read_classified():
    path = CLASSIFIED_MERGED
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_classified(rows):
    path = CLASSIFIED_MERGED
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CLASSIFIED_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def _norm_playstore(entry):
    review_date = entry.get("at")
    return {
        "source": "playstore",
        "id": entry.get("reviewId") or "",
        "date": review_date.isoformat() if review_date else "",
        "text": (entry.get("content") or "").strip(),
        "engagement_score": entry.get("thumbsUpCount") or 0,
        "rating_if_available": entry.get("score") if entry.get("score") is not None else "",
    }


def _norm_appstore(entry):
    return {
        "source": "appstore",
        "id": entry.get("review_id") or "",
        "date": entry.get("date") or "",
        "text": (entry.get("review_text") or "").strip(),
        "engagement_score": entry.get("thumbs_up") or 0,
        "rating_if_available": entry.get("rating") if entry.get("rating") is not None else "",
    }


def _set_job(job_id, **kwargs):
    with JOB_LOCK:
        JOBS.setdefault(job_id, {})
        JOBS[job_id].update(kwargs)


def _run_scrape(job_id: str):
    global ACTIVE_JOB_ID
    if not SCRAPE_LOCK.acquire(blocking=False):
        _set_job(job_id, status="error", message="A scrape is already running.")
        return
    try:
        with JOB_LOCK:
            ACTIVE_JOB_ID = job_id
        _set_job(job_id, status="running", message="Fetching Play Store reviews…")
        play_raw = playstore.fetch_reviews(LIVE_PLAYSTORE)
        _set_job(
            job_id,
            message=f"Play Store {len(play_raw)} · fetching App Store…",
            playstore_fetched=len(play_raw),
        )
        app_raw = appstore.fetch_via_app_store_scraper(LIVE_APPSTORE)
        if not app_raw:
            app_raw = appstore.fetch_via_rss(LIVE_APPSTORE)
        _set_job(job_id, appstore_fetched=len(app_raw), message="Merging with cached corpus…")

        incoming = []
        for entry in play_raw:
            row = _norm_playstore(entry)
            if len(row["text"]) >= MIN_TEXT_LEN and row["id"]:
                incoming.append(row)
        for entry in app_raw:
            row = _norm_appstore(entry)
            if len(row["text"]) >= MIN_TEXT_LEN and row["id"]:
                incoming.append(row)

        existing = _read_classified()
        known = {(r.get("source"), r.get("id")) for r in existing}
        new_rows = [r for r in incoming if (r["source"], r["id"]) not in known]
        _set_job(job_id, new_unique=len(new_rows), message=f"Classifying {len(new_rows)} new reviews…")

        client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and new_rows:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

        classified_new = []
        for i, row in enumerate(new_rows, start=1):
            if client:
                verdict = C.classify_text(client, row["text"])
            else:
                verdict = {"relevant": False, "category": "", "key_phrase": ""}
            classified_new.append({
                **{k: row.get(k, "") for k in CLASSIFIED_COLUMNS if k not in C.NEW_COLUMNS},
                "relevant": verdict["relevant"],
                "category": C.norm(verdict["category"]),
                "key_phrase": C.norm(verdict["key_phrase"]),
            })
            if i % 20 == 0:
                _set_job(job_id, message=f"Classified {i}/{len(new_rows)} new reviews…")

        if classified_new:
            existing.extend(classified_new)
            _write_classified(existing)

        extract = build_extract()
        SNAPSHOT_TMP.parent.mkdir(parents=True, exist_ok=True)
        _write_json(SNAPSHOT_TMP, assemble_snapshot(extract))
        os.replace(SNAPSHOT_TMP, SNAPSHOT_PATH)
        _set_job(
            job_id,
            status="done",
            message=(
                f"Live scrape finished · Play Store {len(play_raw)} · "
                f"App Store {len(app_raw)} · {len(new_rows)} new unique"
            ),
            extract=extract,
            playstore_fetched=len(play_raw),
            appstore_fetched=len(app_raw),
            new_unique=len(new_rows),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:  # noqa: BLE001
        _set_job(job_id, status="error", message=str(exc))
    finally:
        with JOB_LOCK:
            if ACTIVE_JOB_ID == job_id:
                ACTIVE_JOB_ID = None
        SCRAPE_LOCK.release()


@app.get("/api/health")
def health():
    with JOB_LOCK:
        active = ACTIVE_JOB_ID
    return {"ok": True, "scrape_busy": SCRAPE_LOCK.locked(), "active_job_id": active}


@app.get("/api/extract")
def get_extract():
    if EXTRACT_PATH.exists():
        return json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    return build_extract()


@app.post("/api/scrape")
def start_scrape():
    with JOB_LOCK:
        if SCRAPE_LOCK.locked() and ACTIVE_JOB_ID:
            return {"job_id": ACTIVE_JOB_ID, "already_running": True}
    job_id = uuid.uuid4().hex[:12]
    _set_job(
        job_id,
        status="queued",
        message="Queued live scrape…",
        playstore_fetched=0,
        appstore_fetched=0,
        new_unique=0,
    )
    threading.Thread(target=_run_scrape, args=(job_id,), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/scrape/{job_id}")
def scrape_status(job_id: str):
    with JOB_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return {"status": "error", "message": "Unknown job"}
    return job


@app.get("/")
def index():
    return FileResponse(DISCOVERY_DIR / "index.html")


@app.get("/data.json")
def data_file():
    return FileResponse(EXTRACT_PATH)


if __name__ == "__main__":
    import uvicorn

    print("Discovery API + findings page: http://127.0.0.1:8000/")
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=False)

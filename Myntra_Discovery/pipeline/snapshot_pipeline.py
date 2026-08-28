"""Live scrape pipeline that writes a NEW snapshot to a caller-chosen path.

A failed scrape raises and never touches data/snapshot.json. The classified
CSV is updated only after the dest snapshot file has been written successfully.
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import CLASSIFIED_MERGED as CLASSIFIED_PATH, ENV_PATH, ROOT

load_dotenv(ENV_PATH)

from pipeline import classify_relevance as C  # noqa: E402
from pipeline.build_snapshot import _write_json, assemble_snapshot  # noqa: E402
from scrapers import appstore, playstore  # noqa: E402

LIVE_PLAYSTORE = 200
LIVE_APPSTORE = 200
MIN_TEXT_LEN = 15
CLASSIFIED_COLUMNS = [
    "source", "id", "date", "text", "engagement_score",
    "rating_if_available", "relevant", "category", "key_phrase",
]
Progress = Callable[[str], None]


def _read_classified():
    path = Path(CLASSIFIED_PATH)
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_classified(rows):
    path = Path(CLASSIFIED_PATH)
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


def run_live_scrape_to_path(dest: str | Path, progress: Progress | None = None) -> dict:
    """Fetch new store reviews, classify unseen rows, write snapshot to dest.

    Does not replace data/snapshot.json. Caller should os.replace(dest, snapshot)
    only after this returns.
    """
    def note(msg: str) -> None:
        if progress:
            progress(msg)

    note("Fetching Play Store reviews…")
    play_raw = playstore.fetch_reviews(LIVE_PLAYSTORE)
    note(f"Play Store {len(play_raw)} · fetching App Store…")
    app_raw = appstore.fetch_via_app_store_scraper(LIVE_APPSTORE)
    if not app_raw:
        app_raw = appstore.fetch_via_rss(LIVE_APPSTORE)
    note(f"App Store {len(app_raw)} · merging with cached corpus…")

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
    note(f"Classifying {len(new_rows)} new reviews…")

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
            note(f"Classified {i}/{len(new_rows)} new reviews…")

    merged = list(existing)
    if classified_new:
        merged.extend(classified_new)

    fd, tmp_csv = tempfile.mkstemp(suffix=".csv", prefix="classified_")
    os.close(fd)
    try:
        with open(tmp_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CLASSIFIED_COLUMNS)
            w.writeheader()
            w.writerows(merged)
        snap = assemble_snapshot(classified_path=tmp_csv)
    finally:
        try:
            os.remove(tmp_csv)
        except OSError:
            pass

    dest = Path(dest)
    if not dest.is_absolute():
        dest = ROOT / dest
    _write_json(dest, snap)

    if classified_new:
        _write_classified(merged)

    note(
        f"Live scrape finished · Play Store {len(play_raw)} · "
        f"App Store {len(app_raw)} · {len(new_rows)} new unique"
    )
    snap["_scrape"] = {
        "playstore_fetched": len(play_raw),
        "appstore_fetched": len(app_raw),
        "new_unique": len(new_rows),
    }
    return snap

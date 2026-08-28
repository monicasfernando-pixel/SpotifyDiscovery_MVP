"""Parse manually-collected Reddit .txt files into the shared source schema.

Each file in data/reddit_raw_txt/ becomes ONE row:
    source = "reddit"
    id     = filename without extension
    text   = full file content (verbatim)
    date   = the post's created_utc (if present) as an ISO date, else ""
    engagement_score = the post's score/ups (if present), else ""
    rating_if_available = "" (not applicable to Reddit)

The files are raw Reddit JSON API dumps, so dates/scores are read from the
JSON when possible, with a regex fallback for any non-JSON files.

Output -> data/reddit_manual_parsed.csv (schema matches all_raw_sources.csv).
"""

import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import REDDIT_PARSED as OUTPUT_PATH, REDDIT_RAW_TXT as INPUT_DIR

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

COLUMNS = ["source", "id", "date", "text", "engagement_score", "rating_if_available"]


def _iso_date(epoch):
    try:
        return datetime.fromtimestamp(float(epoch), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _find_first_post(obj):
    """Depth-first search for the first Reddit submission (kind == 't3')."""
    if isinstance(obj, dict):
        if obj.get("kind") == "t3" and isinstance(obj.get("data"), dict):
            return obj["data"]
        for value in obj.values():
            found = _find_first_post(value)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_first_post(value)
            if found:
                return found
    return None


def extract_date_and_score(content):
    """Return (date, engagement_score) extracted from the file content."""
    # Preferred: parse the Reddit JSON and read the post's fields.
    try:
        data = json.loads(content)
    except (ValueError, json.JSONDecodeError):
        data = None

    if data is not None:
        post = _find_first_post(data)
        if post:
            date = _iso_date(post.get("created_utc"))
            score = post.get("score")
            if score is None:
                score = post.get("ups")
            return date, ("" if score is None else score)

    # Fallback for non-JSON text: regex for an epoch, an ISO date, or a score.
    date = ""
    m = re.search(r'"created_utc":\s*([0-9]+(?:\.[0-9]+)?)', content)
    if m:
        date = _iso_date(m.group(1))
    else:
        m = re.search(r"\b(20[12]\d-\d{2}-\d{2})\b", content)
        if m:
            date = m.group(1)

    score = ""
    m = re.search(r'"score":\s*([0-9]+)', content) or re.search(r'"ups":\s*([0-9]+)', content)
    if m:
        score = int(m.group(1))
    return date, score


def main():
    if not INPUT_DIR.is_dir():
        raise SystemExit(f"Folder not found: {INPUT_DIR}")

    paths = sorted(INPUT_DIR.glob("*.txt"))
    rows = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()

        file_id = path.stem
        date, score = extract_date_and_score(content)
        rows.append(
            {
                "source": "reddit",
                "id": file_id,
                "date": date,
                "text": content,
                "engagement_score": score,
                "rating_if_available": "",
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows: {len(rows)}")
    print(f"Wrote {OUTPUT_PATH}\n")
    print("First 3 rows (text truncated for display):")
    for row in rows[:3]:
        preview = row["text"].replace("\n", " ")[:200]
        print("-" * 60)
        print(f"source           : {row['source']}")
        print(f"id               : {row['id']}")
        print(f"date             : {row['date'] or 'null'}")
        print(f"engagement_score : {row['engagement_score'] if row['engagement_score'] != '' else 'null'}")
        print(f"rating_if_available: null")
        print(f"text (200 chars) : {preview}")


if __name__ == "__main__":
    main()

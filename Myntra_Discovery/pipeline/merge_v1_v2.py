"""Merge Play/App Store v1+v2 with YouTube + Reddit into one normalized corpus.

Dedupes by (source, id). Drops text shorter than 15 characters.
Writes data/all_raw_sources_merged.csv.
"""

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import (
    ALL_RAW_SOURCES_MERGED as OUT,
    APPSTORE_V1,
    APPSTORE_V2,
    PLAYSTORE_V1,
    PLAYSTORE_V2,
    REDDIT_PARSED,
    YOUTUBE_COMMENTS,
)

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
MIN_TEXT_LEN = 15
COLUMNS = ["source", "id", "date", "text", "engagement_score", "rating_if_available"]


def to_int(value):
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def read_csv(path):
    if not os.path.exists(path):
        print(f"  missing {path}")
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def collect_comments(obj, acc):
    if isinstance(obj, dict):
        if obj.get("kind") == "t1" and isinstance(obj.get("data"), dict):
            body = (obj["data"].get("body") or "").strip()
            if body and body not in ("[deleted]", "[removed]"):
                acc.append(body)
        for v in obj.values():
            collect_comments(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            collect_comments(v, acc)


def find_post(obj):
    if isinstance(obj, dict):
        if obj.get("kind") == "t3" and isinstance(obj.get("data"), dict):
            return obj["data"]
        for v in obj.values():
            found = find_post(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_post(v)
            if found:
                return found
    return None


def readable_reddit(raw):
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return raw
    post = find_post(data)
    parts = []
    if post:
        title = (post.get("title") or "").strip()
        body = (post.get("selftext") or "").strip()
        if title:
            parts.append(title)
        if body:
            parts.append(body)
    comments = []
    collect_comments(data, comments)
    if comments:
        parts.append("COMMENTS:\n" + "\n---\n".join(comments))
    return "\n\n".join(parts) or raw


def add_review(rows, source, raw):
    text = (raw.get("review_text") or "").strip()
    if len(text) < MIN_TEXT_LEN:
        return
    rows.append(
        {
            "source": source,
            "id": raw.get("review_id", ""),
            "date": raw.get("date", ""),
            "text": text,
            "engagement_score": to_int(raw.get("thumbs_up")),
            "rating_if_available": raw.get("rating", "") or "",
        }
    )


def dedupe(rows):
    seen = set()
    out = []
    for r in rows:
        key = (r["source"], r["id"] or r["text"][:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    rows = []

    for path in (PLAYSTORE_V1, PLAYSTORE_V2):
        chunk = read_csv(path)
        print(f"  {path}: {len(chunk)} raw")
        for raw in chunk:
            add_review(rows, "playstore", raw)

    for path in (APPSTORE_V1, APPSTORE_V2):
        chunk = read_csv(path)
        print(f"  {path}: {len(chunk)} raw")
        for raw in chunk:
            add_review(rows, "appstore", raw)

    yt = read_csv(YOUTUBE_COMMENTS)
    print(f"  youtube_comments.csv: {len(yt)} raw")
    for raw in yt:
        text = (raw.get("comment_text") or "").strip()
        if len(text) < MIN_TEXT_LEN:
            continue
        rows.append(
            {
                "source": "youtube",
                "id": raw.get("comment_id", ""),
                "date": raw.get("date", ""),
                "text": text,
                "engagement_score": to_int(raw.get("like_count")),
                "rating_if_available": "",
            }
        )

    reddit = read_csv(REDDIT_PARSED)
    print(f"  reddit_manual_parsed.csv: {len(reddit)} raw")
    for raw in reddit:
        text = readable_reddit(raw.get("text") or "").strip()
        if len(text) < MIN_TEXT_LEN:
            continue
        rows.append(
            {
                "source": "reddit",
                "id": raw.get("id", ""),
                "date": raw.get("date", ""),
                "text": text,
                "engagement_score": to_int(raw.get("engagement_score")),
                "rating_if_available": "",
            }
        )

    before = len(rows)
    rows = dedupe(rows)
    print(f"\nBefore dedupe (post length filter): {before}")
    print(f"After dedupe: {len(rows)}")
    counts = Counter(r["source"] for r in rows)
    for s in ("playstore", "appstore", "youtube", "reddit"):
        print(f"  {s:10} {counts.get(s, 0)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()

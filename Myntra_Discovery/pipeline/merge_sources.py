"""Merge all source CSVs in data/ into one normalized dataset.

Reads the Play Store, App Store, Reddit, and YouTube CSVs, maps each into a
common schema, drops duplicates and empty / very short text (<15 chars), and
writes data/all_raw_sources.csv.

Unified schema:
    source, id, date, text, engagement_score, rating_if_available
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ALL_RAW_SOURCES as OUTPUT_PATH, RAW_DIR

# Some review/comment text can be long; lift the CSV field size limit.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MIN_TEXT_LEN = 15

OUTPUT_COLUMNS = [
    "source",
    "id",
    "date",
    "text",
    "engagement_score",
    "rating_if_available",
]


def to_int(value):
    """Best-effort convert an engagement value to int, defaulting to 0."""
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def map_review(row):
    """Play Store / App Store reviews share the same schema."""
    return {
        "id": row.get("review_id", ""),
        "date": row.get("date", ""),
        "text": row.get("review_text", "") or "",
        "engagement_score": to_int(row.get("thumbs_up")),
        "rating_if_available": row.get("rating", "") or "",
    }


def map_youtube(row):
    return {
        "id": row.get("comment_id", ""),
        "date": row.get("date", ""),
        "text": row.get("comment_text", "") or "",
        "engagement_score": to_int(row.get("like_count")),
        "rating_if_available": "",
    }


def map_reddit(row):
    # Combine title + body for posts; comments keep just their own text.
    title = (row.get("title", "") or "").strip()
    body = (row.get("text", "") or "").strip()
    if row.get("comment_or_post") == "comment":
        text = body
    else:
        text = f"{title}\n\n{body}".strip() if title else body
    return {
        "id": row.get("post_id", ""),
        "date": row.get("date", ""),
        "text": text,
        "engagement_score": to_int(row.get("upvotes")),
        "rating_if_available": "",
    }


# filename -> (canonical source label, mapping function)
SOURCES = {
    "playstore_reviews.csv": ("playstore", map_review),
    "appstore_reviews.csv": ("appstore", map_review),
    "reddit_posts.csv": ("reddit", map_reddit),
    "youtube_comments.csv": ("youtube", map_youtube),
}


def load_source(filename, source_label, mapper, seen, counts):
    path = RAW_DIR / filename
    rows = []
    if not os.path.exists(path):
        print(f"  {filename}: not found, skipping.")
        return rows

    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            mapped = mapper(raw)
            text = (mapped["text"] or "").strip()
            if len(text) < MIN_TEXT_LEN:
                continue

            dedup_key = (source_label, mapped["id"], text)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            rows.append(
                {
                    "source": source_label,
                    "id": mapped["id"],
                    "date": mapped["date"],
                    "text": text,
                    "engagement_score": mapped["engagement_score"],
                    "rating_if_available": mapped["rating_if_available"],
                }
            )
            counts[source_label] += 1

    print(f"  {filename}: {counts[source_label]} rows kept")
    return rows


def main():
    seen = set()
    counts = Counter()
    all_rows = []

    print("Merging sources from data/raw ...")
    for filename, (source_label, mapper) in SOURCES.items():
        all_rows.extend(load_source(filename, source_label, mapper, seen, counts))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows to {OUTPUT_PATH}")
    print("Per-source breakdown:")
    for source_label in ("playstore", "appstore", "reddit", "youtube"):
        print(f"  {source_label:10} {counts[source_label]}")


if __name__ == "__main__":
    main()

"""Keyword-filter the new Play Store / App Store v2 scrapes.

Same pipeline as before:
  - normalize to source, id, date, text, engagement_score, rating_if_available
  - drop empty / very short text (<15 chars) and duplicates
  - case-insensitive match on wishlist / save / favourite keywords

Writes matches to data/relevant_subset_v2.csv (does not overwrite v1).
"""

import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import APPSTORE_V2, PLAYSTORE_V2, RELEVANT_SUBSET_V2 as OUTPUT_PATH

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MIN_TEXT_LEN = 15
OUTPUT_COLUMNS = [
    "source",
    "id",
    "date",
    "text",
    "engagement_score",
    "rating_if_available",
    "matched_keywords",
]

KEYWORDS = [
    "wishlist",
    "wish list",
    "saved",
    "favourite",
    "favorite",
    "heart icon",
    "bookmark",
]

SOURCES = [
    ("playstore", PLAYSTORE_V2),
    ("appstore", APPSTORE_V2),
]


def to_int(value):
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def load_normalized(source, path):
    if not os.path.exists(path):
        print(f"  {path}: not found, skipping.")
        return []
    rows = []
    seen = set()
    kept = 0
    raw = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for raw_row in csv.DictReader(fh):
            raw += 1
            text = (raw_row.get("review_text") or "").strip()
            if len(text) < MIN_TEXT_LEN:
                continue
            rid = raw_row.get("review_id", "")
            key = (source, rid, text)
            if key in seen:
                continue
            seen.add(key)
            kept += 1
            rows.append(
                {
                    "source": source,
                    "id": rid,
                    "date": raw_row.get("date", ""),
                    "text": text,
                    "engagement_score": to_int(raw_row.get("thumbs_up")),
                    "rating_if_available": raw_row.get("rating", "") or "",
                }
            )
    print(f"  {path}: {raw} raw -> {kept} kept after short/dedupe filter")
    return rows


def matching_keywords(text, keywords):
    lower = text.lower()
    return [kw for kw in keywords if kw in lower]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print("Normalizing v2 scrapes...")
    all_rows = []
    for source, path in SOURCES:
        all_rows.extend(load_normalized(source, path))

    keywords = [k.lower() for k in KEYWORDS]
    matches = []
    by_source = Counter()
    by_kw = Counter()
    by_source_kw = defaultdict(Counter)

    for row in all_rows:
        hits = matching_keywords(row["text"], keywords)
        if not hits:
            continue
        row = dict(row)
        row["matched_keywords"] = "; ".join(hits)
        matches.append(row)
        by_source[row["source"]] += 1
        for kw in hits:
            by_kw[kw] += 1
            by_source_kw[row["source"]][kw] += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(matches)

    print(f"\nTotal matching rows: {len(matches)} / {len(all_rows)} kept reviews")
    print("Per-source breakdown:")
    for source in ("playstore", "appstore"):
        print(f"  {source:10} {by_source.get(source, 0)}")

    print("\nPer-keyword hits (a row can match more than one):")
    for kw in keywords:
        if by_kw.get(kw):
            print(f"  {kw:12} {by_kw[kw]}")

    print("\nKeyword x source:")
    for source in ("playstore", "appstore"):
        if not by_source_kw[source]:
            continue
        bits = ", ".join(f"{k}={n}" for k, n in by_source_kw[source].most_common())
        print(f"  {source}: {bits}")

    print(f"\nSaved matching rows to {OUTPUT_PATH}")
    print("\nSample matches:")
    for i, row in enumerate(matches[:12], 1):
        preview = row["text"].replace("\n", " ")[:180]
        print(f"[{i}] {row['source']} | {row['matched_keywords']} | rating={row['rating_if_available']}")
        print(f"    {preview}")


if __name__ == "__main__":
    main()

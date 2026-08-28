"""Filter the merged dataset for wishlist/save/favourite-related mentions.

Reads data/all_raw_sources.csv, keeps rows whose `text` contains any target
keyword (case-insensitive), prints a total + per-source breakdown, and writes
the matching rows (all original columns intact) to data/relevant_subset.csv.
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ALL_RAW_SOURCES as INPUT_PATH, RELEVANT_SUBSET as OUTPUT_PATH

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

KEYWORDS = [
    "wishlist",
    "wish list",
    "saved",
    "favourite",
    "favorite",
    "heart icon",
    "bookmark",
]


def main():
    if not os.path.exists(INPUT_PATH):
        raise SystemExit(f"Input not found: {INPUT_PATH}. Run merge_sources.py first.")

    keywords = [k.lower() for k in KEYWORDS]
    counts = Counter()
    matches = []

    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        for row in reader:
            text = (row.get("text", "") or "").lower()
            if any(kw in text for kw in keywords):
                matches.append(row)
                counts[row.get("source", "")] += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)

    print(f"Total matching rows: {len(matches)}")
    print("Per-source breakdown:")
    for source in ("playstore", "appstore", "youtube", "reddit"):
        if counts.get(source):
            print(f"  {source:10} {counts[source]}")
    # Surface any other sources not in the expected list.
    for source, n in counts.items():
        if source not in ("playstore", "appstore", "youtube", "reddit"):
            print(f"  {source:10} {n}")

    print(f"\nSaved matching rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

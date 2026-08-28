"""Concatenate the merged sources with the manually-parsed Reddit rows.

Aligns columns across both CSVs and writes data/all_raw_sources_final.csv.
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ALL_RAW_SOURCES, ALL_RAW_SOURCES_FINAL as OUTPUT_PATH, REDDIT_PARSED

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

INPUTS = [ALL_RAW_SOURCES, REDDIT_PARSED]


def read_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def main():
    # Build the union of columns, preserving first-seen order.
    columns = []
    datasets = []
    for path in INPUTS:
        if not os.path.exists(path):
            print(f"  {path}: not found, skipping.")
            continue
        cols, rows = read_csv(path)
        for c in cols:
            if c not in columns:
                columns.append(c)
        datasets.append((path, rows))

    total = 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for path, rows in datasets:
            for row in rows:
                writer.writerow({c: row.get(c, "") for c in columns})
            total += len(rows)
            print(f"  {path}: {len(rows)} rows")

    print(f"\nNew total row count: {total}")
    print(f"Wrote {OUTPUT_PATH} with columns: {columns}")


if __name__ == "__main__":
    main()

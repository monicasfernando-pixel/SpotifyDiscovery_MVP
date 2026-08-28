"""Classify only new v1+v2 merged rows, reuse existing labels, write merged classified CSV."""

import csv
import os
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import (
    ALL_RAW_SOURCES_MERGED as MERGED_PATH,
    CLASSIFIED_FINAL as EXISTING_PATH,
    CLASSIFIED_MERGED as OUTPUT_PATH,
    ENV_PATH,
    MERGED_STATS,
)
from pipeline import classify_relevance as C

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

KEYWORDS = [
    "wishlist", "wish list", "saved", "favourite", "favorite", "heart icon", "bookmark",
]
BUCKETS = [
    ("Forgot / went stale", ["forget", "forgot", "stale", "unavailab", "out of stock", "stock"]),
    ("Wishlist / save / favourite", ["wishlist", "favourite", "favorite", "heart", "saved", "save"]),
    ("Price / sale timing", ["price", "sale", "timing", "discount", "money", "afford"]),
    ("Comparison shopping", ["comparison", "compare"]),
    ("Size / fit uncertainty", ["size", "fit"]),
    ("Purchase hesitation (other)", ["hesitat", "delay", "defer", "confusion", "restriction", "confidence", "intent"]),
]


def bucketize(cat):
    c = (cat or "").lower()
    for name, keys in BUCKETS:
        if any(k in c for k in keys):
            return name
    return "Other / uncategorized"


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    load_dotenv(ENV_PATH)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Missing ANTHROPIC_API_KEY in .env.")

    merged = read(MERGED_PATH)
    existing = {(r["source"], r["id"]): r for r in read(EXISTING_PATH)}
    todo = [r for r in merged if (r["source"], r["id"]) not in existing]
    print(f"Merged corpus: {len(merged)}")
    print(f"Already classified: {len(merged) - len(todo)}")
    print(f"New to classify: {len(todo)}")

    client = Anthropic(api_key=api_key)
    fieldnames = ["source", "id", "date", "text", "engagement_score",
                  "rating_if_available", "relevant", "category", "key_phrase"]

    classified_new = []
    for start in range(0, len(todo), C.BATCH_SIZE):
        batch = todo[start:start + C.BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=C.BATCH_SIZE) as pool:
            verdicts = list(
                pool.map(lambda r: C.classify_text(client, r.get("text", "") or ""), batch)
            )
        for row, verdict in zip(batch, verdicts):
            classified_new.append({
                **{k: row.get(k, "") for k in fieldnames if k not in C.NEW_COLUMNS},
                "relevant": verdict["relevant"],
                "category": C.norm(verdict["category"]),
                "key_phrase": C.norm(verdict["key_phrase"]),
            })
        print(f"  classified {min(start + C.BATCH_SIZE, len(todo))}/{len(todo)}")
        write(OUTPUT_PATH, classified_new, fieldnames)  # partial new-only checkpoint
        if start + C.BATCH_SIZE < len(todo):
            time.sleep(C.BATCH_DELAY)

    out = []
    for row in merged:
        old = existing.get((row["source"], row["id"]))
        if old:
            out.append({
                "source": row["source"],
                "id": row["id"],
                "date": row["date"],
                "text": row["text"],
                "engagement_score": row["engagement_score"],
                "rating_if_available": row["rating_if_available"],
                "relevant": old.get("relevant", ""),
                "category": old.get("category", ""),
                "key_phrase": old.get("key_phrase", ""),
            })
        else:
            # filled below from classified_new map
            out.append(None)

    new_map = {(r["source"], r["id"]): r for r in classified_new}
    filled = []
    for i, row in enumerate(merged):
        if out[i] is not None:
            filled.append(out[i])
        else:
            filled.append(new_map[(row["source"], row["id"])])

    write(OUTPUT_PATH, filled, fieldnames)

    total = len(filled)
    relevant = [r for r in filled if str(r.get("relevant", "")).lower() == "true"]
    src_all = Counter(r["source"] for r in filled)
    src_rel = Counter(r["source"] for r in relevant)
    buckets = Counter(bucketize(r.get("category", "")) for r in relevant)
    kw = 0
    kw_src = Counter()
    kws = [k.lower() for k in KEYWORDS]
    for r in filled:
        t = (r.get("text") or "").lower()
        if any(k in t for k in kws):
            kw += 1
            kw_src[r["source"]] += 1

    print(f"\nWrote {total} rows to {OUTPUT_PATH}")
    print(f"Relevant: {len(relevant)} / {total} ({100*len(relevant)/total:.1f}%)")
    print("Relevant by source:")
    for s in ("playstore", "youtube", "reddit", "appstore"):
        print(f"  {s}: {src_rel.get(s, 0)} of {src_all.get(s, 0)}")
    print(f"Keyword-adjacent: {kw}")
    print("Keywords by source:", dict(kw_src))
    print("Buckets:")
    for b, n in buckets.most_common():
        print(f"  {n:3}  {b}")

    # dump a tiny stats sidecar for the page update
    MERGED_STATS.parent.mkdir(parents=True, exist_ok=True)
    with MERGED_STATS.open("w", encoding="utf-8") as fh:
        fh.write(f"total={total}\n")
        fh.write(f"relevant={len(relevant)}\n")
        fh.write(f"keyword={kw}\n")
        for s in ("playstore", "youtube", "reddit", "appstore"):
            fh.write(f"rel_{s}={src_rel.get(s, 0)}\n")
            fh.write(f"all_{s}={src_all.get(s, 0)}\n")
        for b, n in buckets.most_common():
            fh.write(f"bucket|{b}|{n}\n")


if __name__ == "__main__":
    main()

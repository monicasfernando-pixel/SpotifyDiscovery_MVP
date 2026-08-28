"""Classify the new Reddit threads and reprint the prior analysis on the full set.

The 1,973 already-classified rows are reused. The 11 Reddit dumps are converted
to readable title + body + comments (so we don't send raw JSON to the API),
classified with the same prompt, then the combined set is summarized.
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict

from dotenv import load_dotenv
from anthropic import Anthropic
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import (
    CLASSIFIED as CLASSIFIED_PATH,
    CLASSIFIED_FINAL as OUTPUT_PATH,
    ENV_PATH,
    REDDIT_PARSED as REDDIT_PARSED_PATH,
)
from pipeline import classify_relevance as C

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

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

BUCKETS = [
    ("Forgot / went stale", ["forget", "forgot", "stale", "unavailab", "out of stock", "stock"]),
    ("Wishlist / save / favourite", ["wishlist", "favourite", "favorite", "heart", "saved", "save"]),
    ("Price / sale timing", ["price", "sale", "timing", "discount", "money", "afford"]),
    ("Comparison shopping", ["comparison", "compare"]),
    ("Size / fit uncertainty", ["size", "fit"]),
    ("Purchase hesitation (other)", ["hesitat", "delay", "defer", "confusion", "restriction", "confidence", "intent"]),
]


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


def readable_reddit_text(raw):
    """Turn a Reddit JSON dump into title + selftext + comments."""
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


def bucketize(cat):
    c = (cat or "").lower()
    for name, keys in BUCKETS:
        if any(k in c for k in keys):
            return name
    return "Other / uncategorized"


def keyword_hits(rows):
    kws = [k.lower() for k in KEYWORDS]
    counts = Counter()
    matches = 0
    for r in rows:
        text = (r.get("text", "") or "").lower()
        if any(kw in text for kw in kws):
            matches += 1
            counts[r.get("source", "")] += 1
    return matches, counts


def print_classification_summary(rows):
    total = len(rows)
    relevant = [r for r in rows if str(r.get("relevant", "")).lower() == "true"]
    errors = sum(1 for r in rows if r.get("category") == "error")
    print(f"\n=== Claude relevance classification ===")
    print(f"Total relevant: {len(relevant)} / {total}")
    if errors:
        print(f"WARNING: {errors} rows still marked category=error")

    src = Counter(r.get("source", "") for r in relevant)
    print("\nRelevant by source:")
    for s, n in src.most_common():
        print(f"  {s}: {n}")

    by_cat = Counter((r.get("category") or "uncategorized") for r in relevant)
    print("\nBreakdown by (raw) category:")
    for cat, n in by_cat.most_common():
        print(f"  {n:3}  {cat}")

    bucket_counts = Counter()
    bucket_src = defaultdict(Counter)
    bucket_raw = defaultdict(Counter)
    for r in relevant:
        b = bucketize(r.get("category", ""))
        bucket_counts[b] += 1
        bucket_src[b][r.get("source", "")] += 1
        bucket_raw[b][r.get("category", "")] += 1

    print("\n=== Canonical bucket breakdown ===")
    for b, n in bucket_counts.most_common():
        srcs = ", ".join(f"{s}:{c}" for s, c in bucket_src[b].most_common())
        print(f"{n:3}  {b}   [{srcs}]")

    print("\n=== Reddit relevant rows (new) ===")
    reddit_rel = [r for r in relevant if r.get("source") == "reddit"]
    print(f"count: {len(reddit_rel)}")
    for r in reddit_rel:
        kp = (r.get("key_phrase") or "").replace("\n", " ")[:180]
        print(f"- id={r.get('id')} | tag={r.get('category')}")
        print(f"  key_phrase: {kp}")


def main():
    load_dotenv(ENV_PATH)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Missing ANTHROPIC_API_KEY in .env.")

    with open(CLASSIFIED_PATH, encoding="utf-8", newline="") as fh:
        existing = list(csv.DictReader(fh))
    print(f"Loaded {len(existing)} already-classified rows.")

    with open(REDDIT_PARSED_PATH, encoding="utf-8", newline="") as fh:
        reddit_raw = list(csv.DictReader(fh))
    print(f"Classifying {len(reddit_raw)} Reddit threads...")

    client = Anthropic(api_key=api_key)
    reddit_classified = []
    for row in reddit_raw:
        clean = readable_reddit_text(row.get("text", "") or "")
        verdict = C.classify_text(client, clean)
        out = {
            "source": "reddit",
            "id": row.get("id", ""),
            "date": row.get("date", ""),
            "text": clean,
            "engagement_score": row.get("engagement_score", ""),
            "rating_if_available": "",
            "relevant": verdict["relevant"],
            "category": C.norm(verdict["category"]),
            "key_phrase": C.norm(verdict["key_phrase"]),
        }
        reddit_classified.append(out)
        print(f"  {out['id']}: relevant={out['relevant']} | {out['category']}")

    all_rows = existing + reddit_classified
    fieldnames = list(existing[0].keys()) if existing else list(reddit_classified[0].keys())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} rows to {OUTPUT_PATH}")

    matches, kw_counts = keyword_hits(all_rows)
    print("\n=== Keyword filter (wishlist/saved/favourite/...) ===")
    print(f"Total matching rows: {matches}")
    print("Per-source:")
    for s in ("playstore", "appstore", "youtube", "reddit"):
        if kw_counts.get(s):
            print(f"  {s:10} {kw_counts[s]}")

    print_classification_summary(all_rows)


if __name__ == "__main__":
    main()

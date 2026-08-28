"""Rebuild discovery/data.json from the classified merged CSV."""

import csv
import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import (
    CLASSIFIED_MERGED as CLASSIFIED_PATH,
    EXTRACT_PATH as OUT_PATH,
    PRICE_RECLASSIFIED_MERGED as PRICE_PATH,
)

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

KEYWORDS = [
    "wishlist", "wish list", "saved", "favourite", "favorite", "heart icon", "bookmark",
]
BUCKETS = [
    ("Price / sale timing", ["price", "sale", "timing", "discount", "money", "afford"], "var(--marigold-deep)"),
    ("Wishlist / save behaviour", ["wishlist", "favourite", "favorite", "heart", "saved", "save"], "var(--ink)"),
    ("Purchase hesitation (other)", ["hesitat", "delay", "defer", "confusion", "restriction", "confidence", "intent"], "var(--slate)"),
    ("Comparison shopping", ["comparison", "compare"], "var(--teal)"),
    ("Size / fit uncertainty", ["size", "fit"], "var(--clay)"),
    ("Forgot / went stale", ["forget", "forgot", "stale", "unavailab", "out of stock", "stock"], "var(--rose)"),
]
SOURCE_ORDER = [
    ("playstore", "play store"),
    ("youtube", "youtube"),
    ("reddit", "reddit"),
    ("appstore", "app store"),
]
QUOTES = [
    ["Saved it for later, waited for a sale — but by the time the price dropped the size was gone, so I bought the same thing cheaper elsewhere.", "Reddit", "cross-platform leakage", "var(--teal)"],
    ["Sizes are not available for many of my liked products.", "Play Store", "size / fit", "var(--clay)"],
    ["Prices are slightly higher than other platforms — I cross-check before buying.", "Play Store", "comparison shopping", "var(--teal)"],
    ["The offer showed on the app, but two days later at booking it was auto-cancelled.", "Play Store", "price / timing", "var(--marigold-deep)"],
    ["1,000-item wishlist cap stopped me from saving more.", "Reddit", "wishlist behaviour", "var(--ink)"],
    ["Wishlisted item shows a higher price than its sibling colours.", "Reddit", "price / timing", "var(--marigold-deep)"],
    ["I’ll wait for the December End of Reason Sale before buying what’s saved.", "Reddit", "price / timing", "var(--marigold-deep)"],
    ["Bought it straight from the wishlist because it was sale time.", "Reddit", "wishlist behaviour", "var(--ink)"],
]


def bucketize(cat):
    c = (cat or "").lower()
    for name, keys, color in BUCKETS:
        if any(k in c for k in keys):
            return name, color
    return "Other / uncategorized", "var(--slate)"


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build_extract():
    rows = read_csv(CLASSIFIED_PATH)
    total = len(rows)
    relevant_rows = [r for r in rows if str(r.get("relevant", "")).lower() == "true"]
    kws = [k.lower() for k in KEYWORDS]
    keyword = 0
    for r in rows:
        t = (r.get("text") or "").lower()
        if any(k in t for k in kws):
            keyword += 1

    src_all = Counter(r.get("source", "") for r in rows)
    src_rel = Counter(r.get("source", "") for r in relevant_rows)
    sources = [
        {"key": label, "relevant": src_rel.get(code, 0), "total": src_all.get(code, 0)}
        for code, label in SOURCE_ORDER
    ]

    bucket_counts = Counter(bucketize(r.get("category", ""))[0] for r in relevant_rows)
    themes = []
    for name, _keys, color in BUCKETS:
        n = bucket_counts.get(name, 0)
        if n:
            themes.append([name, n, color])
    other = bucket_counts.get("Other / uncategorized", 0)
    if other:
        themes.append(["Other / uncategorized", other, "var(--slate)"])

    price_rows = read_csv(PRICE_PATH)
    price_labels = Counter(r.get("price_label", "") for r in price_rows)
    tagged = sum(1 for r in relevant_rows if bucketize(r.get("category", ""))[0] == "Price / sale timing")
    extract = {
        "extracted_at": date.today().isoformat(),
        "source_file": os.path.basename(CLASSIFIED_PATH),
        "total": total,
        "relevant": len(relevant_rows),
        "keyword": keyword,
        "sources": sources,
        "themes": themes,
        "price": {
            "tagged": len(price_rows) or tagged,
            "generic": price_labels.get("price_sentiment_generic", 0),
            "deferral": price_labels.get("price_deferral", 0),
        },
        "quotes": QUOTES,
    }
    Path(OUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(extract, fh, ensure_ascii=False, indent=2)
    return extract


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    data = build_extract()
    print(f"Wrote {OUT_PATH}: total={data['total']} relevant={data['relevant']}")

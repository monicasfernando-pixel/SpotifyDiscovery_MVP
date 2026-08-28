"""Build data/snapshot.json — the dashboard's single source of truth.

Corpus counts come from the classified CSV. Questions, opportunities, and
verbatims are the published findings (not recomputed from a live scrape).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ROOT, SNAPSHOT_PATH
from pipeline.build_extract import (
    BUCKETS,
    CLASSIFIED_PATH,
    KEYWORDS,
    PRICE_PATH,
    QUOTES,
    SOURCE_ORDER,
    bucketize,
    build_extract,
    read_csv,
)
from collections import Counter

QUESTIONS = [
    {
        "question": "Why do users add to wishlist?",
        "answer": "Deferred intent — a price/occasion holding pen, not impulse.",
        "confidence": "medium",
    },
    {
        "question": "What prevents purchase?",
        "answer": "Price gap vs other platforms; size unavailable in their size.",
        "confidence": "high",
    },
    {
        "question": "What uncertainties remain?",
        "answer": "Whether the price is genuinely good, and whether their size stays in stock.",
        "confidence": "medium",
    },
    {
        "question": "What causes postponement?",
        "answer": "Waiting for a sale; size out of stock; comparing elsewhere.",
        "confidence": "high",
    },
    {
        "question": "How do users compare shortlisted products?",
        "answer": "Cross-platform price checks (Amazon/Flipkart/Ajio) dominate.",
        "confidence": "high",
    },
    {
        "question": "What info sought outside Myntra?",
        "answer": "Prices on other apps; reviews/YouTube for fit and quality.",
        "confidence": "high",
    },
    {
        "question": "Role of fit/size/styling/price/reviews/occasion/social validation?",
        "answer": "Price, size and comparison strongly present; styling and social validation NOT strongly surfaced in public text.",
        "confidence": "medium",
    },
    {
        "question": "Wishlist as genuine intent vs bookmark?",
        "answer": "Both — large unpruned lists used as bookmarks, alongside sale-triggered buying.",
        "confidence": "medium",
    },
    {
        "question": "How do behaviours differ across segments?",
        "answer": "Not resolvable from public text alone — carried to interviews.",
        "confidence": "low",
    },
    {
        "question": "What unmet needs recur?",
        "answer": "Users repeatedly leave Myntra to verify price/value elsewhere before buying.",
        "confidence": "high",
    },
]

OPPORTUNITIES = [
    {"name": "Cross-platform price-leakage", "evidence": 0.88, "impact": 0.90, "verdict": "pursue"},
    {"name": "In-app “good price/time?” signal", "evidence": 0.76, "impact": 0.78, "verdict": "pursue"},
    {"name": "Size/fit availability clarity", "evidence": 0.50, "impact": 0.72, "verdict": "secondary"},
    {"name": "Notification opt-out / signal ignored", "evidence": 0.48, "impact": 0.50, "verdict": "secondary"},
    {"name": "Trend staleness", "evidence": 0.18, "impact": 0.32, "verdict": "drop"},
    {"name": "Generic price sentiment", "evidence": 0.86, "impact": 0.16, "verdict": "drop"},
]

THEME_HEX = {
    "Price / sale timing": "#B67A05",
    "Wishlist / save behaviour": "#3A1D3D",
    "Purchase hesitation (other)": "#5B5568",
    "Comparison shopping": "#0E7C6B",
    "Size / fit uncertainty": "#B45309",
    "Forgot / went stale": "#9B2C4A",
    "Other / uncategorized": "#5B5568",
}

ENGINE = {
    "steps": [
        {"n": "01 · collect", "title": "Scrape sources", "body": "Play/App Store v1+v2 merged, plus YouTube and Reddit, into one schema."},
        {"n": "02 · classify", "title": "Relevance pass", "body": "LLM tags each item: is this real save-then-decide behaviour? Not sentiment."},
        {"n": "03 · re-check", "title": "Strict re-read", "body": "Separate genuine deferral from generic mentions. Counts corrected down."},
        {"n": "04 · validate", "title": "Manual audit", "body": "Hand-tag a sample, compare to the model, report the agreement rate."},
    ],
    "note": (
        "The live pipeline runs from the project repo (scrapers + classification scripts). "
        "This page is the findings surface — it presents the output of that run so it can be "
        "read and interrogated without re-running collection. Classification is fact-constrained: "
        "the model tags and quotes, it doesn't invent items."
    ),
}


def _write_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def assemble_snapshot(extract: dict | None = None, classified_path: str | Path | None = None) -> dict:
    """Merge live corpus stats with published findings into one snapshot."""
    if extract is None:
        rows = read_csv(str(classified_path or CLASSIFIED_PATH))
        relevant_rows = [r for r in rows if str(r.get("relevant", "")).lower() == "true"]
        kws = [k.lower() for k in KEYWORDS]
        keyword = sum(1 for r in rows if any(k in (r.get("text") or "").lower() for k in kws))
        src_all = Counter(r.get("source", "") for r in rows)
        src_rel = Counter(r.get("source", "") for r in relevant_rows)
        sources = [
            {"key": label, "relevant": src_rel.get(code, 0), "total": src_all.get(code, 0)}
            for code, label in SOURCE_ORDER
        ]
        bucket_counts = Counter(bucketize(r.get("category", ""))[0] for r in relevant_rows)
        themes = []
        for name, _keys, _color in BUCKETS:
            n = bucket_counts.get(name, 0)
            if n:
                themes.append({"name": name, "count": n, "color": THEME_HEX.get(name, "#5B5568")})
        other = bucket_counts.get("Other / uncategorized", 0)
        if other:
            themes.append({"name": "Other / uncategorized", "count": other, "color": "#5B5568"})
        price_rows = read_csv(PRICE_PATH)
        price_labels = Counter(r.get("price_label", "") for r in price_rows)
        tagged = sum(1 for r in relevant_rows if bucketize(r.get("category", ""))[0] == "Price / sale timing")
        extract = {
            "extracted_at": date.today().isoformat(),
            "source_file": os.path.basename(CLASSIFIED_PATH),
            "total": len(rows),
            "relevant": len(relevant_rows),
            "keyword": keyword,
            "sources": sources,
            "themes": [[t["name"], t["count"], t["color"]] for t in themes],
            "price": {
                "tagged": len(price_rows) or tagged,
                "generic": price_labels.get("price_sentiment_generic", 0),
                "deferral": price_labels.get("price_deferral", 0),
            },
            "quotes": QUOTES,
        }

    themes = []
    for item in extract.get("themes") or []:
        if isinstance(item, dict):
            themes.append({
                "name": item["name"],
                "count": item["count"],
                "color": item.get("color") or THEME_HEX.get(item["name"], "#5B5568"),
            })
        else:
            name, count, color = item[0], item[1], item[2] if len(item) > 2 else "#5B5568"
            if isinstance(color, str) and color.startswith("var("):
                color = THEME_HEX.get(name, "#5B5568")
            themes.append({"name": name, "count": count, "color": color})

    verbatims = []
    for q in extract.get("quotes") or QUOTES:
        if isinstance(q, dict):
            verbatims.append(q)
        else:
            text, source, tag, color = q[0], q[1], q[2], q[3] if len(q) > 3 else "#3A1D3D"
            if isinstance(color, str) and color.startswith("var("):
                color = {
                    "var(--teal)": "#0E7C6B",
                    "var(--clay)": "#B45309",
                    "var(--marigold-deep)": "#B67A05",
                    "var(--ink)": "#3A1D3D",
                }.get(color, "#3A1D3D")
            verbatims.append({"text": text, "source": source, "tag": tag, "color": color})

    price = extract.get("price") or {}
    return {
        "extracted_at": extract.get("extracted_at") or date.today().isoformat(),
        "source_file": extract.get("source_file") or os.path.basename(CLASSIFIED_PATH),
        "corpus_total": extract.get("corpus_total", extract.get("total", 0)),
        "relevant_count": extract.get("relevant_count", extract.get("relevant", 0)),
        "keyword": extract.get("keyword", 0),
        "sources": extract.get("sources") or [],
        "themes": themes,
        "questions": extract.get("questions") or QUESTIONS,
        "opportunities": extract.get("opportunities") or OPPORTUNITIES,
        "honesty": {
            "tagged": price.get("tagged", 0),
            "generic": price.get("generic", 0),
            "deferral": price.get("deferral", 0),
        },
        "verbatims": verbatims,
        "engine": extract.get("engine") or ENGINE,
    }


def build_snapshot(dest: str | Path | None = None, *, also_write_extract: bool = True) -> dict:
    """Write snapshot to dest (default data/snapshot.json). Returns the payload."""
    extract = None
    if also_write_extract:
        extract = build_extract()
    snap = assemble_snapshot(extract)
    path = Path(dest) if dest else SNAPSHOT_PATH
    if not path.is_absolute():
        path = ROOT / path
    _write_json(path, snap)
    return snap


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    data = build_snapshot()
    print(
        f"Wrote {SNAPSHOT_PATH}: corpus={data['corpus_total']} "
        f"relevant={data['relevant_count']}"
    )

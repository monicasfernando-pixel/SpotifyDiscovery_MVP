"""Re-classify the price/sale-timing cluster with a stricter deferral vs generic split.

Reads data/classified_relevance.csv, selects the relevant rows whose existing
category relates to price / sale timing, and asks Claude to assign exactly one
of two labels:

  price_deferral        - actively waiting / hesitating / delaying a purchase
                          specifically due to price or an expected/ongoing sale.
  price_sentiment_generic - merely mentions price / discounts / affordability
                          without describing hesitation or a delayed decision.

The existing key_phrase extraction is preserved. Output is written to
data/price_cluster_reclassified.csv and the per-label counts are printed.
"""

import csv
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import CLASSIFIED_MERGED as INPUT_PATH, ENV_PATH, PRICE_RECLASSIFIED_MERGED as OUTPUT_PATH

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 50
BATCH_SIZE = 20
BATCH_DELAY = 2.0
MAX_RETRIES = 2

PRICE_KEYS = ["price", "sale", "timing", "discount", "money", "afford"]
VALID_LABELS = {"price_deferral", "price_sentiment_generic"}

OUTPUT_COLUMNS = [
    "source",
    "id",
    "date",
    "text",
    "engagement_score",
    "rating_if_available",
    "previous_category",
    "price_label",
    "key_phrase",
]

SYSTEM_PROMPT = (
    "You are analyzing user feedback about a fashion shopping app. Each text was "
    "already flagged as related to price or sale timing. Classify it into exactly "
    "one of two labels:\n"
    '- "price_deferral": the text describes actively waiting, hesitating, or '
    "delaying a purchase specifically due to price or an expected/ongoing sale "
    '(e.g. "I\'ll wait for the sale", "was more expensive than I expected so I '
    'didn\'t buy", "cancelled because the offer expired").\n'
    '- "price_sentiment_generic": the text merely mentions price, discounts, or '
    "affordability without describing hesitation or a delayed purchase decision "
    '(e.g. "prices are high but quality is good", "I love the discounts here").\n'
    'Respond with strict JSON only: {"label": "price_deferral" or '
    '"price_sentiment_generic"}'
)


def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def classify(client, text):
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}],
            )
            reply = "".join(
                b.text for b in resp.content if getattr(b, "type", None) == "text"
            )
            label = extract_json(reply).get("label")
            if label in VALID_LABELS:
                return label
            raise ValueError(f"unexpected label: {label!r}")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
    print(f"    ! failed after retries: {last_err}")
    return "error"


def main():
    load_dotenv(ENV_PATH)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Missing ANTHROPIC_API_KEY in .env.")
    if not os.path.exists(INPUT_PATH):
        raise SystemExit(f"Input not found: {INPUT_PATH}.")

    client = Anthropic(api_key=api_key)

    with open(INPUT_PATH, encoding="utf-8", newline="") as fh:
        all_rows = list(csv.DictReader(fh))

    cluster = [
        r
        for r in all_rows
        if str(r.get("relevant", "")).lower() == "true"
        and any(k in (r.get("category", "") or "").lower() for k in PRICE_KEYS)
    ]
    print(f"Price/sale-timing cluster rows to re-classify: {len(cluster)}")

    results = []
    for start in range(0, len(cluster), BATCH_SIZE):
        batch = cluster[start : start + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            labels = list(
                pool.map(lambda r: classify(client, r.get("text", "") or ""), batch)
            )
        for row, label in zip(batch, labels):
            results.append(
                {
                    "source": row.get("source", ""),
                    "id": row.get("id", ""),
                    "date": row.get("date", ""),
                    "text": row.get("text", ""),
                    "engagement_score": row.get("engagement_score", ""),
                    "rating_if_available": row.get("rating_if_available", ""),
                    "previous_category": row.get("category", ""),
                    "price_label": label,
                    "key_phrase": row.get("key_phrase", ""),
                }
            )
        if start + BATCH_SIZE < len(cluster):
            time.sleep(BATCH_DELAY)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(results)

    counts = Counter(r["price_label"] for r in results)
    print(f"\nWrote {len(results)} rows to {OUTPUT_PATH}")
    print("Label counts:")
    for label in ("price_deferral", "price_sentiment_generic", "error"):
        if counts.get(label):
            print(f"  {label}: {counts[label]}")


if __name__ == "__main__":
    main()

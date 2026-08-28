"""Classify each row of data/all_raw_sources.csv with the Anthropic API.

For every row we ask Claude whether the text relates to save-for-later /
wishlist / purchase-hesitation behavior (even without explicit keywords), and
record a structured JSON verdict. All rows (relevant or not) are written to
data/classified_relevance.csv with three new columns: relevant, category,
key_phrase.

Usage:
    python classify_relevance.py [--limit N]

    --limit N   classify only the first N rows (handy for a smoke test).

ANTHROPIC_API_KEY is read from .env.
"""

import argparse
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
from paths import ALL_RAW_SOURCES as INPUT_PATH, CLASSIFIED as OUTPUT_PATH, ENV_PATH

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 300
BATCH_SIZE = 20
BATCH_DELAY = 2.0          # seconds to pause between batches of 20
MAX_RETRIES = 2           # additional attempts after the first failure
PROGRESS_EVERY = 100

NEW_COLUMNS = ["relevant", "category", "key_phrase"]

SYSTEM_PROMPT = (
    "You are analyzing user feedback about a fashion shopping app. Determine if "
    "this text relates to any of: saving items for later, wishlist/favourite/heart "
    "behavior, purchase hesitation or delay, deferred buying decisions, price or "
    "sale timing considerations, comparison shopping, size/fit uncertainty causing "
    "a delay, or forgetting about saved items — even if it doesn't use words like "
    "'wishlist' explicitly. Respond with strict JSON only: "
    '{"relevant": true/false, "category": "<short tag or null>", '
    '"key_phrase": "<the specific sentence/phrase that shows this, or null>"}'
)


def _extract_json_block(text):
    """Return the first balanced {...} block, ignoring braces inside strings."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return text[start:]


def parse_verdict(raw_text):
    """Parse the model's JSON reply, tolerating code fences / surrounding text."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    data = json.loads(_extract_json_block(text))
    return {
        "relevant": bool(data.get("relevant", False)),
        "category": data.get("category"),
        "key_phrase": data.get("key_phrase"),
    }


def classify_text(client, text):
    """Call the API with retries; return a verdict dict (never raises)."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}],
            )
            reply = "".join(
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            )
            return parse_verdict(reply)
        except Exception as exc:  # noqa: BLE001 - includes API + JSON errors
            last_err = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))

    print(f"    ! classification failed after retries: {last_err}")
    return {"relevant": False, "category": "error", "key_phrase": None}


def norm(value):
    """Render None as empty string for CSV output."""
    return "" if value is None else value


def write_all(out_columns, rows):
    """(Re)write the full output CSV so partial progress is always persisted."""
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=out_columns)
        writer.writeheader()
        writer.writerows(rows)


def load_rows(resume):
    """Return (out_columns, rows). In resume mode, load the existing output so
    already-classified rows are kept and only failures get retried."""
    if resume and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            out_columns = reader.fieldnames
            rows = list(reader)
        print(f"Resuming from {OUTPUT_PATH} ({len(rows)} rows).")
        return out_columns, rows

    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        out_columns = list(reader.fieldnames) + NEW_COLUMNS
        rows = list(reader)
    for row in rows:
        for col in NEW_COLUMNS:
            row.setdefault(col, "")
    return out_columns, rows


def print_summary(rows):
    total = len(rows)
    relevant_count = 0
    error_count = 0
    by_category = Counter()
    by_source_relevant = Counter()

    for row in rows:
        category = row.get("category", "")
        if category == "error":
            error_count += 1
        # 'relevant' may be a bool (fresh) or the string 'True'/'False' (resume).
        is_relevant = str(row.get("relevant", "")).lower() == "true"
        if is_relevant:
            relevant_count += 1
            by_source_relevant[row.get("source", "")] += 1
            by_category[category or "uncategorized"] += 1

    print(f"\nDone. Wrote {total} classified rows to {OUTPUT_PATH}")
    print(f"Total relevant: {relevant_count} / {total}")
    if error_count:
        print(f"WARNING: {error_count} rows failed to classify (category=error). "
              "Fix the cause (e.g. API credits) and re-run with --resume.")

    print("\nBreakdown by category:")
    for cat, n in by_category.most_common():
        print(f"  {cat}: {n}")

    print("\nRelevant breakdown by source:")
    for source, n in by_source_relevant.most_common():
        print(f"  {source}: {n}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="classify only the first N rows (fresh run only)")
    parser.add_argument("--resume", action="store_true",
                        help="only re-classify rows that previously failed "
                             "(category=error) in the existing output CSV")
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Missing ANTHROPIC_API_KEY in .env.")
    if not os.path.exists(INPUT_PATH):
        raise SystemExit(f"Input not found: {INPUT_PATH}. Run merge_sources.py first.")

    client = Anthropic(api_key=api_key)
    out_columns, rows = load_rows(args.resume)

    if not args.resume and args.limit is not None:
        rows = rows[: args.limit]

    # Decide which rows still need classifying.
    if args.resume:
        todo = [i for i, r in enumerate(rows) if r.get("category") == "error"]
        print(f"{len(todo)} rows need re-classification.")
    else:
        todo = list(range(len(rows)))
        print(f"Classifying {len(todo)} rows with {MODEL}...")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not args.resume:
        write_all(out_columns, rows)  # write header + placeholder rows up front

    processed = 0
    for start in range(0, len(todo), BATCH_SIZE):
        batch_idx = todo[start : start + BATCH_SIZE]
        batch_rows = [rows[i] for i in batch_idx]

        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            verdicts = list(
                pool.map(
                    lambda r: classify_text(client, r.get("text", "") or ""),
                    batch_rows,
                )
            )

        for row, verdict in zip(batch_rows, verdicts):
            row["relevant"] = verdict["relevant"]
            row["category"] = norm(verdict["category"])
            row["key_phrase"] = norm(verdict["key_phrase"])
            processed += 1
            if processed % PROGRESS_EVERY == 0:
                print(f"  processed {processed}/{len(todo)}")

        # Rewrite the whole file after each batch to persist partial progress.
        write_all(out_columns, rows)
        if start + BATCH_SIZE < len(todo):
            time.sleep(BATCH_DELAY)

    print_summary(rows)


if __name__ == "__main__":
    main()

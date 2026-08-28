"""Scrape the most recent Play Store reviews for the Myntra Android app.

Fetches up to TARGET_REVIEWS reviews sorted by "newest" using the
google-play-scraper library's paginated `reviews` function, then writes them
to a CSV file.
"""

import csv
import sys
import time
from pathlib import Path

from google_play_scraper import Sort, reviews

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import PLAYSTORE_V2 as OUTPUT_PATH

APP_ID = "com.myntra.android"
TARGET_REVIEWS = 3000
BATCH_SIZE = 200          # reviews requested per page (max ~200)
REQUEST_DELAY = 1.0       # seconds to wait between requests (rate limiting)
PROGRESS_EVERY = 200      # print progress after this many reviews

CSV_COLUMNS = [
    "source",
    "review_id",
    "date",
    "rating",
    "review_text",
    "thumbs_up",
]


def fetch_reviews(target):
    """Fetch up to `target` newest reviews using continuation-token pagination."""
    collected = []
    seen_ids = set()
    continuation_token = None
    last_reported = 0

    while len(collected) < target:
        remaining = target - len(collected)
        count = min(BATCH_SIZE, remaining)

        try:
            batch, continuation_token = reviews(
                APP_ID,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token,
            )
        except Exception as exc:  # noqa: BLE001 - keep scraping resilient
            print(f"Request failed: {exc}. Retrying after a short delay...")
            time.sleep(REQUEST_DELAY * 5)
            continue

        if not batch:
            print(f"No more reviews returned by the store; stopping at {len(collected)}.")
            break

        new_in_batch = 0
        for entry in batch:
            review_id = entry.get("reviewId")
            if review_id in seen_ids:
                continue
            seen_ids.add(review_id)
            collected.append(entry)
            new_in_batch += 1

        if new_in_batch == 0:
            print(f"No new unique reviews in this page; stopping at {len(collected)}.")
            break

        if len(collected) - last_reported >= PROGRESS_EVERY:
            last_reported = len(collected)
            print(f"Fetched {len(collected)} / {target} reviews...")

        if continuation_token is None:
            print(f"Reached the end of available reviews; stopping at {len(collected)}.")
            break

        time.sleep(REQUEST_DELAY)

    return collected[:target]


def write_csv(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in rows:
            review_date = entry.get("at")
            writer.writerow(
                {
                    "source": "playstore",
                    "review_id": entry.get("reviewId"),
                    "date": review_date.isoformat() if review_date else "",
                    "rating": entry.get("score"),
                    "review_text": entry.get("content") or "",
                    "thumbs_up": entry.get("thumbsUpCount"),
                }
            )


def main():
    print(f"Scraping up to {TARGET_REVIEWS} newest reviews for {APP_ID} "
          f"(country=in)...")
    rows = fetch_reviews(TARGET_REVIEWS)
    write_csv(rows, OUTPUT_PATH)
    print(f"Total rows fetched: {len(rows)}")
    print(f"Wrote {len(rows)} reviews to {OUTPUT_PATH}")
    if len(rows) < TARGET_REVIEWS:
        print(
            f"Stopped cleanly: store returned {len(rows)} reviews "
            f"(fewer than the {TARGET_REVIEWS} requested)."
        )


if __name__ == "__main__":
    main()

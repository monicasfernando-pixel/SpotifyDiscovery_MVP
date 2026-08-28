"""Scrape the most recent App Store reviews for the Myntra iOS app (India).

Output schema matches data/playstore_reviews.csv:
    source, review_id, date, rating, review_text, thumbs_up

Two data sources are attempted, in order:

1. `app-store-scraper` (Apple's private amp-api). This can page through
   thousands of reviews, BUT it needs a bearer token that Apple used to embed
   in the App Store web page. Apple now injects that token at runtime via JS,
   so on most setups the library can no longer obtain it and returns 0 reviews.
   We still try it first so the run uses the requested library and benefits
   automatically if a valid token is ever available.

2. Apple's public RSS "customerreviews" feed. No token required, sorted by
   most recent. Apple caps this feed at ~500 reviews (10 pages x 50); for
   Myntra IN it currently exposes ~250. This is the reliable fallback.

TARGET_REVIEWS is a ceiling (3000, or whatever Apple actually returns).
The script stops cleanly as soon as a source runs out of new reviews.

`thumbs_up` is populated from the RSS vote sum when available; fields not
exposed by a given source are written as empty (null).
"""

import csv
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import APPSTORE_V2 as OUTPUT_PATH

APP_NAME = "myntra"
APP_ID = 907394059          # Myntra - Fashion Shopping App (Indian App Store)
COUNTRY = "in"              # Myntra is India-only
TARGET_REVIEWS = 3000       # ceiling; stop early if the store returns fewer
REQUEST_DELAY = 1.0         # seconds between requests (rate limiting)
MAX_RETRIES = 5            # per-request retry attempts
CSV_COLUMNS = [
    "source",
    "review_id",
    "date",
    "rating",
    "review_text",
    "thumbs_up",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Source 1: app-store-scraper (amp-api)
# ---------------------------------------------------------------------------
def fetch_via_app_store_scraper(target):
    """Try the private amp-api via app-store-scraper. Returns a list of dicts
    in the normalized shape, or [] if the token/endpoint is unavailable."""
    try:
        from datetime import datetime

        from app_store_scraper import AppStore
    except Exception as exc:  # noqa: BLE001
        print(f"app-store-scraper unavailable: {exc}")
        return []

    class MyntraAppStore(AppStore):
        def _parse_data(self, after):
            response = self._response.json()
            for data in response["data"]:
                review = data["attributes"]
                review["review_id"] = data.get("id")
                review["date"] = datetime.strptime(
                    review["date"], "%Y-%m-%dT%H:%M:%SZ"
                )
                self.reviews.append(review)
                self.reviews_count += 1
                self._fetched_count += 1

    app = MyntraAppStore(country=COUNTRY, app_name=APP_NAME, app_id=APP_ID)
    if not app._request_headers.get("Authorization"):
        print("amp-api bearer token unavailable (Apple no longer embeds it); "
              "falling back to the RSS feed.")
        return []

    app._request_params["sort"] = "mostRecent"
    attempts = 0
    last = 0
    while len(app.reviews) < target:
        try:
            app.review(how_many=target - len(app.reviews), sleep=int(REQUEST_DELAY) or 1)
        except Exception as exc:  # noqa: BLE001
            print(f"amp-api fetch error: {exc}")
        current = len(app.reviews)
        print(f"[amp-api] fetched {current} / {target}...")
        if app._request_offset is None:
            print(f"[amp-api] store returned no further pages; stopping at {current}.")
            break
        if current == last:
            attempts += 1
            if attempts >= MAX_RETRIES:
                print(f"[amp-api] no new reviews after retries; stopping at {current}.")
                break
            time.sleep(REQUEST_DELAY * 3)
        else:
            attempts = 0
        last = current

    return [
        {
            "review_id": r.get("review_id"),
            "date": r["date"].isoformat() if r.get("date") else "",
            "rating": r.get("rating"),
            "review_text": r.get("review") or "",
            "thumbs_up": "",  # not exposed by amp-api
        }
        for r in app.reviews[:target]
    ]


# ---------------------------------------------------------------------------
# Source 2: Apple RSS customer reviews feed (no token required)
# ---------------------------------------------------------------------------
def _get_json(url):
    """GET with retries + exponential backoff; returns parsed JSON or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 503):
                wait = REQUEST_DELAY * (2 ** attempt)
                print(f"Rate limited ({resp.status_code}); retrying in {wait:.0f}s...")
                time.sleep(wait)
                continue
            print(f"HTTP {resp.status_code} for {url}")
            return None
        except (requests.RequestException, ValueError) as exc:
            wait = REQUEST_DELAY * (2 ** attempt)
            print(f"Request error: {exc}; retrying in {wait:.0f}s...")
            time.sleep(wait)
    return None


def fetch_via_rss(target, countries=None):
    """Public RSS. Path order matters: page=N/id=APP/sortby=mostrecent/json.

    The older id=.../sortBy=mostRecent/page=N/json form returns an empty feed.
    India often only exposes page 1 (~50). Extra storefronts are used only if
    still short of `target`, then deduped by review id.
    """
    collected = []
    seen = set()
    storefronts = []
    for c in list(countries or [COUNTRY, "us", "gb", "ae", "sg"]):
        if c not in storefronts:
            storefronts.append(c)

    for country in storefronts:
        if len(collected) >= target:
            break
        for page in range(1, 11):
            if len(collected) >= target:
                break
            url = (
                f"https://itunes.apple.com/{country}/rss/customerreviews/"
                f"page={page}/id={APP_ID}/sortby=mostrecent/json"
            )
            data = _get_json(url)
            if not data:
                print(f"[rss {country}] no data for page {page}; stopping this storefront.")
                break

            entries = data.get("feed", {}).get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]
            reviews = [e for e in entries if isinstance(e, dict) and "im:rating" in e]
            # Apple often returns HTTP 200 with an empty stub feed (~900 bytes)
            # under rate-limit; retry page 1 before giving up on the storefront.
            if not reviews and page == 1:
                for attempt in range(1, MAX_RETRIES + 1):
                    wait = REQUEST_DELAY * (2 ** attempt)
                    print(f"[rss {country}] empty stub on page 1; retry {attempt}/{MAX_RETRIES} in {wait:.0f}s")
                    time.sleep(wait)
                    data = _get_json(url)
                    entries = (data or {}).get("feed", {}).get("entry", []) if data else []
                    if isinstance(entries, dict):
                        entries = [entries]
                    reviews = [e for e in entries if isinstance(e, dict) and "im:rating" in e]
                    if reviews:
                        break
            if not reviews:
                print(f"[rss {country}] no reviews on page {page}; stopping this storefront at {len(collected)}.")
                break

            new_on_page = 0
            for e in reviews:
                review_id = (e.get("id") or {}).get("label")
                if not review_id or review_id in seen:
                    continue
                seen.add(review_id)
                new_on_page += 1
                title = (e.get("title") or {}).get("label", "") or ""
                body = (e.get("content") or {}).get("label", "") or ""
                text = f"{title}\n\n{body}".strip() if title else body
                collected.append(
                    {
                        "review_id": review_id,
                        "date": (e.get("updated") or {}).get("label", ""),
                        "rating": (e.get("im:rating") or {}).get("label"),
                        "review_text": text,
                        "thumbs_up": (e.get("im:voteSum") or {}).get("label"),
                    }
                )

            print(f"[rss {country}] page {page}: +{new_on_page} unique (total {len(collected)})")
            if new_on_page == 0:
                break
            time.sleep(REQUEST_DELAY)

    return collected[:target]


def write_csv(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "source": "appstore",
                    "review_id": r.get("review_id") or "",
                    "date": r.get("date") or "",
                    "rating": r.get("rating") if r.get("rating") is not None else "",
                    "review_text": r.get("review_text") or "",
                    "thumbs_up": r.get("thumbs_up") if r.get("thumbs_up") is not None else "",
                }
            )


def main():
    print(f"Scraping up to {TARGET_REVIEWS} newest App Store reviews for "
          f"{APP_NAME} (id={APP_ID}, country={COUNTRY})...")

    rows = fetch_via_app_store_scraper(TARGET_REVIEWS)
    if not rows:
        rows = fetch_via_rss(TARGET_REVIEWS)

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

"""Scrape comments from Myntra-related YouTube videos via the YouTube Data API v3.

The API key is read from .env (YOUTUBE_API_KEY) and never hardcoded.

Steps:
1. Search YouTube for several Myntra queries, restricted to the last 2 years,
   ordered by relevance.
2. Merge + de-duplicate results and keep the top 15 videos overall.
3. For each video, fetch up to 100 top (relevance-ordered) comments.

Output -> data/youtube_comments.csv with columns:
    source, video_id, video_title, comment_id, date, comment_text, like_count
"""

import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows consoles default to cp1252 and choke on emoji in video titles/logs.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ENV_PATH, YOUTUBE_COMMENTS as OUTPUT_PATH

QUERIES = [
    "myntra haul",
    "myntra review",
    "myntra try on haul",
    "myntra unboxing",
]

TOP_VIDEOS = 15
COMMENTS_PER_VIDEO = 100    # commentThreads.list caps a page at 100
RESULTS_PER_QUERY = 15

CSV_COLUMNS = [
    "source",
    "video_id",
    "video_title",
    "comment_id",
    "date",
    "comment_text",
    "like_count",
]


def get_youtube():
    load_dotenv(ENV_PATH)
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing YOUTUBE_API_KEY in .env. Add your YouTube Data API v3 key."
        )
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def search_videos(youtube):
    """Search each query and return up to TOP_VIDEOS unique (id, title) pairs."""
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=2 * 365)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    ordered_videos = []
    seen = set()

    for query in QUERIES:
        try:
            response = (
                youtube.search()
                .list(
                    part="snippet",
                    q=query,
                    type="video",
                    order="relevance",
                    publishedAfter=published_after,
                    relevanceLanguage="en",
                    regionCode="IN",
                    maxResults=RESULTS_PER_QUERY,
                )
                .execute()
            )
        except HttpError as exc:
            print(f"  Search failed for '{query}': {exc}")
            continue

        found = 0
        for item in response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            title = item.get("snippet", {}).get("title", "")
            ordered_videos.append((video_id, title))
            found += 1
        print(f"  '{query}': {found} new videos")

    # Keep the top N unique videos (relevance order across queries).
    return ordered_videos[:TOP_VIDEOS]


def fetch_comments(youtube, video_id, video_title):
    """Fetch up to COMMENTS_PER_VIDEO top comments for a single video."""
    rows = []
    try:
        response = (
            youtube.commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                order="relevance",
                textFormat="plainText",
                maxResults=COMMENTS_PER_VIDEO,
            )
            .execute()
        )
    except HttpError as exc:
        reason = ""
        try:
            reason = exc.error_details[0].get("reason", "")
        except Exception:  # noqa: BLE001
            pass
        if "commentsDisabled" in str(exc) or reason == "commentsDisabled":
            print(f"    Comments disabled for {video_id}; skipping.")
        else:
            print(f"    Could not fetch comments for {video_id}: {exc}")
        return rows

    for item in response.get("items", []):
        top = item.get("snippet", {}).get("topLevelComment", {})
        snippet = top.get("snippet", {})
        rows.append(
            {
                "source": "youtube",
                "video_id": video_id,
                "video_title": video_title,
                "comment_id": top.get("id", ""),
                "date": snippet.get("publishedAt", ""),
                "comment_text": snippet.get("textOriginal", "")
                or snippet.get("textDisplay", ""),
                "like_count": snippet.get("likeCount", ""),
            }
        )
    return rows


def write_csv(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    youtube = get_youtube()

    print("Searching YouTube...")
    videos = search_videos(youtube)
    print(f"Selected {len(videos)} videos. Fetching comments...")

    all_rows = []
    for idx, (video_id, title) in enumerate(videos, start=1):
        print(f"[{idx}/{len(videos)}] {video_id} - {title[:60]}")
        all_rows.extend(fetch_comments(youtube, video_id, title))

    write_csv(all_rows, OUTPUT_PATH)
    print(f"Done. Wrote {len(all_rows)} comments from {len(videos)} videos "
          f"to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

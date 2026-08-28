"""Scrape Myntra-related Reddit posts and comments via Reddit's public JSON API.

No authentication / OAuth / PRAW required - this hits the same public JSON
endpoints the website uses, e.g.:

    https://old.reddit.com/r/{subreddit}/search.json
        ?q=myntra&restrict_sr=1&sort=relevance&t=all&limit=100

For each matching post we record the post row, and if the post has more than
5 comments we fetch its permalink .json to collect up to 20 top-level comments.

Output -> data/reddit_posts.csv with columns:
    source, post_id, date, title, text, upvotes, comment_or_post, permalink
"""

import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import REDDIT_POSTS as OUTPUT_PATH

SUBREDDITS = [
    "india",
    "IndianFashionAddicts",
    "femalefashionadvice",
]

QUERY = "myntra"
TOP_COMMENTS = 20
COMMENT_THRESHOLD = 5       # only fetch comments if a post has more than this
SEARCH_LIMIT = 100
REQUEST_DELAY = 2.0         # seconds between requests (rate limiting)
RATE_LIMIT_WAIT = 30        # seconds to wait after a 429 before retrying once

USER_AGENT = "myntra-research-script/1.0"
REDDIT_BASE = "https://www.reddit.com"

CSV_COLUMNS = [
    "source",
    "post_id",
    "date",
    "title",
    "text",
    "upvotes",
    "comment_or_post",
    "permalink",
]


def get_json(url, params=None):
    """GET JSON with a custom UA. On HTTP 429, wait 30s and retry once."""
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(2):  # initial try + one retry after 429
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        except requests.RequestException as exc:
            print(f"    Request error for {url}: {exc}")
            return None

        if resp.status_code == 429:
            if attempt == 0:
                print(f"    429 rate limited; waiting {RATE_LIMIT_WAIT}s and retrying once...")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            print("    Still rate limited after retry; skipping.")
            return None

        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code} for {url}")
            return None

        try:
            return resp.json()
        except ValueError as exc:
            print(f"    Could not parse JSON from {url}: {exc}")
            return None

    return None


def iso_date(created_utc):
    if not created_utc:
        return ""
    return datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()


def fetch_top_comments(permalink):
    """Fetch up to TOP_COMMENTS top-level comments for a post permalink."""
    url = f"{REDDIT_BASE}{permalink}.json"
    data = get_json(url, params={"limit": TOP_COMMENTS, "depth": 1})
    time.sleep(REQUEST_DELAY)
    if not data or len(data) < 2:
        return []

    children = data[1].get("data", {}).get("children", [])
    comments = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        c = child.get("data", {})
        body = c.get("body")
        if not body:
            continue
        comments.append(c)
        if len(comments) >= TOP_COMMENTS:
            break
    return comments


def rows_for_post(post):
    rows = []
    permalink = REDDIT_BASE + post.get("permalink", "")
    rows.append(
        {
            "source": "reddit",
            "post_id": post.get("id", ""),
            "date": iso_date(post.get("created_utc")),
            "title": post.get("title", "") or "",
            "text": post.get("selftext", "") or "",
            "upvotes": post.get("score", ""),
            "comment_or_post": "post",
            "permalink": permalink,
        }
    )

    if (post.get("num_comments") or 0) > COMMENT_THRESHOLD:
        for c in fetch_top_comments(post.get("permalink", "")):
            c_permalink = c.get("permalink")
            full_permalink = (
                REDDIT_BASE + c_permalink if c_permalink else permalink
            )
            rows.append(
                {
                    "source": "reddit",
                    "post_id": post.get("id", ""),   # parent post id
                    "date": iso_date(c.get("created_utc")),
                    "title": post.get("title", "") or "",  # parent title
                    "text": c.get("body", "") or "",
                    "upvotes": c.get("score", ""),
                    "comment_or_post": "comment",
                    "permalink": full_permalink,
                }
            )

    return rows


def search_subreddit(name, seen_ids):
    print(f"Searching r/{name} for '{QUERY}'...")
    url = f"https://old.reddit.com/r/{name}/search.json"
    params = {
        "q": QUERY,
        "restrict_sr": 1,
        "sort": "relevance",
        "t": "all",
        "limit": SEARCH_LIMIT,
    }
    data = get_json(url, params=params)
    time.sleep(REQUEST_DELAY)
    if not data:
        print(f"  No results for r/{name}; skipping.")
        return []

    children = data.get("data", {}).get("children", [])
    rows = []
    new_posts = 0
    for child in children:
        post = child.get("data", {})
        post_id = post.get("id")
        if not post_id or post_id in seen_ids:
            continue
        seen_ids.add(post_id)
        rows.extend(rows_for_post(post))
        new_posts += 1
    print(f"  r/{name}: {new_posts} posts matched")
    return rows


def write_csv(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    all_rows = []
    seen_ids = set()

    for name in SUBREDDITS:
        all_rows.extend(search_subreddit(name, seen_ids))

    write_csv(all_rows, OUTPUT_PATH)
    posts = sum(1 for r in all_rows if r["comment_or_post"] == "post")
    comments = len(all_rows) - posts
    print(
        f"Done. Wrote {len(all_rows)} rows "
        f"({posts} posts, {comments} comments) to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()

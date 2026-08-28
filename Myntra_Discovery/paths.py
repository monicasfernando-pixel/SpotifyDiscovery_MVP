"""Canonical project paths. Import these instead of hardcoding data/ locations."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DISCOVERY_DIR = ROOT / "discovery"

SNAPSHOT_PATH = DATA_DIR / "snapshot.json"
SNAPSHOT_TMP = DATA_DIR / "snapshot.tmp.json"
EXTRACT_PATH = DISCOVERY_DIR / "data.json"

PLAYSTORE_V1 = RAW_DIR / "playstore_reviews.csv"
PLAYSTORE_V2 = RAW_DIR / "playstore_reviews_v2.csv"
APPSTORE_V1 = RAW_DIR / "appstore_reviews.csv"
APPSTORE_V2 = RAW_DIR / "appstore_reviews_v2.csv"
YOUTUBE_COMMENTS = RAW_DIR / "youtube_comments.csv"
REDDIT_POSTS = RAW_DIR / "reddit_posts.csv"
REDDIT_RAW_TXT = RAW_DIR / "reddit_raw_txt"
REDDIT_PARSED = RAW_DIR / "reddit_manual_parsed.csv"

ALL_RAW_SOURCES = PROCESSED_DIR / "all_raw_sources.csv"
ALL_RAW_SOURCES_FINAL = PROCESSED_DIR / "all_raw_sources_final.csv"
ALL_RAW_SOURCES_MERGED = PROCESSED_DIR / "all_raw_sources_merged.csv"
CLASSIFIED = PROCESSED_DIR / "classified_relevance.csv"
CLASSIFIED_FINAL = PROCESSED_DIR / "classified_relevance_final.csv"
CLASSIFIED_MERGED = PROCESSED_DIR / "classified_relevance_merged.csv"
PRICE_RECLASSIFIED = PROCESSED_DIR / "price_cluster_reclassified.csv"
PRICE_RECLASSIFIED_MERGED = PROCESSED_DIR / "price_cluster_reclassified_merged.csv"
RELEVANT_SUBSET = PROCESSED_DIR / "relevant_subset.csv"
RELEVANT_SUBSET_V2 = PROCESSED_DIR / "relevant_subset_v2.csv"
MERGED_STATS = PROCESSED_DIR / "merged_stats.txt"

ENV_PATH = ROOT / ".env"

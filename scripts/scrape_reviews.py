#!/usr/bin/env python3
"""
Task 1.2: Google Play Store Review Scraper

Scrapes user reviews for three Ethiopian banks (CBE, BOA, Dashen)
using the google-play-scraper library.

Usage:
    python scripts/scrape_reviews.py
    python scripts/scrape_reviews.py --bank CBE --count 500
    python scripts/scrape_reviews.py --output data/raw/reviews_raw.csv

Output columns:
    review_id, review, rating, date, bank, source, scraped_at
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import BANKS, RAW_DATA_DIR, REVIEW_COLUMNS, SCRAPING_CONFIG

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core scraping function
# ---------------------------------------------------------------------------
def scrape_bank_reviews(
    bank_code: str,
    app_id: str,
    bank_name: str,
    target_count: int = 500,
    sleep_seconds: float = 2.0,
    max_retries: int = 3,
    sort_method: Sort = Sort.MOST_RELEVANT,
) -> pd.DataFrame:
    """
    Scrape reviews for a single bank app from Google Play Store.

    Args:
        bank_code: Short code (CBE, BOA, Dashen)
        app_id: Google Play package name
        bank_name: Human-readable bank name
        target_count: Number of reviews to collect
        sleep_seconds: Delay between pagination requests
        max_retries: Retry attempts on failure
        sort_method: Sort.MOST_RELEVANT or Sort.NEWEST

    Returns:
        DataFrame with standardized columns
    """
    logger.info(f"[{bank_code}] Starting scrape for '{app_id}' — target: {target_count} reviews")

    all_reviews = []
    continuation_token = None
    batch_size = 100  # google-play-scraper default max per call
    attempts = 0

    while len(all_reviews) < target_count and attempts < max_retries:
        try:
            # Calculate how many to fetch in this batch
            remaining = target_count - len(all_reviews)
            fetch_count = min(batch_size, remaining)

            result, continuation_token = reviews(
                app_id,
                lang="en",
                country="et",
                sort=sort_method,
                count=fetch_count,
                continuation_token=continuation_token,
            )

            if not result:
                logger.warning(f"[{bank_code}] No more reviews returned. Stopping at {len(all_reviews)}.")
                break

            for r in result:
                all_reviews.append({
                    "review_id": r.get("reviewId", ""),
                    "review": r.get("content", "").strip(),
                    "rating": r.get("score", None),
                    "date": r.get("at", None),
                    "bank": bank_name,
                    "source": "Google Play",
                    "scraped_at": datetime.utcnow().isoformat(),
                })

            logger.info(f"[{bank_code}] Collected {len(all_reviews)} / {target_count} reviews")

            # Rate limiting — be nice to Google's servers
            if continuation_token and len(all_reviews) < target_count:
                time.sleep(sleep_seconds)

        except Exception as e:
            attempts += 1
            logger.error(f"[{bank_code}] Error (attempt {attempts}/{max_retries}): {e}")
            if attempts < max_retries:
                wait = sleep_seconds * attempts
                logger.info(f"[{bank_code}] Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"[{bank_code}] Max retries exceeded. Stopping.")
                break

    # Build DataFrame
    df = pd.DataFrame(all_reviews, columns=REVIEW_COLUMNS)

    # Drop rows with missing review text or rating
    missing_before = len(df)
    df = df.dropna(subset=["review", "rating"])
    missing_after = len(df)
    if missing_before != missing_after:
        logger.warning(
            f"[{bank_code}] Dropped {missing_before - missing_after} rows with missing review/rating"
        )

    logger.info(f"[{bank_code}] Final count: {len(df)} valid reviews")
    return df


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_app_id(app_id: str) -> bool:
    """Quick validation that app_id looks like a real package name."""
    return isinstance(app_id, str) and "." in app_id and len(app_id) > 5


def try_alternative_ids(bank_info: dict, bank_code: str) -> pd.DataFrame:
    """
    If primary app_id fails, try alternative IDs listed in config.
    Returns DataFrame or raises RuntimeError if all fail.
    """
    primary_id = bank_info["app_id"]
    alternatives = bank_info.get("alternative_ids", [])
    all_ids = [primary_id] + alternatives

    for app_id in all_ids:
        if not validate_app_id(app_id):
            continue
        try:
            logger.info(f"[{bank_code}] Trying app_id: {app_id}")
            df = scrape_bank_reviews(
                bank_code=bank_code,
                app_id=app_id,
                bank_name=bank_info["name"],
                target_count=SCRAPING_CONFIG["reviews_per_bank"],
                sleep_seconds=SCRAPING_CONFIG["sleep_between_requests"],
                max_retries=SCRAPING_CONFIG["max_retries"],
            )
            if len(df) > 0:
                logger.info(f"[{bank_code}] Success with app_id: {app_id}")
                return df
        except Exception as e:
            logger.warning(f"[{bank_code}] Failed with {app_id}: {e}")
            continue

    raise RuntimeError(
        f"[{bank_code}] Could not scrape with any app_id. "
        f"Please verify the correct package name on Google Play Store."
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Play Store reviews for Ethiopian bank apps"
    )
    parser.add_argument(
        "--bank",
        choices=["CBE", "BOA", "Dashen", "all"],
        default="all",
        help="Which bank to scrape (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=SCRAPING_CONFIG["reviews_per_bank"],
        help=f"Reviews per bank (default: {SCRAPING_CONFIG['reviews_per_bank']})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/raw/reviews_raw_YYYYMMDD.csv)",
    )
    parser.add_argument(
        "--sort",
        choices=["most_relevant", "newest"],
        default="most_relevant",
        help="Review sort order",
    )
    args = parser.parse_args()

    # Determine which banks to scrape
    if args.bank == "all":
        banks_to_scrape = list(BANKS.keys())
    else:
        banks_to_scrape = [args.bank]

    sort_map = {
        "most_relevant": Sort.MOST_RELEVANT,
        "newest": Sort.NEWEST,
    }
    sort_method = sort_map[args.sort]

    all_dfs = []
    summary = []

    for bank_code in banks_to_scrape:
        bank_info = BANKS[bank_code]

        try:
            df = try_alternative_ids(bank_info, bank_code)
            all_dfs.append(df)
            summary.append({
                "bank": bank_code,
                "app_id": bank_info["app_id"],
                "reviews_collected": len(df),
                "avg_rating": round(df["rating"].mean(), 2) if len(df) > 0 else None,
                "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}" if len(df) > 0 else "N/A",
            })
        except RuntimeError as e:
            logger.error(str(e))
            summary.append({
                "bank": bank_code,
                "app_id": bank_info["app_id"],
                "reviews_collected": 0,
                "avg_rating": None,
                "date_range": "FAILED",
            })

    if not all_dfs:
        logger.error("No reviews collected for any bank. Exiting.")
        sys.exit(1)

    # Combine all banks
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = RAW_DATA_DIR / f"reviews_raw_{timestamp}.csv"

    combined_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved {len(combined_df)} reviews to: {output_path}")

    # Print summary table
    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)
    for row in summary:
        print(f"  {row['bank']:8s} | {row['reviews_collected']:4d} reviews | "
              f"avg rating: {row['avg_rating']} | {row['date_range']}")
    print(f"  TOTAL    | {len(combined_df):4d} reviews")
    print("=" * 60)

    # Warn if any bank is below target
    for row in summary:
        if row["reviews_collected"] < 400:
            logger.warning(
                f"{row['bank']} only has {row['reviews_collected']} reviews (target: 400+). "
                "Consider expanding date range or checking app_id."
            )


if __name__ == "__main__":
    main()
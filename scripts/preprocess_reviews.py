#!/usr/bin/env python3
"""
Task 1.3: Data Preprocessing

Cleans and normalizes raw scraped reviews into an analysis-ready dataset.

Usage:
    python scripts/preprocess_reviews.py
    python scripts/preprocess_reviews.py --input data/raw/reviews_raw_20250519.csv

Output columns:
    review_id, review, rating, date, bank, source
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def find_latest_raw_file() -> Path:
    """Auto-detect the most recent raw reviews CSV in data/raw/."""
    raw_files = sorted(RAW_DATA_DIR.glob("reviews_raw_*.csv"))
    if not raw_files:
        raise FileNotFoundError(f"No reviews_raw_*.csv found in {RAW_DATA_DIR}")
    return raw_files[-1]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate reviews based on review_id."""
    before = len(df)
    df = df.drop_duplicates(subset=["review_id"], keep="first")
    after = len(df)
    dropped = before - after
    if dropped > 0:
        logger.info(f"Dropped {dropped} duplicate reviews ({dropped/before*100:.1f}%)")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows missing review text or rating.
    Log counts for transparency.
    """
    before = len(df)

    missing_review = df["review"].isna().sum() + (df["review"].str.strip() == "").sum()
    missing_rating = df["rating"].isna().sum()

    df = df.dropna(subset=["review", "rating"])
    df = df[df["review"].str.strip() != ""]

    after = len(df)
    dropped = before - after
    logger.info(f"Dropped {dropped} rows with missing/empty review or rating")
    logger.info(f"  - Missing/empty review text: {missing_review}")
    logger.info(f"  - Missing rating: {missing_rating}")
    return df


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dates to YYYY-MM-DD format."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = df["date"].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"{invalid_dates} rows have unparseable dates — dropped")
        df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def clean_review_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic text cleaning:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces/newlines
    - Remove non-printable characters
    """
    df = df.copy()
    df["review"] = (
        df["review"]
        .astype(str)
        .str.strip()
        .apply(lambda x: re.sub(r"\s+", " ", x))   # collapse whitespace
        .apply(lambda x: re.sub(r"[^\x00-\x7F]+", "", x))  # remove non-ASCII
    )
    return df


def validate_rating_range(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure ratings are integers 1–5."""
    df = df.copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    invalid = (~df["rating"].between(1, 5)).sum()
    if invalid > 0:
        logger.warning(f"{invalid} ratings outside 1–5 range — dropped")
        df = df[df["rating"].between(1, 5)]
    df["rating"] = df["rating"].astype(int)
    return df


def preprocess(input_path: Path, output_path: Path = None) -> pd.DataFrame:
    """
    Full preprocessing pipeline.

    Args:
        input_path: Path to raw CSV
        output_path: Optional explicit output path

    Returns:
        Cleaned DataFrame
    """
    logger.info(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} raw rows")

    # Step 1: Remove duplicates
    df = remove_duplicates(df)

    # Step 2: Handle missing values
    df = handle_missing_values(df)

    # Step 3: Normalize dates
    df = normalize_dates(df)

    # Step 4: Clean review text
    df = clean_review_text(df)

    # Step 5: Validate ratings
    df = validate_rating_range(df)

    # Step 6: Select final columns
    final_cols = ["review_id", "review", "rating", "date", "bank", "source"]
    df = df[[col for col in final_cols if col in df.columns]]

    # Output
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = PROCESSED_DATA_DIR / f"reviews_cleaned_{timestamp}.csv"

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved {len(df)} cleaned reviews to: {output_path}")

    # Summary
    print("\n" + "=" * 60)
    print("PREPROCESSING SUMMARY")
    print("=" * 60)
    print(f"  Input rows:     {len(pd.read_csv(input_path))}")
    print(f"  Output rows:    {len(df)}")
    print(f"  Duplicates:     removed")
    print(f"  Missing dropped:  logged above")
    print(f"  Date format:    YYYY-MM-DD")
    print(f"  Rating range:   1–5 (integers)")
    print("=" * 60)

    return df


def main():
    parser = argparse.ArgumentParser(description="Preprocess raw Google Play reviews")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to raw CSV (default: auto-detect latest in data/raw/)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/processed/reviews_cleaned_YYYYMMDD.csv)",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else find_latest_raw_file()
    output_path = Path(args.output) if args.output else None

    preprocess(input_path, output_path)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Task 3: Store Cleaned Data in PostgreSQL

Initializes the database schema and inserts analyzed review data.

Usage:
    python scripts/load_to_postgres.py
    python scripts/load_to_postgres.py --input data/processed/reviews_analyzed_20250519.csv
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import PROCESSED_DATA_DIR, SQL_DIR
from src.db import init_schema, insert_reviews, verify_database_health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def find_latest_analyzed_file() -> Path:
    """Find the most recent analyzed reviews CSV."""
    files = sorted(PROCESSED_DATA_DIR.glob("reviews_analyzed_*.csv"))
    if not files:
        # Fallback to cleaned if analyzed is missing
        files = sorted(PROCESSED_DATA_DIR.glob("reviews_cleaned_*.csv"))
        
    if not files:
        raise FileNotFoundError(f"No analyzed or cleaned CSVs found in {PROCESSED_DATA_DIR}")
    return files[-1]

def main():
    parser = argparse.ArgumentParser(description="Load analyzed data into PostgreSQL")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None, 
        help="Path to analyzed CSV (default: latest in data/processed/)"
    )
    parser.add_argument(
        "--no-init", 
        action="store_true", 
        help="Skip schema initialization"
    )
    args = parser.parse_args()

    # 1. Initialize Schema
    if not args.no_init:
        schema_path = SQL_DIR / "schema.sql"
        logger.info(f"Initializing schema from {schema_path}...")
        try:
            init_schema(str(schema_path))
            logger.info("Schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            logger.info("Ensure PostgreSQL is running and database 'bank_reviews' exists.")
            sys.exit(1)

    # 2. Load Data
    try:
        input_path = Path(args.input) if args.input else find_latest_analyzed_file()
    except FileNotFoundError as e:
        logger.error(e)
        logger.info("Please run scripts/sentiment_analysis.py first.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    # 3. Insert into DB
    logger.info("Inserting reviews into database...")
    count = insert_reviews(df)
    logger.info(f"Successfully inserted/updated {count} reviews.")

    # 4. Verify Health
    logger.info("Running database health check...")
    health = verify_database_health()
    
    print("\n" + "=" * 60)
    print("DATABASE HEALTH CHECK")
    print("=" * 60)
    for key, val in health.items():
        print(f"  {key:<20}: {val}")
    print("=" * 60)

    if health["overall_status"] == "PASS":
        logger.info("Database load verified.")
    else:
        logger.warning("Database health check failed. Review the results above.")

if __name__ == "__main__":
    main()

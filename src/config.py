"""
Configuration for the Fintech Review Analytics pipeline.
Contains app IDs, paths, and scraping parameters.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data paths
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SQL_DIR = PROJECT_ROOT / "sql"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Bank app configurations
# NOTE: If scraping fails for any bank, verify the app_id on Google Play Store
BANKS = {
    "CBE": {
        "name": "Commercial Bank of Ethiopia Mobile",
        "app_id": "com.combanketh.mobilebanking",  # Correct ID: Amole/Mobile Banking
        "alternative_ids": [
            "com.cbe.mobile",
            "com.combanketh.mobile",
            "com.commercialbankofethiopia.mobile",
        ],
        "country": "ET",
        "language": "en",
    },
    "BOA": {
        "name": "Bank of Abyssinia Mobile",
        "app_id": "com.bankofabyssinia.boamobile.retail",  # Confirmed via Apptopia
        "alternative_ids": [
            "com.bankofabyssinia.mobile",
            "com.boa.mobile",
            "com.boabank.mobile",
        ],
        "country": "ET",
        "language": "en",
    },
    "Dashen": {
        "name": "Dashen Bank SuperApp",
        "app_id": "com.dashen.dashensuperapp",  # Correct ID
        "alternative_ids": [
            "com.dashen",
            "com.dashenbank.superapp",
            "com.dashen.mobile",
        ],
        "country": "ET",
        "language": "en",
    },
}

# Scraping parameters
SCRAPING_CONFIG = {
    "reviews_per_bank": 500,      # Target: 400+ per bank (buffer for duplicates)
    "max_reviews_per_request": 100,  # google-play-scraper batch size
    "sleep_between_requests": 2,   # Seconds between requests (rate limiting)
    "max_retries": 3,
    "sort": "most_relevant",      # Alternative: "newest"
}

# Output columns
REVIEW_COLUMNS = [
    "review_id",
    "review",
    "rating",
    "date",
    "bank",
    "source",
    "scraped_at",
]

# Database config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "bank_reviews"),
    "user": os.getenv("DB_USER", "sumeya"),
    "password": os.getenv("DB_PASSWORD", "S3cure_P@ss_987"),
}
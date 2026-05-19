"""
Unit tests for the Google Play Store review scraper.

Run with:
    pytest tests/test_scraper.py -v
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import BANKS, REVIEW_COLUMNS


class TestConfigValidation:
    """Tests for configuration and validation helpers."""

    def test_banks_config_structure(self):
        """Each bank must have required keys."""
        required_keys = {"name", "app_id", "alternative_ids", "country", "language"}
        for code, info in BANKS.items():
            assert required_keys.issubset(info.keys()), f"{code} missing keys"
            assert isinstance(info["app_id"], str)
            assert isinstance(info["alternative_ids"], list)

    def test_review_columns_defined(self):
        """Column list must match expected schema."""
        expected = [
            "review_id",
            "review",
            "rating",
            "date",
            "bank",
            "source",
            "scraped_at",
        ]
        assert REVIEW_COLUMNS == expected


class TestDataFrameStructure:
    """Tests for scraped DataFrame structure and quality."""

    @pytest.fixture
    def sample_reviews_df(self):
        """Create a minimal sample DataFrame mimicking scraper output."""
        data = {
            "review_id": ["r1", "r2", "r3"],
            "review": [
                "Great app, fast transfers!",
                "Login error every morning.",
                "",  # empty review — should be dropped
            ],
            "rating": [5.0, 2.0, None],
            "date": pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-10"]),
            "bank": ["CBE", "BOA", "Dashen"],
            "source": ["Google Play", "Google Play", "Google Play"],
            "scraped_at": ["2024-05-01T10:00:00"] * 3,
        }
        return pd.DataFrame(data)

    def test_drop_missing_review_or_rating(self, sample_reviews_df):
        """Rows with missing review text or rating must be dropped."""
        df = sample_reviews_df.dropna(subset=["review", "rating"])
        assert len(df) == 2
        assert all(df["review"].notna())
        assert all(df["rating"].notna())

    def test_rating_range(self, sample_reviews_df):
        """Ratings must be between 1 and 5."""
        df = sample_reviews_df.dropna(subset=["rating"])
        assert df["rating"].between(1, 5).all()

    def test_date_parsing(self, sample_reviews_df):
        """Dates must be parseable datetime objects."""
        df = sample_reviews_df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        assert df["date"].isna().sum() == 0

    def test_no_duplicate_review_ids(self, sample_reviews_df):
        """Review IDs should be unique."""
        df = sample_reviews_df.dropna(subset=["review", "rating"])
        assert df["review_id"].duplicated().sum() == 0


class TestScrapingParameters:
    """Tests for scraping configuration values."""

    def test_target_count_meets_minimum(self):
        """Config must request at least 400 reviews per bank."""
        from config import SCRAPING_CONFIG
        assert SCRAPING_CONFIG["reviews_per_bank"] >= 400

    def test_rate_limiting_present(self):
        """Sleep between requests must be > 0 to avoid rate limits."""
        from config import SCRAPING_CONFIG
        assert SCRAPING_CONFIG["sleep_between_requests"] > 0

    def test_retries_configured(self):
        """Max retries must be at least 1."""
        from config import SCRAPING_CONFIG
        assert SCRAPING_CONFIG["max_retries"] >= 1
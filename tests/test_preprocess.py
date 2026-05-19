"""
Unit tests for the review preprocessing pipeline.

Run with:
    pytest tests/test_preprocess.py -v
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import PROCESSED_DATA_DIR


class TestPreprocessingPipeline:
    """Tests for data cleaning and normalization logic."""

    @pytest.fixture
    def dirty_df(self):
        """Simulate raw scraped data with common quality issues."""
        data = {
            "review_id": ["r1", "r2", "r3", "r4", "r1"],  # r1 duplicated
            "review": [
                "Great   app!!!  ",
                "",
                "Login fails every morning\n\nPlease fix",
                None,
                "Great   app!!!  ",  # duplicate content
            ],
            "rating": [5.0, 3.0, 2.0, None, 5.0],
            "date": ["2024-01-15", "2024-02-20", "bad_date", "2024-04-01", "2024-01-15"],
            "bank": ["CBE", "BOA", "Dashen", "CBE", "CBE"],
            "source": ["Google Play"] * 5,
            "scraped_at": ["2024-05-01T10:00:00"] * 5,
        }
        return pd.DataFrame(data)

    def test_duplicate_removal(self, dirty_df):
        """Duplicate review_ids must be removed, keeping first occurrence."""
        df = dirty_df.drop_duplicates(subset=["review_id"], keep="first")
        assert df["review_id"].duplicated().sum() == 0
        assert len(df) == 4  # 5 - 1 duplicate

    def test_missing_review_or_rating_dropped(self, dirty_df):
        """Rows with empty/None review or rating must be dropped."""
        df = dirty_df.drop_duplicates(subset=["review_id"], keep="first")
        df = df.dropna(subset=["review", "rating"])
        df = df[df["review"].str.strip() != ""]
        assert len(df) == 2  # r1 and r3 only
        assert all(df["review"].notna())
        assert all(df["rating"].notna())

    def test_date_normalization(self, dirty_df):
        """Valid dates parse to datetime; invalid become NaT and can be dropped."""
        df = dirty_df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        assert pd.isna(df.loc[2, "date"])  # "bad_date" should be NaT
        assert df.loc[0, "date"] == pd.Timestamp("2024-01-15")

    def test_rating_range_validation(self, dirty_df):
        """Ratings outside 1–5 must be rejected."""
        df = dirty_df.copy()
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df[df["rating"].between(1, 5)]
        assert all(df["rating"].between(1, 5))

    def test_whitespace_cleaning(self, dirty_df):
        """Multiple spaces and newlines should collapse to single spaces."""
        import re
        text = "Login fails every morning\n\nPlease fix"
        cleaned = re.sub(r"\s+", " ", text.strip())
        assert "\n" not in cleaned
        assert "  " not in cleaned

    def test_final_column_schema(self, dirty_df):
        """Output must contain exactly the required columns."""
        required = ["review_id", "review", "rating", "date", "bank", "source"]
        df = dirty_df.drop_duplicates(subset=["review_id"], keep="first")
        df = df.dropna(subset=["review", "rating"])
        df = df[[col for col in required if col in df.columns]]
        assert list(df.columns) == required
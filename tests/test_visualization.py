"""
Unit tests for visualization module.

Run with:
    pytest tests/test_visualizations.py -v
"""

import sys
from pathlib import Path
import pandas as pd
import pytest
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for testing

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from visualizations import (
    plot_sentiment_distribution,
    plot_rating_distribution,
    plot_theme_frequency,
    BANK_COLORS,
    SENTIMENT_COLORS,
)


class TestVisualizationStructure:
    """Tests that plots generate without errors and return Figure objects."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame with all required columns."""
        return pd.DataFrame({
            "review_id": [f"r{i}" for i in range(1, 16)],
            "review": [
                "Great app fast transfers",
                "Login fails every time",
                "Okay but slow",
                "Love the UI design",
                "Support never replies",
                "Transfer instant amazing",
                "Crash on startup",
                "Dark mode please",
                "OTP not received",
                "Best banking app",
                "Payment failed again",
                "Nice interface clean",
                "Bug in balance display",
                "Fingerprint login works",
                "Slow loading screens",
            ],
            "rating": [5, 1, 3, 5, 2, 5, 1, 4, 2, 5, 1, 4, 2, 5, 3],
            "date": pd.date_range("2024-01-01", periods=15, freq="D").strftime("%Y-%m-%d"),
            "bank": ["CBE"] * 5 + ["BOA"] * 5 + ["Dashen"] * 5,
            "source": ["Google Play"] * 15,
            "sentiment_label": [
                "positive", "negative", "neutral", "positive", "negative",
                "positive", "negative", "neutral", "negative", "positive",
                "negative", "positive", "negative", "positive", "neutral",
            ],
            "sentiment_score": [0.95, 0.88, 0.50, 0.92, 0.85, 0.97, 0.90, 0.55, 0.87, 0.93, 0.89, 0.91, 0.86, 0.94, 0.52],
            "identified_theme": [
                "Transaction Performance", "Account Access Issues", "Transaction Performance",
                "UI & Design", "Customer Support", "Transaction Performance",
                "App Stability", "Feature Requests", "Account Access Issues",
                "General", "Transaction Performance", "UI & Design",
                "App Stability", "Account Access Issues", "UI & Design",
            ],
        })

    def test_sentiment_distribution_returns_figure(self, sample_df):
        fig = plot_sentiment_distribution(sample_df)
        assert fig is not None
        assert hasattr(fig, "savefig")

    def test_rating_distribution_returns_figure(self, sample_df):
        fig = plot_rating_distribution(sample_df)
        assert fig is not None
        assert hasattr(fig, "savefig")

    def test_theme_frequency_returns_figure(self, sample_df):
        fig = plot_theme_frequency(sample_df)
        assert fig is not None
        assert hasattr(fig, "savefig")

    def test_sentiment_distribution_saves_file(self, sample_df, tmp_path):
        save_path = tmp_path / "test_sentiment.png"
        fig = plot_sentiment_distribution(sample_df, save_path=str(save_path))
        assert save_path.exists()
        assert save_path.stat().st_size > 0

    def test_color_constants_defined(self):
        assert "positive" in SENTIMENT_COLORS
        assert "negative" in SENTIMENT_COLORS
        assert "neutral" in SENTIMENT_COLORS
        assert "CBE" in BANK_COLORS or "Commercial Bank of Ethiopia" in BANK_COLORS
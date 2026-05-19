#!/usr/bin/env python3
"""
Task 2: Sentiment and Thematic Analysis

Classifies review sentiment using DistilBERT and VADER, 
and extracts business-relevant themes using TF-IDF and keyword matching.

Usage:
    python scripts/sentiment_analysis.py
    python scripts/sentiment_analysis.py --input data/processed/reviews_cleaned_20250519.csv
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# NLP imports
try:
    from transformers import pipeline
    import torch
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import PROCESSED_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentiment Analysis
# ---------------------------------------------------------------------------

class SentimentAnalyzer:
    def __init__(self, use_gpu: bool = False):
        logger.info("Initializing sentiment models...")
        
        # 1. DistilBERT (Transformer-based)
        device = 0 if use_gpu and torch.cuda.is_available() else -1
        try:
            self.classifier = pipeline(
                "sentiment-analysis", 
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=device
            )
        except Exception as e:
            logger.warning(f"Failed to load DistilBERT: {e}. Falling back to VADER only.")
            self.classifier = None
            
        # 2. VADER (Lexicon-based fallback/comparison)
        self.vader = SentimentIntensityAnalyzer()

    def get_sentiment(self, text: str) -> tuple:
        """
        Return (label, score).
        Label: positive, negative, neutral
        Score: 0 to 1 confidence
        """
        if not text or str(text).strip() == "":
            return "neutral", 0.0

        # DistilBERT logic
        if self.classifier:
            try:
                # Truncate text for DistilBERT (max 512 tokens)
                truncated_text = text[:512] 
                result = self.classifier(truncated_text)[0]
                label = result['label'].lower() # 'POSITIVE' or 'NEGATIVE'
                score = result['score']
                
                # Refine with VADER for neutral discovery (DistilBERT is binary here)
                vader_scores = self.vader.polarity_scores(text)
                if abs(vader_scores['compound']) < 0.05:
                    return "neutral", 1.0 - abs(vader_scores['compound'])
                
                return label, score
            except Exception as e:
                logger.debug(f"DistilBERT error: {e}")

        # Fallback to VADER
        v_scores = self.vader.polarity_scores(text)
        compound = v_scores['compound']
        if compound >= 0.05:
            return "positive", compound
        elif compound <= -0.05:
            return "negative", abs(compound)
        else:
            return "neutral", 1.0 - abs(compound)

# ---------------------------------------------------------------------------
# Thematic Analysis
# ---------------------------------------------------------------------------

THEME_KEYWORDS = {
    "Account Access Issues": ["login", "password", "otp", "code", "access", "sign in", "authentication", "biometric", "fingerprint"],
    "Transaction Performance": ["transfer", "send", "receive", "payment", "transaction", "fast", "slow", "delay", "pending", "failed"],
    "UI & Design": ["ui", "layout", "design", "interface", "color", "look", "navigation", "easy", "hard", "confusing", "beautiful"],
    "Customer Support": ["support", "service", "help", "call", "agent", "ticket", "response", "friendly", "rude"],
    "Feature Requests": ["wish", "want", "add", "feature", "hope", "future", "dark mode", "budget", "notification"],
    "App Stability": ["crash", "freeze", "bug", "stuck", "error", "loading", "open", "close", "update"],
}

def identify_theme(text: str) -> str:
    """simple rule-based theme assignment."""
    text = str(text).lower()
    scores = {theme: 0 for theme in THEME_KEYWORDS}
    
    for theme, keywords in THEME_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[theme] += 1
                
    max_score = max(scores.values())
    if max_score == 0:
        return "General"
    
    # Return first theme with max score
    for theme, score in scores.items():
        if score == max_score:
            return theme
    return "General"

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def find_latest_cleaned_file() -> Path:
    files = sorted(PROCESSED_DATA_DIR.glob("reviews_cleaned_*.csv"))
    if not files:
        raise FileNotFoundError(f"No reviews_cleaned_*.csv found in {PROCESSED_DATA_DIR}")
    return files[-1]

def run_analysis(input_path: Path, output_path: Path = None):
    logger.info(f"Loading cleaned data from: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Analyzing {len(df)} reviews...")

    analyzer = SentimentAnalyzer()
    
    labels = []
    scores = []
    themes = []

    for text in tqdm(df["review"], desc="NLP Processing"):
        label, score = analyzer.get_sentiment(text)
        theme = identify_theme(text)
        
        labels.append(label)
        scores.append(round(score, 4))
        themes.append(theme)

    df["sentiment_label"] = labels
    df["sentiment_score"] = scores
    df["identified_theme"] = themes

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = PROCESSED_DATA_DIR / f"reviews_analyzed_{timestamp}.csv"

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved analyzed data to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Sentiment and Thematic Analysis")
    parser.add_argument("--input", type=str, default=None, help="Path to cleaned CSV")
    parser.add_argument("--output", type=str, default=None, help="Output path")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else find_latest_cleaned_file()
    output_path = Path(args.output) if args.output else None

    run_analysis(input_path, output_path)

if __name__ == "__main__":
    main()

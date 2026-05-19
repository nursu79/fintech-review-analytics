"""
Insights and Recommendations module for Task 4.

Generates bank-specific satisfaction drivers, pain points,
and concrete product recommendations based on data evidence.
"""

import logging
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Driver / Pain Point Extraction
# ---------------------------------------------------------------------------

def extract_drivers_and_pain_points(
    df: pd.DataFrame,
    bank: str,
    min_reviews: int = 5,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract satisfaction drivers and pain points for a specific bank.

    Returns:
        (drivers, pain_points) where each is a list of dicts:
        {
            "theme": str,
            "evidence": str,  # example review snippet
            "review_count": int,
            "avg_rating": float,
            "sentiment": str,
        }
    """
    bank_df = df[df["bank"] == bank]

    drivers = []
    pain_points = []

    for theme in bank_df["identified_theme"].unique():
        if theme == "General":
            continue

        theme_df = bank_df[bank_df["identified_theme"] == theme]
        if len(theme_df) < min_reviews:
            continue

        avg_rating = theme_df["rating"].mean()
        positive_pct = (theme_df["sentiment_label"] == "positive").mean() * 100
        negative_pct = (theme_df["sentiment_label"] == "negative").mean() * 100

        # Pick a representative review
        if positive_pct > negative_pct:
            rep_review = theme_df[theme_df["sentiment_label"] == "positive"]["review"].iloc[0]
            drivers.append({
                "theme": theme,
                "evidence": rep_review[:120] + "..." if len(rep_review) > 120 else rep_review,
                "review_count": len(theme_df),
                "avg_rating": round(avg_rating, 2),
                "positive_pct": round(positive_pct, 1),
            })
        else:
            rep_review = theme_df[theme_df["sentiment_label"] == "negative"]["review"].iloc[0]
            pain_points.append({
                "theme": theme,
                "evidence": rep_review[:120] + "..." if len(rep_review) > 120 else rep_review,
                "review_count": len(theme_df),
                "avg_rating": round(avg_rating, 2),
                "negative_pct": round(negative_pct, 1),
            })

    # Sort by review count (strength of signal)
    drivers = sorted(drivers, key=lambda x: x["review_count"], reverse=True)[:3]
    pain_points = sorted(pain_points, key=lambda x: x["review_count"], reverse=True)[:3]

    return drivers, pain_points


# ---------------------------------------------------------------------------
# Recommendations Generator
# ---------------------------------------------------------------------------

def generate_recommendations(
    df: pd.DataFrame,
    bank: str,
) -> List[Dict]:
    """
    Generate concrete, prioritized product recommendations for a bank.

    Returns list of dicts:
    {
        "priority": int,
        "title": str,
        "rationale": str,
        "action_items": List[str],
        "expected_impact": str,
    }
    """
    bank_df = df[df["bank"] == bank]
    drivers, pain_points = extract_drivers_and_pain_points(df, bank)

    recommendations = []

    # Recommendation 1: Address top pain point
    if pain_points:
        top_pain = pain_points[0]
        rec = {
            "priority": 1,
            "title": f"Fix {top_pain['theme']}",
            "rationale": (
                f"{top_pain['theme']} is the top complaint ({top_pain['review_count']} reviews, "
                f"{top_pain['negative_pct']}% negative). Example: '{top_pain['evidence']}'"
            ),
            "action_items": _get_action_items(top_pain["theme"]),
            "expected_impact": "Reduce negative reviews by 20-30% and improve app store rating by 0.3 stars",
        }
        recommendations.append(rec)

    # Recommendation 2: Leverage top driver
    if drivers:
        top_driver = drivers[0]
        rec = {
            "priority": 2,
            "title": f"Amplify {top_driver['theme']}",
            "rationale": (
                f"Users love {top_driver['theme']} ({top_driver['review_count']} reviews, "
                f"{top_driver['positive_pct']}% positive). Double down on this strength."
            ),
            "action_items": _get_amplify_actions(top_driver["theme"]),
            "expected_impact": "Increase user retention and positive word-of-mouth",
        }
        recommendations.append(rec)

    # Recommendation 3: Competitive feature gap
    all_themes = set(df["identified_theme"].unique())
    bank_themes = set(bank_df["identified_theme"].unique())
    missing_themes = all_themes - bank_themes - {"General"}

    if missing_themes:
        missing = list(missing_themes)[0]
        rec = {
            "priority": 3,
            "title": f"Introduce {missing} capabilities",
            "rationale": (
                f"Competitors receive feedback on {missing} but {bank} has minimal coverage. "
                f"This suggests either a gap or untapped user need."
            ),
            "action_items": [f"Research {missing} features in competitor apps",
                           f"Run user surveys on {missing} needs",
                           f"Pilot {missing} in next release"],
            "expected_impact": "Close competitive gap and attract switchers",
        }
        recommendations.append(rec)

    # Recommendation 4: General stability / performance
    stability_df = bank_df[bank_df["identified_theme"] == "App Stability"]
    if len(stability_df) > 0 and stability_df["rating"].mean() < 3.0:
        rec = {
            "priority": 1 if not pain_points else 2,
            "title": "Improve App Stability",
            "rationale": (
                f"App Stability reviews average {stability_df['rating'].mean():.1f} stars. "
                f"Crashes and freezes directly drive uninstalls."
            ),
            "action_items": [
                "Implement crash analytics (Firebase Crashlytics)",
                "Add offline mode for critical transactions",
                "Reduce app size and memory footprint",
            ],
            "expected_impact": "Reduce churn by 15% and improve store rating",
        }
        recommendations.append(rec)

    return sorted(recommendations, key=lambda x: x["priority"])


def _get_action_items(theme: str) -> List[str]:
    """Return specific action items for a given theme."""
    actions = {
        "Account Access Issues": [
            "Implement biometric login (fingerprint / face ID)",
            "Add 'remember device' option to reduce OTP fatigue",
            "Create self-service password reset flow",
        ],
        "Transaction Performance": [
            "Optimize backend API response times",
            "Add transaction progress indicators",
            "Implement retry logic for failed transfers",
        ],
        "UI & Design": [
            "Conduct UX audit with 5-8 user interviews",
            "Add dark mode toggle",
            "Simplify navigation to 3-tap rule for key actions",
        ],
        "Customer Support": [
            "Integrate AI chatbot for L1 queries",
            "Add in-app ticket tracking",
            "Reduce response time SLA to <4 hours",
        ],
        "Feature Requests": [
            "Launch public feature voting board",
            "Prioritize top 3 requested features for Q3 roadmap",
            "Add budget tracker and spending insights",
        ],
        "App Stability": [
            "Implement crash analytics (Firebase Crashlytics)",
            "Add offline mode for critical transactions",
            "Reduce app size and memory footprint",
        ],
    }
    return actions.get(theme, [f"Investigate {theme} root causes", f"Create {theme} improvement roadmap"])


def _get_amplify_actions(theme: str) -> List[str]:
    """Return actions to amplify a strength."""
    actions = {
        "Transaction Performance": [
            "Market 'instant transfer' as key differentiator",
            "Add transfer speed badges in UI",
        ],
        "UI & Design": [
            "Showcase design awards in app store listing",
            "Create 'design story' blog post",
        ],
        "Account Access Issues": [
            "Promote biometric login in onboarding",
            "Add security tips section",
        ],
    }
    return actions.get(theme, [f"Highlight {theme} in marketing", f"Add {theme} to onboarding tour"])


# ---------------------------------------------------------------------------
# Cross-Bank Comparison
# ---------------------------------------------------------------------------

def compare_banks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a comparison table across all banks.

    Returns DataFrame with columns:
        bank, total_reviews, avg_rating, positive_pct, negative_pct,
        top_theme, top_pain_point, top_driver
    """
    rows = []
    for bank in sorted(df["bank"].unique()):
        bank_df = df[df["bank"] == bank]
        drivers, pain_points = extract_drivers_and_pain_points(df, bank)

        row = {
            "bank": bank,
            "total_reviews": len(bank_df),
            "avg_rating": round(bank_df["rating"].mean(), 2),
            "positive_pct": round((bank_df["sentiment_label"] == "positive").mean() * 100, 1),
            "negative_pct": round((bank_df["sentiment_label"] == "negative").mean() * 100, 1),
            "top_theme": bank_df["identified_theme"].value_counts().index[0],
            "top_pain_point": pain_points[0]["theme"] if pain_points else "N/A",
            "top_driver": drivers[0]["theme"] if drivers else "N/A",
        }
        rows.append(row)

    return pd.DataFrame(rows)
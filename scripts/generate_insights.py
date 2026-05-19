#!/usr/bin/env python3
"""
Task 4: Insights, Visualizations & Recommendations

Generates all plots and writes the final report synthesizing
findings into business-actionable insights.

Usage:
    python scripts/generate_insights.py
    python scripts/generate_insights.py --input data/processed/reviews_analyzed_20250519.csv
    python scripts/generate_insights.py --output-dir reports/

Outputs:
    - 5-6 PNG plots in reports/figures/
    - Final report as Markdown in reports/final_report.md
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import PROCESSED_DATA_DIR
from src.visualizations import (
    plot_sentiment_distribution,
    plot_rating_distribution,
    plot_theme_frequency,
    plot_sentiment_trend,
    plot_wordcloud,
    plot_comparison_radar,
)
from src.insights import (
    extract_drivers_and_pain_points,
    generate_recommendations,
    compare_banks,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def find_latest_analyzed_file() -> Path:
    """Auto-detect the most recent analyzed reviews CSV."""
    files = sorted(PROCESSED_DATA_DIR.glob("reviews_analyzed_*.csv"))
    if not files:
        raise FileNotFoundError(f"No reviews_analyzed_*.csv found in {PROCESSED_DATA_DIR}")
    return files[-1]


def print_section(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def generate_report(df: pd.DataFrame, output_dir: Path) -> str:
    """
    Generate the final Markdown report.

    Returns the report content as a string.
    """
    report_lines = []

    # Header
    report_lines.append("# Fintech Review Analytics: Final Report")
    report_lines.append(f"\n> **Omega Consultancy** | 10 Academy Week 2 Challenge")
    report_lines.append(f"> Date: {datetime.now().strftime('%B %d, %Y')}")
    report_lines.append("\n---\n")

    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append(f"\nThis report analyzes **{len(df)} Google Play Store reviews** across three Ethiopian banks:")
    report_lines.append("- **Commercial Bank of Ethiopia (CBE)**")
    report_lines.append("- **Bank of Abyssinia (BOA)**")
    report_lines.append("- **Dashen Bank**")
    report_lines.append("\nOur pipeline scraped, cleaned, classified sentiment, extracted themes, and stored results in PostgreSQL. Key findings reveal distinct satisfaction drivers and critical pain points for each bank.")
    report_lines.append("\n---\n")

    # Methodology
    report_lines.append("## Methodology")
    report_lines.append("\n### Data Collection")
    report_lines.append("- **Source:** Google Play Store reviews")
    report_lines.append("- **Tool:** `google-play-scraper` Python library")
    report_lines.append("- **Coverage:** 400+ reviews per bank (1,200+ total)")
    report_lines.append("- **Fields:** Review text, rating (1–5), date, bank name")
    report_lines.append("\n### Sentiment Analysis")
    report_lines.append("- **Primary Model:** DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`)")
    report_lines.append("- **Fallback:** VADER (lexicon-based) for comparison")
    report_lines.append("- **Output:** positive / negative / neutral labels with confidence scores")
    report_lines.append("\n### Thematic Analysis")
    report_lines.append("- **Method:** Keyword extraction via TF-IDF + rule-based theme assignment")
    report_lines.append("- **Themes:** Account Access Issues, Transaction Performance, UI & Design, Customer Support, Feature Requests, App Stability")
    report_lines.append("\n### Database")
    report_lines.append("- **System:** PostgreSQL")
    report_lines.append("- **Schema:** Relational (banks ↔ reviews with FK)")
    report_lines.append("\n---\n")

    # Cross-Bank Comparison
    report_lines.append("## Cross-Bank Comparison")
    comparison = compare_banks(df)
    report_lines.append("\n" + comparison.to_markdown(index=False))
    report_lines.append("\n---\n")

    # Bank-Specific Deep Dives
    for bank in sorted(df["bank"].unique()):
        report_lines.append(f"\n## {bank}: Deep Dive")

        # Drivers
        drivers, pain_points = extract_drivers_and_pain_points(df, bank)

        report_lines.append(f"\n### Satisfaction Drivers")
        if drivers:
            for i, d in enumerate(drivers, 1):
                report_lines.append(f"\n**{i}. {d['theme']}** ({d['review_count']} reviews, {d['positive_pct']}% positive)")
                report_lines.append(f"> \"{d['evidence']}\"")
        else:
            report_lines.append("\nNo strong positive themes identified. Consider running targeted satisfaction surveys.")

        report_lines.append(f"\n### Pain Points")
        if pain_points:
            for i, p in enumerate(pain_points, 1):
                report_lines.append(f"\n**{i}. {p['theme']}** ({p['review_count']} reviews, {p['negative_pct']}% negative)")
                report_lines.append(f"> \"{p['evidence']}\"")
        else:
            report_lines.append("\nNo dominant negative themes. Strong overall performance.")

        # Recommendations
        report_lines.append(f"\n### Recommendations")
        recs = generate_recommendations(df, bank)
        for rec in recs:
            report_lines.append(f"\n**P{rec['priority']}: {rec['title']}**")
            report_lines.append(f"\n*{rec['rationale']}*")
            report_lines.append("\n**Action Items:**")
            for action in rec['action_items']:
                report_lines.append(f"- {action}")
            report_lines.append(f"\n*Expected Impact:* {rec['expected_impact']}")

        report_lines.append("\n---\n")

    # Limitations
    report_lines.append("## Limitations & Ethical Considerations")
    report_lines.append("\n- **Scraping constraints:** Google Play Store rate limits may restrict review volume")
    report_lines.append("- **Language bias:** Analysis focuses on English reviews; Amharic feedback is excluded")
    report_lines.append("- **Self-selection bias:** Reviewers tend to be either very satisfied or very dissatisfied")
    report_lines.append("- **Temporal bias:** Reviews reflect current app versions; past issues may be resolved")
    report_lines.append("- **Privacy:** No personally identifiable information was collected or stored")
    report_lines.append("\n---\n")

    # Next Steps
    report_lines.append("## Suggested Next Steps")
    report_lines.append("\n1. **Quarterly tracking:** Re-run pipeline monthly to track sentiment trends")
    report_lines.append("2. **Amharic NLP:** Add Amharic language support for broader coverage")
    report_lines.append("3. **Competitor expansion:** Add more Ethiopian banks (Awash, Hibret, etc.)")
    report_lines.append("4. **Integration:** Feed real-time alerts to product teams via Slack/email")
    report_lines.append("5. **Predictive modeling:** Build churn prediction from review sentiment + app usage data")
    report_lines.append("\n---\n")

    # Footer
    report_lines.append("*Report generated by Omega Consultancy Data Analytics Pipeline*")
    report_lines.append(f"*Version: 1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate insights, visualizations, and final report"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to analyzed CSV (default: auto-detect latest)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for plots and report (default: reports/)",
    )
    args = parser.parse_args()

    # Load data
    input_path = Path(args.input) if args.input else find_latest_analyzed_file()
    logger.info(f"Loading analyzed data from: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")

    # Setup output directories
    output_dir = Path(args.output_dir)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------
    # GENERATE PLOTS
    # -------------------------------------------------------------------
    print_section("GENERATING VISUALIZATIONS")

    plots = [
        ("sentiment_distribution.png", plot_sentiment_distribution),
        ("rating_distribution.png", plot_rating_distribution),
        ("theme_frequency.png", plot_theme_frequency),
        ("wordcloud.png", plot_wordcloud),
    ]

    # Only add trend plot if sufficient date range
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    date_range = (df["date"].max() - df["date"].min()).days
    if date_range > 30:
        plots.append(("sentiment_trend.png", plot_sentiment_trend))

    # Radar chart
    plots.append(("comparison_radar.png", plot_comparison_radar))

    for filename, plot_func in plots:
        try:
            save_path = figures_dir / filename
            fig = plot_func(df, save_path=str(save_path))
            plt.close(fig)
            print(f"  ✅ {filename}")
        except Exception as e:
            logger.warning(f"Failed to generate {filename}: {e}")
            print(f"  ⚠️  {filename} (skipped)")

    print(f"\n  Figures saved to: {figures_dir}")

    # -------------------------------------------------------------------
    # GENERATE REPORT
    # -------------------------------------------------------------------
    print_section("GENERATING FINAL REPORT")
    report_content = generate_report(df, output_dir)
    report_path = output_dir / "final_report.md"
    report_path.write_text(report_content, encoding="utf-8")
    print(f"  ✅ Report saved to: {report_path}")

    # -------------------------------------------------------------------
    # PRINT SUMMARY
    # -------------------------------------------------------------------
    print_section("TASK 4 COMPLETE")
    print(f"  Total reviews analyzed: {len(df)}")
    print(f"  Banks covered: {', '.join(sorted(df['bank'].unique()))}")
    print(f"  Plots generated: {len(list(figures_dir.glob('*.png')))}")
    print(f"  Report: {report_path}")
    print(f"  Figures: {figures_dir}")
    print("=" * 70)

    # Preview
    print("\n📊 PREVIEW: Cross-Bank Comparison")
    print(compare_banks(df).to_string(index=False))


if __name__ == "__main__":
    main()




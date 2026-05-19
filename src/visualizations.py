"""
Visualization module for Task 4.

Creates publication-ready plots using Matplotlib and Seaborn.
All functions return matplotlib Figure objects for saving or display.
"""

import logging
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud

logger = logging.getLogger(__name__)

# Set default style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 11

# Color palette for banks
BANK_COLORS = {
    "Commercial Bank of Ethiopia": "#1f77b4",
    "Bank of Abyssinia": "#ff7f0e",
    "Dashen Bank": "#2ca02c",
    "CBE": "#1f77b4",
    "BOA": "#ff7f0e",
    "Dashen": "#2ca02c",
}

SENTIMENT_COLORS = {
    "positive": "#2ecc71",
    "negative": "#e74c3c",
    "neutral": "#95a5a6",
}


# ---------------------------------------------------------------------------
# Plot 1: Sentiment Distribution by Bank (Stacked Bar)
# ---------------------------------------------------------------------------

def plot_sentiment_distribution(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Stacked bar chart showing sentiment distribution per bank.
    """
    fig, ax = plt.subplots(figsize=figsize)

    sentiment_counts = (
        df.groupby(["bank", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["positive", "neutral", "negative"], fill_value=0)
    )

    sentiment_counts.plot(
        kind="bar",
        stacked=True,
        color=[SENTIMENT_COLORS[c] for c in sentiment_counts.columns],
        ax=ax,
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_title("Sentiment Distribution by Bank", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Bank", fontsize=12)
    ax.set_ylabel("Number of Reviews", fontsize=12)
    ax.legend(title="Sentiment", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha="center")
    ax.yaxis.grid(True, alpha=0.3)

    # Add percentage labels
    for i, bank in enumerate(sentiment_counts.index):
        total = sentiment_counts.loc[bank].sum()
        cumsum = 0
        for sentiment in sentiment_counts.columns:
            val = sentiment_counts.loc[bank, sentiment]
            if val > 0:
                pct = val / total * 100
                ax.text(
                    i, cumsum + val / 2, f"{pct:.0f}%",
                    ha="center", va="center", fontsize=9, color="white", fontweight="bold"
                )
            cumsum += val

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Plot 2: Rating Distribution per Bank (Boxplot + Swarm)
# ---------------------------------------------------------------------------

def plot_rating_distribution(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
) -> plt.Figure:
    """
    Boxplot with individual points showing rating distribution per bank.
    """
    fig, ax = plt.subplots(figsize=figsize)

    bank_order = sorted(df["bank"].unique())
    palette = [BANK_COLORS.get(b, "#333333") for b in bank_order]

    sns.boxplot(
        data=df,
        x="bank",
        y="rating",
        order=bank_order,
        palette=palette,
        hue="bank",
        legend=False,
        ax=ax,
        width=0.5,
    )

    # Add individual points with jitter
    sns.stripplot(
        data=df,
        x="bank",
        y="rating",
        order=bank_order,
        color="black",
        alpha=0.15,
        size=3,
        jitter=True,
        ax=ax,
    )

    ax.set_title("Rating Distribution per Bank", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Bank", fontsize=12)
    ax.set_ylabel("Star Rating (1–5)", fontsize=12)
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])

    # Add mean rating labels
    for i, bank in enumerate(bank_order):
        mean_rating = df[df["bank"] == bank]["rating"].mean()
        ax.text(
            i, 5.3, f"μ={mean_rating:.2f}",
            ha="center", va="bottom", fontsize=10, fontweight="bold", color=palette[i]
        )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Plot 3: Theme Frequency per Bank (Horizontal Bar)
# ---------------------------------------------------------------------------

def plot_theme_frequency(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: tuple = (12, 8),
    top_n: int = 6,
) -> plt.Figure:
    """
    Horizontal bar chart showing top themes per bank.
    """
    fig, axes = plt.subplots(1, len(df["bank"].unique()), figsize=figsize, sharey=True)
    if len(df["bank"].unique()) == 1:
        axes = [axes]

    bank_order = sorted(df["bank"].unique())

    for idx, bank in enumerate(bank_order):
        ax = axes[idx]
        bank_df = df[df["bank"] == bank]
        theme_counts = bank_df["identified_theme"].value_counts().head(top_n)

        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(theme_counts)))[::-1]
        bars = ax.barh(theme_counts.index[::-1], theme_counts.values[::-1], color=colors)

        ax.set_title(f"{bank}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Review Count", fontsize=10)
        if idx == 0:
            ax.set_ylabel("Theme", fontsize=10)

        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", ha="left", va="center", fontsize=9
            )

    fig.suptitle("Top Themes by Bank", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Plot 4: Sentiment Trend Over Time (Line Plot)
# ---------------------------------------------------------------------------

def plot_sentiment_trend(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    figsize: tuple = (12, 6),
    freq: str = "M",  # M=monthly, W=weekly, Q=quarterly
) -> plt.Figure:
    """
    Line plot showing sentiment trend over time per bank.
    """
    fig, ax = plt.subplots(figsize=figsize)

    df = df.copy()
    df["review_date"] = pd.to_datetime(df["date"])
    df["period"] = df["review_date"].dt.to_period(freq)

    # Calculate positive sentiment ratio per period per bank
    trend = (
        df.groupby(["bank", "period"])
        .apply(lambda x: (x["sentiment_label"] == "positive").mean() * 100)
        .reset_index(name="positive_pct")
    )
    trend["period"] = trend["period"].dt.to_timestamp()

    bank_order = sorted(df["bank"].unique())
    for bank in bank_order:
        bank_trend = trend[trend["bank"] == bank]
        ax.plot(
            bank_trend["period"],
            bank_trend["positive_pct"],
            marker="o",
            linewidth=2,
            markersize=6,
            label=bank,
            color=BANK_COLORS.get(bank, "#333333"),
        )

    ax.set_title("Positive Sentiment Trend Over Time", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Positive Sentiment (%)", fontsize=12)
    ax.legend(title="Bank", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Plot 5: Word Cloud per Bank
# ---------------------------------------------------------------------------

def plot_wordcloud(
    df: pd.DataFrame,
    bank: Optional[str] = None,
    save_path: Optional[str] = None,
    figsize: tuple = (12, 6),
) -> plt.Figure:
    """
    Generate word clouds for each bank (or a single bank).
    """
    if bank:
        banks = [bank]
        n_cols = 1
    else:
        banks = sorted(df["bank"].unique())
        n_cols = len(banks)

    fig, axes = plt.subplots(1, n_cols, figsize=figsize)
    if n_cols == 1:
        axes = [axes]

    for idx, b in enumerate(banks):
        texts = " ".join(df[df["bank"] == b]["review"].fillna("").astype(str))
        if not texts.strip():
            axes[idx].text(0.5, 0.5, "No data", ha="center", va="center")
            axes[idx].set_title(b)
            axes[idx].axis("off")
            continue

        wc = WordCloud(
            width=400,
            height=300,
            background_color="white",
            colormap="viridis",
            max_words=100,
            relative_scaling=0.5,
        ).generate(texts)

        axes[idx].imshow(wc, interpolation="bilinear")
        axes[idx].set_title(b, fontsize=12, fontweight="bold")
        axes[idx].axis("off")

    fig.suptitle("Most Frequent Words in Reviews", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig


# ---------------------------------------------------------------------------
# Plot 6: Comparison Radar Chart (Optional)
# ---------------------------------------------------------------------------

def plot_comparison_radar(
    df: pd.DataFrame,
    metrics: List[str] = ["avg_rating", "positive_pct", "theme_diversity"],
    save_path: Optional[str] = None,
    figsize: tuple = (8, 8),
) -> plt.Figure:
    """
    Radar chart comparing banks across multiple dimensions.
    """
    from math import pi

    # Calculate metrics per bank
    bank_metrics = []
    for bank in sorted(df["bank"].unique()):
        bank_df = df[df["bank"] == bank]
        avg_rating = bank_df["rating"].mean() / 5 * 100  # Normalize to 0-100
        positive_pct = (bank_df["sentiment_label"] == "positive").mean() * 100
        theme_diversity = bank_df["identified_theme"].nunique() / 6 * 100  # Normalize

        bank_metrics.append({
            "bank": bank,
            "avg_rating": avg_rating,
            "positive_pct": positive_pct,
            "theme_diversity": theme_diversity,
        })

    metrics_df = pd.DataFrame(bank_metrics)

    # Setup radar chart
    categories = ["Avg Rating", "Positive %", "Theme Diversity"]
    N = len(categories)

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for _, row in metrics_df.iterrows():
        values = [row["avg_rating"], row["positive_pct"], row["theme_diversity"]]
        values += values[:1]
        ax.plot(angles, values, "o-", linewidth=2, label=row["bank"],
                color=BANK_COLORS.get(row["bank"], "#333333"))
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    ax.set_title("Bank Comparison Across Dimensions", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Saved: {save_path}")

    return fig
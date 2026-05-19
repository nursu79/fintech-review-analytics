"""
Database module for PostgreSQL operations.
Handles connection, data insertion, and verification queries.

Uses psycopg2 for direct SQL operations.
"""

import logging
from contextlib import contextmanager
from typing import List, Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from config import DB_CONFIG

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

@contextmanager
def get_connection():
    """
    Context manager for PostgreSQL connections.
    Automatically commits on success, rolls back on exception.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_cursor(commit=False):
    """Context manager that yields a cursor from a connection."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# Schema operations
# ---------------------------------------------------------------------------

def init_schema(sql_file_path: str = "sql/schema.sql") -> None:
    """
    Execute the schema SQL file to create tables, indexes, and views.
    """
    with open(sql_file_path, "r") as f:
        sql = f.read()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    logger.info(f"Schema initialized from {sql_file_path}")


def drop_all_tables() -> None:
    """Drop all tables (use with caution — mainly for testing)."""
    with get_cursor(commit=True) as cur:
        cur.execute("DROP TABLE IF EXISTS reviews CASCADE;")
        cur.execute("DROP TABLE IF EXISTS banks CASCADE;")
    logger.warning("All tables dropped.")


# ---------------------------------------------------------------------------
# Data insertion
# ---------------------------------------------------------------------------

def get_bank_id_map() -> dict:
    """Return a mapping of bank_name -> bank_id from the banks table."""
    with get_cursor() as cur:
        cur.execute("SELECT bank_id, bank_name FROM banks;")
        rows = cur.fetchall()
    return {name: bid for bid, name in rows}


def insert_reviews(df: pd.DataFrame, batch_size: int = 500) -> int:
    """
    Insert analyzed review data into the reviews table.

    Args:
        df: DataFrame with columns:
            review_id, review, rating, date, bank, source,
            sentiment_label, sentiment_score, identified_theme, scraped_at
        batch_size: Number of rows per INSERT batch

    Returns:
        Number of rows inserted
    """
    bank_map = get_bank_id_map()

    # Map bank names to bank_ids
    df = df.copy()
    df["bank_id"] = df["bank"].map(bank_map)

    missing_banks = df["bank_id"].isna().sum()
    if missing_banks > 0:
        unknown = df[df["bank_id"].isna()]["bank"].unique()
        logger.warning(f"{missing_banks} reviews with unknown bank names: {unknown}")
        df = df.dropna(subset=["bank_id"])

    df["bank_id"] = df["bank_id"].astype(int)

    # Rename columns to match schema
    df = df.rename(columns={
        "review": "review_text",
        "date": "review_date",
    })

    # Ensure scraped_at exists
    if "scraped_at" not in df.columns:
        df["scraped_at"] = None

    # Select only needed columns
    data = df[[
        "review_id", "bank_id", "review_text", "rating", "review_date",
        "sentiment_label", "sentiment_score", "identified_theme",
        "source", "scraped_at",
    ]].values.tolist()

    insert_sql = """
        INSERT INTO reviews (
            review_id, bank_id, review_text, rating, review_date,
            sentiment_label, sentiment_score, identified_theme,
            source, scraped_at
        ) VALUES %s
        ON CONFLICT (review_id) DO UPDATE SET
            review_text = EXCLUDED.review_text,
            rating = EXCLUDED.rating,
            review_date = EXCLUDED.review_date,
            sentiment_label = EXCLUDED.sentiment_label,
            sentiment_score = EXCLUDED.sentiment_score,
            identified_theme = EXCLUDED.identified_theme;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                execute_values(cur, insert_sql, batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} rows")

    logger.info(f"Total rows inserted/updated: {len(data)}")
    return len(data)


# ---------------------------------------------------------------------------
# Verification queries
# ---------------------------------------------------------------------------

def count_reviews_per_bank() -> pd.DataFrame:
    """Return review counts and average ratings per bank."""
    query = """
        SELECT
            b.bank_name,
            COUNT(r.review_id) AS review_count,
            ROUND(AVG(r.rating), 2) AS avg_rating,
            MIN(r.review_date) AS earliest_date,
            MAX(r.review_date) AS latest_date
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_id, b.bank_name
        ORDER BY b.bank_id;
    """
    with get_cursor() as cur:
        cur.execute(query)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def check_nulls() -> pd.DataFrame:
    """Check for NULL values in key columns."""
    query = """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(*) FILTER (WHERE review_text IS NULL) AS null_review_text,
            COUNT(*) FILTER (WHERE rating IS NULL) AS null_rating,
            COUNT(*) FILTER (WHERE review_date IS NULL) AS null_date,
            COUNT(*) FILTER (WHERE sentiment_label IS NULL) AS null_sentiment,
            COUNT(*) FILTER (WHERE identified_theme IS NULL) AS null_theme
        FROM reviews;
    """
    with get_cursor() as cur:
        cur.execute(query)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def get_sample_reviews(bank_name: Optional[str] = None, limit: int = 5) -> pd.DataFrame:
    """Fetch sample reviews for verification."""
    if bank_name:
        query = """
            SELECT r.*, b.bank_name
            FROM reviews r
            JOIN banks b ON r.bank_id = b.bank_id
            WHERE b.bank_name = %s
            LIMIT %s;
        """
        params = (bank_name, limit)
    else:
        query = """
            SELECT r.*, b.bank_name
            FROM reviews r
            JOIN banks b ON r.bank_id = b.bank_id
            LIMIT %s;
        """
        params = (limit,)

    with get_cursor() as cur:
        cur.execute(query, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def verify_database_health() -> dict:
    """
    Run a comprehensive health check on the database.
    Returns a dict with verification results.
    """
    results = {
        "banks_table": False,
        "reviews_table": False,
        "banks_populated": False,
        "reviews_count": 0,
        "null_check_passed": False,
        "overall_status": "FAIL",
    }

    try:
        # Check banks table
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM banks;")
            bank_count = cur.fetchone()[0]
            results["banks_table"] = True
            results["banks_populated"] = bank_count >= 3

        # Check reviews table
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM reviews;")
            review_count = cur.fetchone()[0]
            results["reviews_table"] = True
            results["reviews_count"] = review_count

        # Check nulls
        null_df = check_nulls()
        null_counts = null_df.iloc[0].drop("total_rows").sum()
        results["null_check_passed"] = null_counts == 0

        # Overall status
        if all([
            results["banks_table"],
            results["reviews_table"],
            results["banks_populated"],
            results["reviews_count"] >= 400,
            results["null_check_passed"],
        ]):
            results["overall_status"] = "PASS"

    except Exception as e:
        logger.error(f"Health check failed: {e}")

    return results
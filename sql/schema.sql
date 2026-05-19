-- ============================================
-- Fintech Review Analytics — PostgreSQL Schema
-- Database: bank_reviews
-- ============================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS banks CASCADE;

-- ============================================
-- Banks Table: Metadata about each bank/app
-- ============================================
CREATE TABLE banks (
    bank_id         SERIAL PRIMARY KEY,
    bank_name       VARCHAR(100) NOT NULL,
    app_name        VARCHAR(100) NOT NULL,
    play_store_id   VARCHAR(100),
    country         VARCHAR(10) DEFAULT 'ET',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert the three Ethiopian banks
INSERT INTO banks (bank_name, app_name, play_store_id) VALUES
    ('Commercial Bank of Ethiopia', 'Commercial Bank of Ethiopia Mobile', 'com.cbe.mobile'),
    ('Bank of Abyssinia', 'Bank of Abyssinia Mobile', 'com.bankofabyssinia.boamobile.retail'),
    ('Dashen Bank', 'Dashen Bank SuperApp', 'com.dashen');

-- ============================================
-- Reviews Table: Scraped and processed reviews
-- ============================================
CREATE TABLE reviews (
    review_id           VARCHAR(50) PRIMARY KEY,
    bank_id             INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
    review_text         TEXT NOT NULL,
    rating              INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date         DATE NOT NULL,
    sentiment_label     VARCHAR(20) CHECK (sentiment_label IN ('positive', 'negative', 'neutral')),
    sentiment_score     DECIMAL(5,4),
    identified_theme    VARCHAR(50),
    source              VARCHAR(50) DEFAULT 'Google Play',
    scraped_at          TIMESTAMP,
    inserted_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX idx_reviews_bank_id ON reviews(bank_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX idx_reviews_theme ON reviews(identified_theme);
CREATE INDEX idx_reviews_date ON reviews(review_date);

-- ============================================
-- Verification Views
-- ============================================

-- View: Review counts per bank
CREATE OR REPLACE VIEW v_reviews_per_bank AS
SELECT
    b.bank_name,
    COUNT(r.review_id) AS review_count,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    ROUND(AVG(r.sentiment_score), 4) AS avg_sentiment_score
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name;

-- View: Sentiment distribution per bank
CREATE OR REPLACE VIEW v_sentiment_distribution AS
SELECT
    b.bank_name,
    r.sentiment_label,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY b.bank_id), 1) AS pct
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name, r.sentiment_label;

-- View: Theme distribution per bank
CREATE OR REPLACE VIEW v_theme_distribution AS
SELECT
    b.bank_name,
    r.identified_theme,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY b.bank_id), 1) AS pct
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_id, b.bank_name, r.identified_theme;
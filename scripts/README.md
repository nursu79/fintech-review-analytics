# Scripts

This folder contains standalone execution scripts for the pipeline.

| Script | Task | Purpose |
|--------|------|---------|
| `scrape_reviews.py` | Task 1 | Scrape Google Play Store reviews |
| `preprocess_reviews.py` | Task 1 | Clean and normalize raw data |
| `sentiment_analysis.py` | Task 2 | Classify sentiment and extract themes |
| `load_to_postgres.py` | Task 3 | Insert cleaned data into PostgreSQL |
| `generate_insights.py` | Task 4 | Create visualizations and reports |

Run each script from the project root:

```bash
python scripts/scrape_reviews.py
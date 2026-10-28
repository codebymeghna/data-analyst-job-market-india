"""
Data cleaning pipeline for the India Tech Job Market dataset.

Reads the raw CSV, standardises and validates it, adds analysis-ready
columns, and writes data/cleaned_jobs.csv.

Run from the project root:
    python src/data_cleaning.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "india_job_market_2024_2026.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "cleaned_jobs.csv"

EXPERIENCE_ORDER = ["Fresher", "Junior", "Mid", "Senior", "Lead"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def load_data(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw job postings CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found at: {path}")
    df = pd.read_csv(path)
    log.info("Loaded %d rows and %d columns", *df.shape)
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case column names and strip stray whitespace."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace and collapse repeated spaces in all text columns."""
    df = df.copy()
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = (
                df[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
            )
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert date_posted to datetime; unparseable values become NaT and are dropped."""
    df = df.copy()
    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
    bad = df["date_posted"].isna().sum()
    if bad:
        log.warning("Dropping %d rows with invalid dates", bad)
        df = df.dropna(subset=["date_posted"])
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop repeated job IDs and fully duplicated rows."""
    before = len(df)
    df = df.drop_duplicates(subset="job_id").drop_duplicates()
    log.info("Removed %d duplicate rows", before - len(df))
    return df


def validate_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with impossible values (non-positive salary/openings, bad ratings)."""
    invalid = (
        (df["salary_lpa"] <= 0)
        | (df["openings"] <= 0)
        | (df["applicants"] < 0)
        | (~df["company_rating"].between(0, 5))
    )
    log.info("Removed %d rows with invalid values", invalid.sum())
    return df.loc[~invalid]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create analysis-ready columns."""
    df = df.copy()

    # Short experience label, e.g. "Senior (6-10 yrs)" -> "Senior"
    df["experience_group"] = df["experience_level"].str.extract(r"^([A-Za-z]+)", expand=False)
    df["experience_group"] = pd.Categorical(
        df["experience_group"], categories=EXPERIENCE_ORDER, ordered=True
    )
    unmapped = df["experience_group"].isna().sum()
    if unmapped:
        log.warning("%d rows have an unrecognised experience level", unmapped)

    # Competition metric
    df["applicants_per_opening"] = (df["applicants"] / df["openings"]).round(2)

    # Time fields for trend analysis
    df["year"] = df["date_posted"].dt.year
    df["month"] = df["date_posted"].dt.month
    df["year_month"] = df["date_posted"].dt.to_period("M").astype(str)

    # Skills
    df["skill_count"] = df["skills_required"].str.split(",").str.len()

    # Data Analyst flag (we will review the job titles in the analysis step)
    df["is_data_analyst"] = df["job_title"].str.contains("data analyst", case=False, na=False)

    # Salary outliers: IQR rule applied within each experience group
    grp = df.groupby("experience_group", observed=True)["salary_lpa"]
    q1, q3 = grp.transform(lambda s: s.quantile(0.25)), grp.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    df["salary_outlier"] = (df["salary_lpa"] < q1 - 1.5 * iqr) | (df["salary_lpa"] > q3 + 1.5 * iqr)

    return df


def save_data(df: pd.DataFrame, path: Path = CLEAN_PATH) -> None:
    """Write the cleaned dataset to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved cleaned data to %s", path)


def clean_pipeline() -> pd.DataFrame:
    """Run the full cleaning pipeline and return the cleaned DataFrame."""
    df = load_data()
    df = standardize_columns(df)
    df = clean_text_columns(df)
    df = parse_dates(df)
    df = remove_duplicates(df)
    df = validate_values(df)
    df = add_features(df)
    save_data(df)
    return df


if __name__ == "__main__":
    cleaned = clean_pipeline()
    print("\n--- Cleaning summary ---")
    print(f"Final shape: {cleaned.shape}")
    print(f"Date range: {cleaned['date_posted'].min().date()} to {cleaned['date_posted'].max().date()}")
    print(f"Data Analyst postings: {cleaned['is_data_analyst'].sum()}")
    print(f"Salary outliers flagged: {cleaned['salary_outlier'].sum()}")
    print("\nExperience groups:")
    print(cleaned["experience_group"].value_counts(sort=False).to_string())
    print("\nTop 15 job titles:")
    print(cleaned["job_title"].value_counts().head(15).to_string())
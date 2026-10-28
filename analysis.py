"""
Analysis and visualisation for the Data Analyst job market (India, 2024-2026).

Reads data/cleaned_jobs.csv (created by data_cleaning.py), prints key findings,
saves them to data/key_findings.json, and writes five charts to visualizations/.

Run from the project root:
    python src/analysis.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = PROJECT_ROOT / "data" / "cleaned_jobs.csv"
FINDINGS_PATH = PROJECT_ROOT / "data" / "key_findings.json"
VIZ_DIR = PROJECT_ROOT / "visualizations"

EXPERIENCE_ORDER = ["Fresher", "Junior", "Mid", "Senior", "Lead"]
MIN_SKILL_POSTINGS = 15  # ignore skills too rare to compare reliably

PRIMARY = "#1F6FEB"
SECONDARY = "#9AA5B1"

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_clean(path: Path = CLEAN_PATH) -> pd.DataFrame:
    """Load the cleaned dataset and restore column types lost in CSV format."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run src/data_cleaning.py first.")
    df = pd.read_csv(path, parse_dates=["date_posted"])
    df["experience_group"] = pd.Categorical(
        df["experience_group"], categories=EXPERIENCE_ORDER, ordered=True
    )
    df["skills_list"] = df["skills_required"].str.split(",").map(
        lambda items: [s.strip() for s in items if s.strip()]
    )
    return df


def data_analyst_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Return only Data Analyst postings."""
    return df[df["is_data_analyst"]].copy()


# --------------------------------------------------------------------------- #
# Analysis functions
# --------------------------------------------------------------------------- #
def skill_demand(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Top skills with posting counts and share of postings (%)."""
    counts = df["skills_list"].explode().value_counts().head(top_n)
    out = counts.rename_axis("skill").reset_index(name="postings")
    out["pct_of_postings"] = (out["postings"] / len(df) * 100).round(1)
    return out


def skill_salary_premium(df: pd.DataFrame, min_postings: int = MIN_SKILL_POSTINGS) -> pd.DataFrame:
    """
    Experience-adjusted salary effect of each skill.

    Salary is first expressed as % above/below the median of the same experience
    group, so seniority cannot masquerade as a skill premium. Then we compare
    postings that list the skill against postings that do not.
    """
    df = df.copy()
    peer_median = df.groupby("experience_group", observed=True)["salary_lpa"].transform("median")
    df["salary_vs_peers_pct"] = (df["salary_lpa"] / peer_median - 1) * 100

    rows = []
    for skill in df["skills_list"].explode().dropna().unique():
        has_skill = df["skills_list"].map(lambda s: skill in s)
        if has_skill.sum() < min_postings:
            continue
        with_med = df.loc[has_skill, "salary_vs_peers_pct"].median()
        without_med = df.loc[~has_skill, "salary_vs_peers_pct"].median()
        rows.append(
            {
                "skill": skill,
                "postings": int(has_skill.sum()),
                "median_vs_peers_with_pct": round(with_med, 1),
                "median_vs_peers_without_pct": round(without_med, 1),
                "difference_pct_points": round(with_med - without_med, 1),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("difference_pct_points", ascending=False)
        .reset_index(drop=True)
    )

def salary_by_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Median salary per experience group: Data Analysts vs all tech roles."""
    da = data_analyst_subset(df)
    all_roles = df.groupby("experience_group", observed=True)["salary_lpa"].median()
    analysts = da.groupby("experience_group", observed=True)["salary_lpa"].median()
    counts = da.groupby("experience_group", observed=True).size()
    return pd.DataFrame(
        {"all_tech_roles": all_roles, "data_analyst": analysts, "da_postings": counts}
    ).round(2)


def top_cities(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Cities with the most postings. 'Remote' is a work mode, not a city, so it is excluded."""
    cities = df[df["city"].str.lower() != "remote"]
    out = cities["city"].value_counts().head(top_n).rename_axis("city").reset_index(name="postings")
    out["pct_of_postings"] = (out["postings"] / len(df) * 100).round(1)
    return out


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Number of postings per month."""
    out = df.groupby("year_month").size().rename("postings").reset_index()
    out["month_start"] = pd.to_datetime(out["year_month"])
    return out.sort_values("month_start").reset_index(drop=True)


def competition_by_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Median applicants per opening by experience group, for Data Analysts."""
    da = data_analyst_subset(df)
    return (
        da.groupby("experience_group", observed=True)["applicants_per_opening"]
        .median()
        .round(1)
        .rename("median_applicants_per_opening")
        .reset_index()
    )


# --------------------------------------------------------------------------- #
# Key findings
# --------------------------------------------------------------------------- #
def compute_key_findings(df: pd.DataFrame) -> dict:
    """Collect the headline numbers used in the README and notebook."""
    da = data_analyst_subset(df)
    fresher_da = da[da["experience_group"] == "Fresher"]
    fresher_all = df[df["experience_group"] == "Fresher"]

    top_da_skills = skill_demand(da, 5)
    top_fresher_skills = skill_demand(fresher_da, 5)
    premium = skill_salary_premium(da)

    return {
        "total_postings": int(len(df)),
        "date_range": [str(df["date_posted"].min().date()), str(df["date_posted"].max().date())],
        "data_analyst_postings": int(len(da)),
        "data_analyst_share_pct": round(len(da) / len(df) * 100, 1),
        "fresher_da_postings": int(len(fresher_da)),
        "fresher_da_share_of_da_pct": round(len(fresher_da) / len(da) * 100, 1),
        "da_median_salary_lpa": round(float(da["salary_lpa"].median()), 1),
        "fresher_da_median_salary_lpa": round(float(fresher_da["salary_lpa"].median()), 1),
        "fresher_all_tech_median_salary_lpa": round(float(fresher_all["salary_lpa"].median()), 1),
        "da_median_applicants_per_opening": round(float(da["applicants_per_opening"].median()), 1),
        "all_median_applicants_per_opening": round(float(df["applicants_per_opening"].median()), 1),
        "da_top_skills": top_da_skills.to_dict("records"),
        "fresher_da_top_skills": top_fresher_skills.to_dict("records"),
        "da_top_skill_premiums": premium.head(5).to_dict("records"),
        "da_work_mode_pct": (da["work_mode"].value_counts(normalize=True) * 100).round(1).to_dict(),
        "top_cities_all_roles": top_cities(df, 5).to_dict("records"),
    }


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def _setup_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"axes.titleweight": "bold", "axes.titlesize": 14, "figure.dpi": 100})


def _save(fig: plt.Figure, name: str) -> None:
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    path = VIZ_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log.info("Saved %s", path.name)


def plot_top_skills(df: pd.DataFrame) -> None:
    da = data_analyst_subset(df)
    data = skill_demand(da, 10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(data["skill"], data["pct_of_postings"], color=PRIMARY)
    ax.bar_label(bars, fmt="%.0f%%", padding=3)
    ax.set_xlabel("Share of Data Analyst postings (%)")
    ax.set_title(f"Top 10 Skills in Data Analyst Job Postings (n={len(da)})", loc="left")
    ax.set_xlim(0, data["pct_of_postings"].max() * 1.15)
    sns.despine(left=True)
    _save(fig, "top_skills.png")


def plot_salary_by_experience(df: pd.DataFrame) -> None:
    table = salary_by_experience(df).reset_index()
    long = table.melt(
        id_vars="experience_group",
        value_vars=["data_analyst", "all_tech_roles"],
        var_name="group",
        value_name="median_salary",
    )
    long["group"] = long["group"].map({"data_analyst": "Data Analyst", "all_tech_roles": "All tech roles"})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=long, x="experience_group", y="median_salary", hue="group",
        palette=[PRIMARY, SECONDARY], ax=ax,
    )
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=2, fontsize=9)
    ax.set_xlabel("Experience level")
    ax.set_ylabel("Median salary (LPA)")
    ax.set_title("Median Salary by Experience Level", loc="left")
    ax.legend(title=None, frameon=False)
    sns.despine()
    _save(fig, "salary_by_experience.png")


def plot_salary_distribution(df: pd.DataFrame) -> None:
    da = data_analyst_subset(df)
    median = da["salary_lpa"].median()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.histplot(da["salary_lpa"], bins=30, kde=True, color=PRIMARY, ax=ax)
    ax.axvline(median, color="#D1242F", linestyle="--", linewidth=1.5)
    ax.text(median, ax.get_ylim()[1] * 0.95, f"  Median: {median:.1f} LPA", color="#D1242F", va="top")
    ax.set_xlabel("Salary (LPA)")
    ax.set_ylabel("Number of postings")
    ax.set_title(f"Salary Distribution of Data Analyst Postings (n={len(da)})", loc="left")
    sns.despine()
    _save(fig, "salary_distribution.png")


def plot_top_cities(df: pd.DataFrame) -> None:
    data = top_cities(df, 10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(data["city"], data["postings"], color=PRIMARY)
    ax.bar_label(bars, padding=3)
    ax.set_xlabel("Number of job postings (all tech roles)")
    ax.set_title("Top 10 Cities by Job Postings (excluding Remote)", loc="left")
    ax.set_xlim(0, data["postings"].max() * 1.12)
    sns.despine(left=True)
    _save(fig, "top_cities.png")


def plot_monthly_trends(df: pd.DataFrame) -> None:
    all_trend = monthly_trend(df)
    da_trend = monthly_trend(data_analyst_subset(df))
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, trend, title, color in [
        (axes[0], all_trend, "All tech roles", SECONDARY),
        (axes[1], da_trend, "Data Analyst roles", PRIMARY),
    ]:
        ax.plot(trend["month_start"], trend["postings"], marker="o", color=color, linewidth=2)
        ax.set_ylabel("Postings")
        ax.set_title(title, loc="left", fontsize=11)
    axes[1].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %Y"))
    plt.setp(axes[1].get_xticklabels(), rotation=45, ha="right")
    fig.suptitle("Monthly Job Posting Trends", x=0.125, ha="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    sns.despine()
    _save(fig, "monthly_job_trends.png")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    _setup_style()
    df = load_clean()

    findings = compute_key_findings(df)
    FINDINGS_PATH.write_text(json.dumps(findings, indent=2, default=str), encoding="utf-8")
    log.info("Saved key findings to %s", FINDINGS_PATH.name)

    plot_top_skills(df)
    plot_salary_by_experience(df)
    plot_salary_distribution(df)
    plot_top_cities(df)
    plot_monthly_trends(df)

    print("\n=== KEY FINDINGS ===")
    print(json.dumps(findings, indent=2, default=str))
    print("\n=== SALARY BY EXPERIENCE ===")
    print(salary_by_experience(df).to_string())
    print("\n=== DA COMPETITION BY EXPERIENCE ===")
    print(competition_by_experience(df).to_string(index=False))


if __name__ == "__main__":
    main()
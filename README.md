# What Does a Fresher Need to Land a Data Analyst Job in India?

An end-to-end Python analysis of **5,000 Indian tech job postings (June 2024 – April 2026)**, focused on one practical question: *which skills, salaries and hiring conditions should an aspiring Data Analyst expect?*

**Tools:** Python · pandas · NumPy · Matplotlib · Seaborn · Jupyter

---

## Highlights

| Finding | Result |
|---|---|
| Postings analysed | 5,000 (254 Data Analyst, 46 at fresher level) |
| Most requested skill for freshers | **SQL**, in 73.9% of fresher Data Analyst postings |
| Next most requested | Power BI (71.7%), Statistics (67.4%), Data Visualization (67.4%), Python (65.2%) |
| Median fresher Data Analyst salary | **5.35 LPA**, rising to 56.95 LPA at Lead level (roughly 10x) |
| Competition | About **89 applicants per opening** for Data Analyst roles |
| Do skills raise pay? | **Not once experience is controlled for.** The largest effect was +1.3 percentage points |

> Read the [Limitations](#limitations) section before using any of these numbers. The dataset appears to be synthetic.

---

## Visual Results

### Skills employers ask for
![top skills](https://raw.githubusercontent.com/codebymeghna/data-analyst-job-market-india/main/visualizations/top_skills.png)

### Salary by experience level
![salary by experience](https://raw.githubusercontent.com/codebymeghna/data-analyst-job-market-india/main/visualizations/salary_by_experience.png)

### Salary distribution
![salary distribution](https://raw.githubusercontent.com/codebymeghna/data-analyst-job-market-india/main/visualizations/salary_distribution.png)

### Where the jobs are
![top cities](https://raw.githubusercontent.com/codebymeghna/data-analyst-job-market-india/main/visualizations/top_cities.png)

### Hiring trend over time
![Monthly job trends](https://raw.githubusercontent.com/codebymeghna/data-analyst-job-market-india/main/visualizations/monthly_job_trends.png)

---

## A Methodological Point Worth Highlighting: Confounding

My first comparison of skill vs salary showed that **Statistics "added" 4.6 LPA** while Excel, Python and Tableau seemed to *reduce* pay. This was misleading: salary is driven mainly by seniority (about 5 LPA for freshers vs 57 LPA for leads), and skills that happen to be more common in senior postings looked well paid.

**Fix:** each salary was first expressed as a percentage above or below the median of its own experience group, and *then* compared between postings with and without each skill. After this adjustment, every skill effect shrank to around one percentage point. The notebook shows the naive and adjusted comparisons side by side.

---

## Project Structure

```
data-analyst-job-market-india/
├── data/
│   ├── india_job_market_2024_2026.csv   # raw data (unchanged)
│   ├── cleaned_jobs.csv                 # output of data_cleaning.py
│   └── key_findings.json                # headline numbers from analysis.py
├── src/
│   ├── data_cleaning.py                 # load, validate, clean, engineer features
│   └── analysis.py                      # analysis functions and chart generation
├── notebooks/
│   └── job_market_analysis.ipynb        # narrative walkthrough of the analysis
├── visualizations/                      # the five charts above
├── requirements.txt
├── .gitignore
└── README.md
```

## How to Run

```bash
# 1. Clone the repository and enter it
git clone https://github.com/codebymeghna/data-analyst-job-market-india.git
cd data-analyst-job-market-india

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Clean the data, then run the analysis (run from the project root)
python src/data_cleaning.py
python src/analysis.py

# 5. Open the notebook for the full walkthrough
jupyter notebook notebooks/job_market_analysis.ipynb
```

## Methodology

1. **Cleaning** (`data_cleaning.py`): standardised column names and text, parsed dates, checked duplicates and invalid values, then engineered features: experience group, applicants per opening, month fields, skill count, a Data Analyst flag and per-experience-group salary outliers (IQR rule).
2. **Scope:** a posting is a *Data Analyst* role only if its title contains "Data Analyst". This strict definition is reproducible, but it leaves a small fresher sample (n = 46).
3. **Analysis** (`analysis.py`): skill demand, salary by experience, experience-adjusted skill effects, city and work-mode distribution, monthly trends and competition (applicants ÷ openings).
4. **Reporting:** sample sizes are shown next to Data Analyst results, and "Remote" is excluded from the city ranking because it is a work mode, not a city.

## Limitations

Several checks suggest the dataset is **synthetic or heavily simulated**, not scraped from real postings:

- Data Analyst salaries are almost identical to the all-roles median at every experience level.
- Applicants per opening are nearly the same for every role (about 89 vs 88).
- The top five Data Analyst skills all fall in a narrow 63–70% band.
- Some records are implausible (for example, a government PSU listed under EdTech).

Therefore, the findings describe **this dataset, not the real Indian job market**, and fresher results rest on only 46 postings. The value of this project is the reproducible method, which can be re-run on real scraped data.

## Possible Next Steps

- Repeat the analysis on a real, scraped dataset
- Widen the role definition to include Business Analyst and BI Analyst titles
- Add statistical tests (for example, bootstrapped confidence intervals) for salary comparisons
- Build an interactive dashboard

## Data Source

Dataset: public Kaggle dataset of Indian tech job postings, 2024–2026. **[https://github.com/powaromkar931-netizen/India_Tech_Job_Market_Analysis?utm_source=chatgpt.com]** The copy used in this project was obtained from a public GitHub repository that mirrors it. Analysis, code and conclusions in this repository are my own.

## Author

**[Meghna Chauhan]** · [GitHub](https://github.com/codebymeghna)

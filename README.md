# The Evolution of Tech Skills — CS 418 Team Blue

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Collect and clean (Ammani)
```bash
python src/collect_data.py --start-year 2023 --end-year 2026
python src/clean_data.py
```
The collection script queries public Hacker News Algolia search results and keeps only top-level comments. Inspect the collection logs and validate a sample against the original threads; API results may be incomplete. For the deadline, use 2023–2026 rather than assuming full historical coverage since 2011. The `remote` field indicates the word appears, **not** that the job is confirmed remote. `company` is a heuristic (text before the first `|`); `role`, `location`, and `salary` are intentionally blank pending reliable extraction. `skills` are keyword matches, not necessarily required skills.

## Teammates
- Teresa: `notebooks/02_visualizations_teresa.ipynb` (3 charts)
- Kendi: `notebooks/03_visualizations_kendi.ipynb` (2 charts)
- Daisy: `notebooks/04_machine_learning.ipynb` (2 analyses + baselines)
- Ammani: data scripts and `notebooks/01_data_collection.ipynb`

Read `data/processed/jobs_cleaned.csv` with `pd.read_csv(...)`. If needed, convert `skills` to lists using `str.split(', ')`. Commit to separate branches and open pull requests. Do not overwrite teammates' notebooks.

## Submission
Combine work in `notebooks/progress_report.ipynb`, run all cells top-to-bottom, commit to private GitHub, and export a PDF for Gradescope by Nov 13. Include project introduction, changes since proposal, data preparation, EDA, five explained visualizations with member names, two ML analyses with baselines and member names, reflection, and next steps.

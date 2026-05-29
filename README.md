# StatClean — Web-Based Statistical Data Cleaning & Validation System

Automated preprocessing and validation system for statistical data, built as a capstone project based on field experience at **BPS Kota Malang**.

## The Problem

Statistical data processing at BPS still relies heavily on manual spreadsheet operations — checking missing values, fixing typos, validating codes, removing duplicates, and cross-checking columns. This is time-consuming and error-prone.

## What This System Does

| Feature | Description |
|---------|-------------|
| **Upload** | Accept `.xlsx`, `.xls`, `.csv` (max 50 MB) |
| **Auto Cleaning** | Detect & handle missing values (drop/fill), remove duplicates, strip whitespace |
| **Format Validation** | Validate gender (L/P), age range (0–120), region codes, and custom patterns |
| **Cross-Validation** | Rule-based checks (e.g., "student" with age > 40 = suspicious) |
| **Outlier Detection** | Z-score and IQR-based statistical outlier detection |
| **Quality Score** | Composite 0–100 score with grade based on completeness, consistency, duplicates, format, and outliers |
| **Visual Dashboard** | Interactive charts (missing data, error distribution, quality breakdown) |
| **Export** | Download cleaned Excel + validation report (HTML) |

## Architecture

```
Upload Dataset → Data Parser → Preprocessing Engine → Validation Engine → Analytics → Export
```

## Tech Stack

- **Backend:** Flask, Pandas, NumPy, SciPy, Matplotlib
- **Frontend:** HTML, CSS, Chart.js
- **Storage:** SQLite (session-based, no DB persistence needed)

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000`.

## Deploy to Vercel

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/import/project?template=naelrudd/statistical-data-cleaning-system)

1. Push to GitHub
2. Import repo at https://vercel.com/import
3. Framework preset: **Other**
4. Build command: `pip install -r requirements.txt`
5. Output directory: leave blank
6. Deploy — done.

## Project Structure

```
├── app.py                  # Flask application
├── config.py               # Validation rules & configuration
├── engine/                 # Core processing modules
│   ├── parser.py           # File parsing (Excel/CSV)
│   ├── cleaner.py          # Missing values & duplicates
│   ├── validator.py        # Format & cross-validation
│   ├── outlier.py          # Z-score & IQR outlier detection
│   ├── quality.py          # Data quality scoring
│   └── exporter.py         # Export & chart generation
├── templates/              # HTML templates (Jinja2)
├── static/                 # Static assets
├── uploads/                # Uploaded files
├── exports/                # Generated exports
└── requirements.txt        # Python dependencies
```

## Evaluation Metrics

- **Time efficiency:** Manual ~45 min vs System ~6 min
- **Error reduction:** Manual baseline vs automated validation
- **SUS Testing:** User satisfaction scoring

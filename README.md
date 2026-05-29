# StatClean — Web-Based Statistical Data Cleaning & Validation System

Automated preprocessing and validation system for statistical data, built as a capstone project based on field experience at **BPS Kota Malang**.

## The Problem

Statistical data processing at BPS still relies heavily on manual spreadsheet operations — checking missing values, fixing typos, validating codes, removing duplicates, and cross-checking columns. This is time-consuming and error-prone.

## Features

| Feature | Description |
|---------|-------------|
| **Upload** | Accept `.xlsx`, `.xls`, `.csv` (max 30 MB) |
| **Auto Cleaning** | Detect & handle missing values (drop/fill mean/median/mode), remove duplicates, strip whitespace |
| **Format Validation** | Validate gender (L/P), age range (0–120), region codes, and custom patterns |
| **Cross-Validation** | Rule-based checks — e.g., "student" with age > 40, child < 15 working, age < 15 married |
| **Outlier Detection** | Z-score (default > 3σ) and IQR-based statistical outlier detection |
| **Quality Score** | Composite 0–100 score with letter grade (A–D) based on 5 weighted dimensions |
| **Visual Dashboard** | Step-by-step workflow with interactive charts (missing data, error distribution, quality breakdown) |
| **Export** | Download cleaned Excel + validation report (HTML) with embedded charts |

## Architecture

```
Upload Dataset (Excel/CSV)
       ↓
Data Parser (Pandas/Openpyxl)
       ↓
Preprocessing Engine
  ├── Missing Value Handling
  ├── Duplicate Removal
  └── Whitespace Cleaning
       ↓
Validation Engine
  ├── Format Validation (gender, age, codes)
  ├── Cross-Field Rule Validation
  └── Statistical Outlier Detection (Z-score, IQR)
       ↓
Analytics & Summary
  ├── Data Quality Score (0–100)
  ├── Visualization Dashboard (Chart.js)
  └── Matplotlib Charts (summary, errors, scores)
       ↓
Export Cleaned Data + Report
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask (Python) |
| **Data Processing** | Pandas, NumPy, SciPy |
| **Charts (report)** | Matplotlib |
| **Charts (dashboard)** | Chart.js |
| **Storage** | Cloudflare R2 (S3-compatible) — fallback to local `/tmp` |
| **Deployment** | Vercel (serverless) |

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Project Structure

```
├── app.py                  # Flask application (routes & API)
├── config.py               # Validation rules, thresholds, paths
├── r2_storage.py           # Cloudflare R2 S3 client wrapper
├── engine/                 # Core processing modules
│   ├── parser.py           # File parsing (Excel/CSV → DataFrame)
│   ├── cleaner.py          # Missing values & duplicates
│   ├── validator.py        # Format & cross-validation
│   ├── outlier.py          # Z-score & IQR outlier detection
│   ├── quality.py          # Data quality scoring (5 dimensions)
│   └── exporter.py         # Export & chart generation
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Layout with Chart.js CDN
│   ├── index.html          # Landing page
│   ├── upload.html         # Upload form with drag & drop
│   └── dashboard.html      # Full pipeline dashboard
├── api/
│   └── index.py            # Vercel serverless entry point
├── vercel.json             # Vercel deployment config
├── .env.example            # R2 credentials template
├── requirements.txt        # Python dependencies
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/upload` | GET/POST | Upload dataset |
| `/dashboard/<id>` | GET | Pipeline dashboard |
| `/api/<id>/preview` | GET | Data preview (first 20 rows) |
| `/api/<id>/clean` | POST | Auto-clean (missing values, duplicates) |
| `/api/<id>/validate` | POST | Format & cross-validation |
| `/api/<id>/outliers` | POST | Outlier detection |
| `/api/<id>/quality` | GET | Quality score computation |
| `/api/<id>/charts` | GET | Matplotlib chart images (base64) |
| `/export/<id>/excel` | GET | Download cleaned Excel |
| `/export/<id>/report` | GET | Download validation report (HTML) |

## Validation Rules

### Format Rules
- **Gender:** Must be `L` or `P`
- **Age:** Must be 0–120
- **Region Codes:** Regex pattern matching (customizable)

### Cross-Field Rules
| Rule | Condition | Trigger |
|------|-----------|---------|
| Student age > 40 | status == "sekolah" | umur > 40 |
| Working age < 10 | status_kerja == "bekerja" | umur < 10 |
| Married age < 15 | status_perkawinan == "kawin" | umur < 15 |
| Pensioner age < 45 | status_kerja == "pensiun" | umur < 45 |
| Child working | — | umur < 15 AND bekerja |

## Quality Scoring

| Dimension | Weight | Metric |
|-----------|--------|--------|
| Completeness | 30% | Missing values / total cells |
| Consistency | 25% | Cross-validation errors / rows |
| No Duplicates | 20% | Duplicate rows / total rows |
| Format Validity | 15% | Format errors / total cells |
| No Outliers | 10% | Outliers / total rows |

**Grade:** A (≥90), B (≥75), C (≥60), D (<60)

## Deployment

### Vercel (Live)

1. Push to GitHub
2. Import at https://vercel.com/import
3. Set environment variables:
   - `R2_ACCOUNT_ID` — Cloudflare R2 Account ID
   - `R2_ACCESS_KEY` — R2 S3 Access Key
   - `R2_SECRET_KEY` — R2 S3 Secret Key
   - `R2_BUCKET` — Bucket name (default: `statclean`)
4. Deploy

## Evaluation Metrics

- **Time efficiency:** Manual ~45 min vs System ~6 min
- **Error reduction:** Manual baseline vs automated validation
- **SUS Testing:** User satisfaction scoring (min 5 respondents)

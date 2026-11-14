# EarthTrend — Earth Intelligence & Environmental Analytics

**NASA Space Apps Challenge 2026 Submission**

EarthTrend transforms NASA Earth observations into scientifically verified, statistical environmental trend analysis. Powered by **28,080 verified historical climate observations** (2000–2025) across Egypt and live NASA POWER API integration globally.

---

## 🌍 The 5 Core Scientific Questions

EarthTrend directly answers:

1. **WHAT is changing?**
   - Air Temperature (`T2M`, °C), Precipitation (`PRECTOTCORR`, mm/day), and All-Sky Surface Solar Radiation (`ALLSKY_SFC_SW_DWN`, MJ/m²/day).
2. **WHERE is the change happening?**
   - Any coordinate globally via NASA POWER point temporal APIs, with high-density coverage across 30 verified stations in Egypt (Cairo, Alexandria, Nile Delta, Suez Canal, Middle Egypt).
3. **HOW MUCH is it changing?**
   - Quantitative annual and decadal rates of change computed using **Ordinary Least Squares (OLS)** linear regression and robust **Theil-Sen** median estimators.
4. **HOW does it change over time?**
   - Decomposes 26 years of monthly records (2000–2025), removing 12-month cyclical seasonality to evaluate baseline anomaly trajectories.
5. **IS the trend statistically significant?**
   - Two-sided p-values and non-parametric **Mann-Kendall** monotonic trend tests evaluated at $\alpha = 0.05$ with exact 95% confidence bands.

---

## 📊 Scientific Datasets

1. **Verified Regional Climate Dataset (2000–2025)**:
   - `climate_power_monthly_2000-2025.csv` (28,080 rows of monthly NASA POWER observations with observed values and baseline anomalies).
   - `climate_power_monthly_2000-2025.xlsx` (multi-sheet deliverable workbook with data, units, and summary statistics).
   - 30 geographical grid points covering Cairo, Alexandria, Nile Delta, Damietta, Suez Canal, Beni Suef, and Fayoum.
2. **Live NASA POWER API**:
   - Upstream temporal point queries derived from the **MERRA-2** atmospheric reanalysis and **CERES** satellite solar products.
3. **Geospatial Context**:
   - **NASADEM** elevation model (SRTM reprocessing) and **ESA WorldCover** 2021 10m land-cover classification serve as static reference context.

---

## 🚀 Quick Start & How to Run

### Prerequisites
- Python 3.12+ (or 3.10+)
- Web browser (Chrome, Edge, Firefox)

### 1. Install Dependencies
```bash
cd backend
py -m pip install -r requirements.txt
```

### 2. Start EarthTrend Full-Stack Application
From the repository root:
```bash
py run.py
```
Or directly with uvicorn:
```bash
cd backend
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Open the Application
- **Interactive Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive NASA API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Reference**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing & Validation

The backend test suite verifies statistical calculations, data parsing, cache expiry, exports, and API endpoints without requiring live internet access:

```bash
cd backend
py -m pytest
```

**Result:**
```
72 passed, 1 skipped, 1 warning in 2.09s
```

All algorithms (OLS slope, Mann-Kendall tie-corrected Z score, Theil-Sen estimator, seasonality decomposition, and PDF report generation) have been empirically validated.

---

## 🖥️ Application Features

- **Home**: Project mission overview, answering the 5 core NASA challenge questions, and quick presets (Cairo warming, Alexandria precipitation, Nile Delta solar radiation).
- **Earth Explorer**: Interactive Leaflet dark-matter map displaying 30 verified stations, custom coordinate pin selection, Nominatim geocoder search, date range picker, and statistical tuning controls.
- **Trend Analysis**:
  - Four scientific KPI cards: OLS Slope/Decade, Statistical Significance (p-value), Mann-Kendall Kendall's $\tau$, and Theil-Sen slope.
  - Objective narrative interpretation.
  - Interactive Chart.js visualization with observed points, fitted OLS regression line, and shaded 95% confidence bands.
  - Empirical data quality diagnostics (completeness %, gaps, lag-1 autocorrelation).
  - One-click exports in **CSV**, **JSON**, and **Official PDF Report**.
- **Compare Regions**: Descriptive side-by-side comparison of rates of change between two regions (e.g. Cairo vs. Alexandria).
- **Data Explorer**: Searchable table of all 30 stations with direct download links for the CSV and Excel datasets.
- **About**: Mathematical formulations, data provenance, and scientific ethics statement.

---

## 🛡️ Scientific Ethics & Integrity

EarthTrend adheres to strict scientific standards:
- **Zero Fabrication**: Observations, trend slopes, and statistical p-values are never synthesized or faked.
- **Transparent Reporting**: Inconclusive or non-significant statistical results ($p \ge 0.05$) are honestly reported as insufficient evidence, never misconstrued as "proof of no climate change".
- **Attribution**: All measurements are attributed to NASA Langley Research Center and their underlying instruments.

---

## 📜 License & Citation

Developed for the **NASA Space Apps Challenge 2026**.
License: MIT.
Dataset source: NASA Prediction Of Worldwide Energy Resources (POWER) Project.

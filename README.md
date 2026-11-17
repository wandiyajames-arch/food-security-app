# NaijaFoodWatch

**Food security early warning for Nigeria: machine learning forecasts of IPC phases for 36 states and the Federal Capital Territory, three and six months ahead.**

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://naija-foodwatch-001.streamlit.app/)

**Live app:** https://naija-foodwatch-001.streamlit.app/

> **Built for early warning.** NaijaFoodWatch is developed at the African Institute for Mathematical Sciences (AIMS) Senegal to give food security teams a tested, transparent outlook between Cadre Harmonisé rounds: every forecast comes with its drivers in plain language and a published track record on held-out years. It is designed to work alongside the official Cadre Harmonisé classifications, flagging where analysts should look closer.

---

## Overview

Nigeria's food security situation is classified by the Cadre Harmonisé roughly twice a year, but conditions on the ground can change within weeks. NaijaFoodWatch forecasts each state's Integrated Food Security Phase Classification (IPC) between assessment rounds, using past phases, conflict, rainfall and vegetation data, and explains what drives each forecast.

The app provides:

- **State forecasts:** projected IPC phase, expected phase, probability of Crisis (Phase 3+) and Emergency (Phase 4+), trajectory, and the main drivers in plain language.
- **Forecasts by year:** pick any year from 2017 to 2028 and a month to see that month's forecasts on the map, compared with the actual Cadre Harmonisé phase. Past years use out-of-sample forecasts only; future years show when their forecasts will become available.
- **An interactive map of Nigeria:** every state coloured by its forecast phase, with names, hover details and the selected state highlighted.
- **A national overview:** states ranked by expected phase, with summary counts.
- **Model performance:** results on held-out years, naive benchmarks, domain attribution and spatial validation.
- **Method notes:** how the forecasts are produced, and their limitations.

---

## How the forecasts are made

| Step | Detail |
|---|---|
| **Data** | Monthly panel, 2015–2025, 37 units × 132 months (4,884 state-months) |
| **Predictors** | Past Cadre Harmonisé phases, ACLED conflict events, CHIRPS rainfall, MODIS NDVI (WFP prices were tested but not retained) |
| **Target** | Cadre Harmonisé phase (1,889 assessed state-months) |
| **Features** | 151 candidates, reduced to 17 (3-month) and 10 (6-month) using training data only |
| **Base learners** | Logistic Regression, Random Forest, XGBoost, LSTM |
| **Final model** | **Averaged ensemble (soft voting).** The four models' phase probabilities are averaged and converted to an expected phase. The combination rule was chosen on 2015–2022 data only. |
| **Explanations** | SHAP values from the XGBoost member |
| **Validation** | Train 2015–2022, test 2023–2025, with an embargo gap that keeps the training labels apart from the test period. Also a spatial holdout by geopolitical zone, a real-time check using only published phases, and naive benchmarks |

### Performance on the 2023–2025 test period

Quadratic weighted kappa (κ), with 95% bootstrap intervals for the ensemble (whole state-years resampled, because months of one state are not independent):

| Forecast | 3 months | 6 months |
|---|---|---|
| **Ensemble (averaged)** | **0.830** [0.745, 0.891] | **0.652** [0.524, 0.748] |
| Logistic Regression | 0.780 | 0.502 |
| XGBoost | 0.736 | 0.657 |
| Random Forest | 0.687 | 0.556 |
| LSTM | 0.668 | 0.519 |
| *Persistence ("same phase as now")* | *0.835* | *0.733* |

At three months the ensemble ties persistence; at six months persistence scores higher on all rows, but the gap (−0.081, interval −0.189 to 0.022) is not significant. Persistence is hard to beat because phases changed in only 8% (3-month) and 13% (6-month) of test cases. On the cases where the phase **did** change, which are what early warning exists to catch, the ensemble's κ is two to four times that of persistence (0.19 and 0.29, against 0.09 and 0.08), and six months ahead it flagged 11 of 32 new crises, with 60 false alarms. Using only Cadre Harmonisé results already published at the forecast date, the gap to persistence does not widen.

Past phases carry most of the signal and conflict comes second, but adding conflict to past phases alone does not raise overall agreement; its possible value is on the months that change.

A spatial holdout shows that skill transfers to northern zones left out of training (κ 0.65–0.76 at 3 months). Southern zones score low (κ 0.16–0.35) mainly because their records are short and almost always Phase 2, so κ cannot show skill; their accuracy is as good as in training. The real limit is severity never seen in training: without the North-East, which holds 56 of the 60 Emergency months, the model has almost no Emergency examples. The same pattern holds with the full ensemble and with a leave-one-state-out design.

---

## Architecture

All model output is **precomputed**. The app only reads prepared tables and renders them; it never loads a model or runs inference at runtime.

This is deliberate. Streamlit Community Cloud provides about 1 GB of memory, and loading PyTorch alone would exhaust it. Precomputing means:

- the app depends only on `streamlit`, `pandas`, `numpy` and `plotly`
- it starts in seconds
- a library version mismatch cannot break a saved model
- the repository stays small

```
Training pipeline (Google Colab)          This repository (Streamlit Cloud)
──────────────────────────────           ─────────────────────────────────
data → features → 4 models → ensemble ─► data/*.csv  ─►  app.py  ─►  browser
                       export_for_app_v7.py
```

---

## Repository structure

```
foodsec-streamlit/
├── app.py                      # Streamlit application
├── requirements.txt            # streamlit, pandas, numpy, plotly
├── make_nigeria_map.py         # one-off: builds the state map file from GADM boundaries
├── README.md
└── data/
    ├── forecasts.csv           # latest state forecasts, both horizons (averaged ensemble)
    ├── monthly_forecasts.csv   # month-by-month out-of-sample and live forecasts, with the actual CH phase
    ├── drivers.csv             # top SHAP drivers per state
    ├── history.csv             # Cadre Harmonisé assessment history
    ├── model_performance.csv   # κ with 95% CIs and κ on changed cases
    ├── benchmarks.csv          # models vs persistence and climatology
    ├── domains_h3.csv / domains_h6.csv     # SHAP share by data domain
    ├── ablation.csv            # κ lost when each domain is removed
    ├── spatial_validation.csv / matched_baseline.csv
    ├── bootstrap.csv / calibration.csv
    ├── nigeria_states.geojson  # simplified state boundaries for the map
    └── meta.json               # build date and panel summary
```

---

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

---

## Updating the forecasts

The data in `data/` is a snapshot. To refresh it:

1. Update the raw data (Cadre Harmonisé, ACLED, CHIRPS, MODIS) in the training pipeline (`foodsec_v7`).
2. Run the notebook `Thesis_FoodSecurity_Nigeria_v7.ipynb` (Run all).
3. From the project folder, run `python export_for_app_v7.py`. It writes `app_data/`.
4. Copy the contents of `app_data/` into this repository's `data/` folder (keep `nigeria_states.geojson`).
5. If the state boundaries have changed, re-run `python make_nigeria_map.py` (this needs `geopandas` locally; do not add it to `requirements.txt`).
6. Commit and push. Streamlit Cloud redeploys automatically.

---

## Limitations

- **Infrequent assessments.** The Cadre Harmonisé assesses about twice a year. Monthly targets are derived by expanding each assessment across its reference period, so most months repeat the previous phase.
- **Few phase changes.** Skill on transitions rests on 69 (3-month) and 104 (6-month) test cases, so those figures carry wide uncertainty.
- **Uneven coverage.** Southern zones have far fewer assessed state-months than northern zones, so skill there cannot yet be judged by κ.
- **Sparse market data.** Price data cover only 28–30% of state-months, and no price variable was retained in the final models.
- **Short horizon.** Forecasts reach 3 or 6 months beyond the latest data. Years further ahead are listed in the app but stay empty until the data for them exists.
- **Rare emergencies.** Phase 4 is rare in the record, and no claim is made about Emergency-phase detection.
- **Publication lag.** Cadre Harmonisé results are published after the period begins. A real-time check that uses only published results shows the ensemble's standing against persistence does not get worse.

---

## Data sources

| Domain | Source |
|---|---|
| Food security phase | Cadre Harmonisé, via the Humanitarian Data Exchange (HDX) |
| Rainfall | CHIRPS (Climate Hazards Group) |
| Vegetation | MODIS NDVI (NASA) |
| Conflict | ACLED (Armed Conflict Location & Event Data), via HDX |
| Market prices | WFP Vulnerability Analysis and Mapping |
| Boundaries | GADM v4.1 |

---

## Design note

Phase colours follow the international IPC scale: pale green (Minimal), yellow (Stressed), orange (Crisis), red (Emergency) and dark red (Catastrophe). No other colour in the interface carries meaning, so the phase colour alone signals severity.

---

## Author

**Wandiya James**: MSc Big Data & Data Science, African Institute for Mathematical Sciences (AIMS) Senegal.
Supervised by **Prof. Blamah N. Vachaku**, Department of Computer Science, University of Jos.
In collaboration with **Oyeleke Olayemi Seun**, DataLab Technology Limited, Abuja.

Contact: wandiya.james@aims-senegal.org

### Citation

If you use this work, please cite:

> Wandiya, J., Vachaku, B. N., & Oyeleke, O. S. (2026). *Bounded spatial generalisation in subnational food insecurity forecasting: A spatial holdout analysis for Nigeria.* 19th UNILAG Annual Research Conference and Fair, University of Lagos.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "No forecast data found" | The `data/` folder is missing or empty. Copy in the files from the export bundle. |
| Map shows a yellow warning | `data/nigeria_states.geojson` is missing. Run `python make_nigeria_map.py`. |
| App exceeds resource limits | Something heavy was added to `requirements.txt`. Remove `torch`, `xgboost`, `scikit-learn`, `shap` and `geopandas`; the app does not need them. |
| Repository too large | Model files were committed. Only the contents of `data/` are needed. |

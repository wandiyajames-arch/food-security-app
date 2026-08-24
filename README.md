# Nigeria Food Security Early Warning — App

A Streamlit application presenting forecasts of Integrated Food Security
Phase Classification outcomes across Nigeria's 36 states and the Federal
Capital Territory, at three- and six-month horizons.

**Wandiya James** · MSc Thesis · African Institute for Mathematical
Sciences (AIMS) Senegal · Supervised by Prof. Blamah N. Vachaku

---

## How this app is built

All model output is **precomputed**. The app reads prepared tables and
renders them. It never loads a model or runs inference.

This is deliberate. Streamlit Community Cloud provides roughly 1 GB of
memory. Loading PyTorch alone would exhaust it, and running SHAP on every
page view would be slow. Precomputing means:

- the app needs only `pandas` and `plotly`
- it starts in seconds
- a library version mismatch cannot break a saved model
- the whole deployment is under 1 MB

---

## Deploying to Streamlit Community Cloud

### Step 1 — Generate the data bundle

In your analysis environment, with the pipeline already run:

```bash
python export_for_app.py
```

This produces `app_bundle/data/` containing forecasts, precomputed SHAP
drivers, assessment history and the result tables. Expect around 5 MB.

### Step 2 — Assemble the repository

```
foodsec-app/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── data/
    ├── forecasts.csv
    ├── drivers.csv
    ├── history.csv
    ├── model_performance.csv
    ├── domains_h3.csv
    ├── domains_h6.csv
    ├── spatial_validation.csv
    └── meta.json
```

Copy the contents of `app_bundle/data/` into `data/`.

### Step 3 — Push to GitHub

The repository must be **public** for the free tier.

```bash
git init
git add .
git commit -m "Nigeria food security early warning app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/foodsec-app.git
git push -u origin main
```

### Step 4 — Deploy

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. **New app** → select your repository
4. Main file path: `app.py`
5. **Deploy**

First build takes two to three minutes. Your URL will be
`https://YOUR-APP-NAME.streamlit.app`.

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

---

## What each tab shows

**State forecast** — Select a state and horizon. Shows the projected IPC
phase, probability of Crisis and Emergency, the five factors driving the
forecast in plain language, recommended response actions, and the
assessment history with the forecast marked.

**National picture** — All states ranked by expected phase, coloured on
the IPC scale, with summary counts.

**Model performance** — Weighted Kappa by model against the operational
threshold, SHAP attribution by data domain, and spatial holdout results
by region.

**Method** — How the forecast is produced, the models used, the
validation designs, and the known limitations.

---

## Design note

The IPC five-phase colour scale is the international standard in
humanitarian food security work: pale green through yellow, orange, red
and dark red. It is used here exactly as specified, and **no other colour
in this interface carries meaning**. Everything else is neutral, so that
phase colour alone signals severity.

---

## Updating the forecasts

The bundle is a snapshot. To refresh:

1. Download new CHIRPS, UCDP and WFP data
2. Re-run preprocessing and feature engineering
3. Run `export_for_app.py`
4. Replace the contents of `data/`
5. Commit and push — Streamlit Cloud redeploys automatically

---

## Limitations stated in the app

- Market price coverage reaches 28 to 30 percent of state-months, and is
  sparsest in conflict-affected areas where markets have closed.
- Cadre Harmonisé assesses approximately twice per year; monthly target
  values are derived by expanding each assessment across its reference
  period.
- Phase 4 is represented by 60 observations in the full panel. No claim
  regarding Emergency-phase detection performance is made.
- Operational forecasts use XGBoost rather than the full stacked
  ensemble, because the meta-learner consumes base-model probabilities
  rather than raw features.

---

## Troubleshooting

**"No forecast data found"** — the `data/` folder is missing or empty.
Run `export_for_app.py` and copy the output across.

**App exceeds resource limits** — something heavy was added to
`requirements.txt`. Remove `torch`, `xgboost`, `scikit-learn` and `shap`;
the app does not need them.

**Repository too large for GitHub** — model pickles were committed. They
are not needed. The Random Forest files alone exceed 20 MB each; keep
only the contents of `data/`.

**Charts do not render** — check that `plotly` is in `requirements.txt`.
# food-security-app

"""
NIGERIA FOOD SECURITY EARLY WARNING
====================================
Streamlit application presenting forecasts of Integrated Food Security
Phase Classification outcomes across Nigeria's 36 states and the Federal
Capital Territory.

All model output is precomputed. This application reads prepared tables
and renders them; it does not load a model or run inference. That keeps
memory use low enough for Streamlit Community Cloud and removes any
dependency on library versions matching those used in training.

Design note: the IPC five-phase colour scale is the international standard
in humanitarian food security work. It is used here exactly as specified,
and no other colour in this interface carries meaning. Everything else is
neutral so that phase colour alone signals severity.

Run locally:   streamlit run app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nigeria Food Security Early Warning",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# IPC Integrated Food Security Phase Classification — official scale
IPC = {
    1: {"name": "Minimal", "fill": "#CDFACD", "ink": "#1a3d1a",
        "meaning": "Households can meet essential food needs without atypical coping."},
    2: {"name": "Stressed", "fill": "#FAE61E", "ink": "#3d3600",
        "meaning": "Minimally adequate consumption, but unable to afford some essential non-food expenditure."},
    3: {"name": "Crisis", "fill": "#E67800", "ink": "#ffffff",
        "meaning": "Food consumption gaps with high acute malnutrition, or assets depleted to meet needs."},
    4: {"name": "Emergency", "fill": "#C80000", "ink": "#ffffff",
        "meaning": "Large consumption gaps, very high acute malnutrition and excess mortality."},
    5: {"name": "Catastrophe", "fill": "#640000", "ink": "#ffffff",
        "meaning": "Starvation, death and destitution evident even with full humanitarian assistance."},
}

RESPONSE = {
    1: ["Continue routine surveillance",
        "Maintain baseline market monitoring"],
    2: ["Increase market monitoring frequency",
        "Review contingency stock positioning"],
    3: ["Activate contingency food assistance planning",
        "Deploy rapid needs assessment teams",
        "Alert implementing partners in affected LGAs",
        "Pre-position emergency stocks within the state"],
    4: ["Deploy emergency food assistance immediately",
        "Scale up nutrition screening for children under five",
        "Activate emergency cash transfer programmes",
        "Coordinate logistics surge with NEMA",
        "Establish supplementary feeding sites"],
    5: ["Declare emergency response",
        "Mobilise full humanitarian operation",
        "Establish therapeutic feeding centres",
        "Request international assistance"],
}

INK = "#2b3440"
MUTED = "#6b7280"
RULE = "#e6e9ed"

# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  .block-container {{ padding-top: 2.2rem; max-width: 1400px; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  #MainMenu, footer {{ visibility: hidden; }}
  [data-testid="stAppDeployButton"] {{ display: none; }}
  .stAppDeployButton {{ display: none; }}

  /* The signature element: a phase classification the eye cannot miss */
  .plate {{
      border-radius: 3px;
      padding: 1.7rem 1.9rem 1.5rem 1.9rem;
      margin: 0.2rem 0 1.1rem 0;
      line-height: 1.15;
  }}
  .plate .num {{
      font-size: 3.6rem; font-weight: 300;
      letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
  }}
  .plate .nm {{
      font-size: 1.55rem; font-weight: 600;
      letter-spacing: 0.01em; margin-left: 0.7rem;
  }}
  .plate .why {{
      font-size: 0.86rem; opacity: 0.86;
      margin-top: 0.7rem; max-width: 56ch;
  }}

  .eyebrow {{
      font-size: 0.7rem; letter-spacing: 0.14em;
      text-transform: uppercase; color: {MUTED};
      font-weight: 600; margin-bottom: 0.25rem;
  }}

  .stat {{
      border-left: 2px solid #d4d8de;
      padding: 0.15rem 0 0.15rem 0.85rem;
      margin-bottom: 0.9rem;
  }}
  .stat .v {{
      font-size: 1.7rem; font-weight: 600;
      font-variant-numeric: tabular-nums; line-height: 1.1;
  }}
  .stat .l {{ font-size: 0.76rem; color: {MUTED}; letter-spacing: 0.02em; }}

  .driver {{
      display: flex; align-items: baseline; gap: 0.8rem;
      padding: 0.6rem 0; border-bottom: 1px solid {RULE};
  }}
  .driver .rank {{
      font-size: 0.72rem; color: #9aa1ab;
      font-variant-numeric: tabular-nums; min-width: 1.1rem;
  }}
  .driver .what {{ flex: 1; font-size: 0.95rem; }}
  .driver .share {{
      font-size: 0.88rem; font-variant-numeric: tabular-nums;
      color: #4b5563; font-weight: 600;
  }}

  .caveat {{
      font-size: 0.78rem; color: {MUTED};
      border-top: 1px solid {RULE};
      padding-top: 0.9rem; margin-top: 1.6rem; line-height: 1.55;
  }}

  div[data-testid="stMetricValue"] {{ font-variant-numeric: tabular-nums; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load(name: str):
    fp = DATA / name
    if not fp.exists():
        return None
    if fp.suffix == ".json":
        return json.loads(fp.read_text())
    return pd.read_csv(fp)


def plate(phase, expected=None):
    c = IPC.get(int(phase), IPC[1])
    exp = (f'<span style="font-size:0.95rem;opacity:0.75;margin-left:0.8rem">'
           f'expected {expected:.2f}</span>') if expected is not None else ""
    st.markdown(
        f'<div class="plate" style="background:{c["fill"]};color:{c["ink"]}">'
        f'<span class="num">{int(phase)}</span>'
        f'<span class="nm">{c["name"]}</span>{exp}'
        f'<div class="why">{c["meaning"]}</div></div>',
        unsafe_allow_html=True)


def stat(value, label):
    st.markdown(f'<div class="stat"><div class="v">{value}</div>'
                f'<div class="l">{label}</div></div>', unsafe_allow_html=True)


def eyebrow(text):
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)


COLUMN_LABELS = {
    "horizon": "Horizon", "model": "Model", "state": "State",
    "region": "Region", "weighted_kappa": "Weighted Kappa",
    "macro_f1": "Macro F1", "accuracy": "Accuracy",
    "auroc_crisis": "AUROC (crisis)", "brier_crisis": "Brier (crisis)",
    "rmse": "RMSE", "mae": "MAE",
    "current_phase": "Current phase", "forecast_phase": "Forecast phase",
    "expected_phase": "Expected phase", "prob_crisis": "P(Crisis)",
    "prob_emergency": "P(Emergency)", "direction": "Trajectory",
    "confidence": "Confidence", "held_out_region": "Held-out region",
    "ci_lower_95": "95% CI lower", "ci_upper_95": "95% CI upper",
    "kappa_on_changed_rows": "Kappa where phase changed",
}


def pretty(df: pd.DataFrame) -> pd.DataFrame:
    """Rename pipeline field names to readable column headers."""
    out = df.rename(columns=COLUMN_LABELS).copy()
    if "Region" in out.columns:
        out["Region"] = out["Region"].astype(str).str.replace("_", " ").str.title()
    if "Trajectory" in out.columns:
        out["Trajectory"] = out["Trajectory"].astype(str).str.capitalize()
    return out


# ─────────────────────────────────────────────────────────────────────────────
fc_all = load("forecasts.csv")
dr_all = load("drivers.csv")
hist = load("history.csv")
meta = load("meta.json") or {}

if fc_all is None:
    st.title("Nigeria Food Security Early Warning")
    st.error(
        "No forecast data found.\n\n"
        "Run `export_for_app.py` in the analysis environment and place the "
        "resulting `data/` folder alongside `app.py`."
    )
    st.stop()

# ── Header ───────────────────────────────────────────────────────────────────
hl, hr = st.columns([3, 1])
with hl:
    eyebrow("Integrated Food Security Phase Classification · Forecast")
    st.markdown("# Nigeria Food Security Early Warning")
    st.caption("Multi-source machine learning forecasts at state level · "
               "36 states and the Federal Capital Territory")
with hr:
    st.write("")
    perf = load("model_performance.csv")
    if perf is not None and not perf.empty:
        best = perf.loc[perf.weighted_kappa.idxmax()]
        stat(f"{best.weighted_kappa:.3f}", "Weighted Kappa · best model")

st.write("")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    eyebrow("Query")
    horizon = st.radio("Forecast horizon", sorted(fc_all.horizon.unique()),
                       format_func=lambda h: f"{int(h)} months ahead",
                       horizontal=True)

    fc = fc_all[fc_all.horizon == horizon].copy()

    regions = ["All regions"] + sorted(
        r for r in fc.region.dropna().unique() if str(r).strip())
    region = st.selectbox("Region", regions,
                          format_func=lambda r: str(r).replace("_", " ").title()
                          if r != "All regions" else r)

    pool = fc if region == "All regions" else fc[fc.region == region]
    state = st.selectbox("State", sorted(pool.state.unique()))

    st.divider()
    eyebrow("IPC scale")
    for ph in range(1, 6):
        c = IPC[ph]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:9px;margin:5px 0">'
            f'<div style="width:15px;height:15px;background:{c["fill"]};'
            f'border:1px solid #b9bfc7;border-radius:2px"></div>'
            f'<span style="font-size:0.83rem">{ph} &nbsp;{c["name"]}</span></div>',
            unsafe_allow_html=True)

    st.divider()
    if meta:
        st.caption(
            f"Panel: {meta.get('panel_rows', 0):,} state-months · "
            f"{meta.get('states', 0)} units · "
            f"{meta.get('period_start', '')} to {meta.get('period_end', '')}"
        )
    st.caption("Decision-support information. Interpret alongside field "
               "assessments and expert judgement.")

# ── Tabs ─────────────────────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs(["State forecast", "National picture",
                          "Model performance", "Method"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — STATE FORECAST
# ═════════════════════════════════════════════════════════════════════════════
with t1:
    row = fc[fc.state == state]
    row = row.iloc[0] if not row.empty else None

    left, right = st.columns([1.35, 1])

    with left:
        if row is not None:
            eyebrow(f"{state} · projected for {row.forecast_for}")
            plate(int(row.forecast_phase), float(row.expected_phase))

            a, b, c = st.columns(3)
            with a:
                stat(f"{row.prob_crisis:.0%}", "Crisis or worse")
            with b:
                stat(f"{row.prob_emergency:.0%}", "Emergency or worse")
            with c:
                d = str(row.get("direction", "")).strip()
                if d and d != "unknown":
                    stat(d.capitalize(), "Trajectory")
                else:
                    stat(f"{row.confidence:.0%}", "Model confidence")
        else:
            st.info(f"No forecast available for {state}.")

    with right:
        eyebrow("What is driving this")

        drv = pd.DataFrame()
        if dr_all is not None:
            drv = dr_all[(dr_all.state == state) &
                         (dr_all.horizon == horizon)].sort_values("rank")

        if not drv.empty:
            for _, d in drv.iterrows():
                colour = IPC[4]["fill"] if d.direction == "raises" else "#5b7c99"
                st.markdown(
                    f'<div class="driver">'
                    f'<span class="rank">{int(d["rank"])}</span>'
                    f'<span class="what">{str(d.label).capitalize()}'
                    f'<span style="color:{colour};font-size:0.8rem;'
                    f'margin-left:0.5rem">{d.direction} risk</span></span>'
                    f'<span class="share">{d.share:.0%}</span></div>',
                    unsafe_allow_html=True)
        else:
            st.caption("Driver attribution not available for this state.")

        if row is not None:
            st.write("")
            eyebrow("Recommended response")
            for action in RESPONSE.get(int(row.forecast_phase), []):
                st.markdown(f"— {action}")

    # ── Assessment history ──
    st.write("")
    if hist is not None:
        h = hist[hist.state == state].copy()
        if not h.empty:
            h["date"] = pd.to_datetime(h["date"])
            h = h.sort_values("date")

            eyebrow("Assessment history")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=h["date"], y=h["ipc_phase"], mode="lines",
                line=dict(color=INK, width=2, shape="hv"),
                name="Assessed phase",
                hovertemplate="%{x|%b %Y}<br>Phase %{y}<extra></extra>"))

            if row is not None:
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(row.forecast_for)],
                    y=[row.expected_phase], mode="markers",
                    marker=dict(size=13,
                                color=IPC[int(row.forecast_phase)]["fill"],
                                line=dict(color=INK, width=1.5)),
                    name="Forecast",
                    hovertemplate="%{x|%b %Y}<br>Forecast %{y:.2f}<extra></extra>"))

            fig.add_hrect(y0=2.5, y1=5.5, fillcolor="#C80000",
                          opacity=0.05, line_width=0)
            fig.add_hline(y=3, line_dash="dot", line_color="#C80000",
                          annotation_text="Crisis threshold",
                          annotation_position="top left",
                          annotation_font_size=11)
            fig.update_layout(
                height=290, margin=dict(t=10, b=10, l=0, r=0),
                yaxis=dict(title="IPC phase", range=[0.6, 5.4],
                           tickvals=[1, 2, 3, 4, 5], gridcolor="#f0f2f5"),
                xaxis=dict(title="", gridcolor="#f0f2f5"),
                plot_bgcolor="white", paper_bgcolor="white",
                hovermode="x unified", showlegend=True,
                legend=dict(orientation="h", y=1.12, x=0))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        '<div class="caveat">Forecasts are generated by a model trained on '
        'climate, vegetation, conflict and market data for 2015 to 2022 and '
        'validated on 2023 to 2025. They are decision-support information and '
        'do not replace Cadre Harmonisé assessment or field verification.</div>',
        unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — NATIONAL PICTURE
# ═════════════════════════════════════════════════════════════════════════════
with t2:
    eyebrow(f"Projected for {fc.forecast_for.mode().iloc[0]} · "
            f"{int(horizon)}-month horizon")

    n3 = int((fc.forecast_phase >= 3).sum())
    n4 = int((fc.forecast_phase >= 4).sum())
    det = int((fc.direction == "deteriorating").sum()) \
        if "direction" in fc.columns else 0

    a, b, c, d = st.columns(4)
    with a:
        stat(str(n3), "States in Crisis or worse")
    with b:
        stat(str(n4), "States in Emergency or worse")
    with c:
        stat(f"{fc.expected_phase.mean():.2f}", "Mean expected phase")
    with d:
        stat(str(det), "States deteriorating")

    st.write("")

    ranked = fc.sort_values("expected_phase").tail(25)
    fig = go.Figure(go.Bar(
        x=ranked.expected_phase, y=ranked.state, orientation="h",
        marker=dict(
            color=[IPC[int(round(v))]["fill"] for v in ranked.expected_phase],
            line=dict(color="#c3c9d1", width=0.8)),
        customdata=np.stack([ranked.prob_crisis, ranked.prob_emergency], axis=-1),
        hovertemplate=("<b>%{y}</b><br>Expected phase %{x:.2f}<br>"
                       "Crisis %{customdata[0]:.0%} · "
                       "Emergency %{customdata[1]:.0%}<extra></extra>")))
    fig.add_vline(x=3, line_dash="dot", line_color="#C80000",
                  annotation_text="Crisis", annotation_position="top")
    fig.update_layout(
        height=max(420, 26 * len(ranked)),
        margin=dict(t=30, b=10, l=0, r=20),
        xaxis=dict(title="Expected IPC phase", range=[0.8, 5.2],
                   gridcolor="#f0f2f5"),
        yaxis=dict(title=""),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Full forecast table"):
        cols = [c for c in ["state", "region", "current_phase",
                            "forecast_phase", "expected_phase",
                            "prob_crisis", "prob_emergency", "direction"]
                if c in fc.columns]
        st.dataframe(pretty(fc[cols].sort_values("expected_phase",
                                                  ascending=False)),
                     use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — MODEL PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
with t3:
    perf = load("model_performance.csv")

    if perf is None or perf.empty:
        st.info("No performance results available.")
    else:
        eyebrow("Out-of-sample holdout · 2023–2025")
        sub = perf[perf.horizon == horizon].sort_values("weighted_kappa")

        fig = go.Figure(go.Bar(
            x=sub.weighted_kappa, y=sub.model, orientation="h",
            marker=dict(color=[INK if "nsemble" in str(m) else "#a8b2bf"
                               for m in sub.model],
                        line=dict(color="#8a929c", width=0.6)),
            text=[f"{v:.3f}" for v in sub.weighted_kappa],
            textposition="outside", textfont=dict(size=12)))
        fig.add_vline(x=0.75, line_dash="dot", line_color="#C80000",
                      annotation_text="Operational threshold",
                      annotation_position="top")
        fig.update_layout(
            height=330, margin=dict(t=34, b=10, l=0, r=70),
            xaxis=dict(title="Quadratic weighted Kappa", range=[0, 1.0],
                       gridcolor="#f0f2f5"),
            yaxis=dict(title=""),
            plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            pretty(perf[perf.horizon == horizon].sort_values(
                "weighted_kappa", ascending=False)),
            use_container_width=True, hide_index=True)

    # ── Domain contribution ──
    dom = load(f"domains_h{int(horizon)}.csv")
    if dom is not None and not dom.empty:
        st.write("")
        eyebrow("What the model relies on")
        st.caption("Share of SHAP attribution by data domain.")
        label_col, val_col = dom.columns[0], dom.columns[-1]
        dom = dom.sort_values(val_col)
        fig = go.Figure(go.Bar(
            x=dom[val_col], y=dom[label_col], orientation="h",
            marker=dict(color="#5b7c99",
                        line=dict(color="#44607a", width=0.6)),
            text=[f"{v:.1f}%" for v in dom[val_col]],
            textposition="outside"))
        fig.update_layout(
            height=290, margin=dict(t=10, b=10, l=0, r=55),
            xaxis=dict(title="Share of importance (%)", gridcolor="#f0f2f5"),
            yaxis=dict(title=""),
            plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Spatial validation ──
    spa = load("spatial_validation.csv")
    if spa is not None and not spa.empty and "held_out_region" in spa.columns:
        st.write("")
        eyebrow("Generalisation to regions excluded from training")
        s = spa[(spa.horizon == horizon) &
                (spa.configuration == "with spatial features")] \
            if "configuration" in spa.columns else spa[spa.horizon == horizon]
        s = s.sort_values("weighted_kappa")
        if not s.empty:
            fig = go.Figure(go.Bar(
                x=s.weighted_kappa,
                y=[r.replace("_", " ").title() for r in s.held_out_region],
                orientation="h",
                marker=dict(color="#5b7c99",
                            line=dict(color="#44607a", width=0.6)),
                text=[f"{v:.3f}" for v in s.weighted_kappa],
                textposition="outside"))
            fig.add_vline(x=0.75, line_dash="dot", line_color="#C80000")
            fig.update_layout(
                height=300, margin=dict(t=14, b=10, l=0, r=60),
                xaxis=dict(title="Weighted Kappa", range=[-0.1, 1.0],
                           gridcolor="#f0f2f5"),
                yaxis=dict(title=""),
                plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Each bar is a model trained on all administrative units "
                "outside the stated region and evaluated on units within it. "
                "Performance tracks the number of assessed observations "
                "available in each region."
            )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — METHOD
# ═════════════════════════════════════════════════════════════════════════════
with t4:
    a, b = st.columns([1.15, 1])

    with a:
        eyebrow("How the forecast is produced")
        st.markdown("""
Five independent data domains are harmonised into a monthly, state-level
panel covering 2015 to 2025.

**Climate** — CHIRPS satellite rainfall and standardised precipitation
indices at one, three and six months, with ERA5-Land temperature.

**Vegetation** — MODIS normalised difference vegetation index anomalies
and vegetation condition indices.

**Conflict** — UCDP georeferenced events, weighted by type, with fatality
counts and rolling burden measures.

**Market** — WFP retail prices for sorghum, millet, maize, rice and
cowpea, with inflation and volatility features.

**Spatial and temporal** — lagged values, rolling statistics,
neighbouring-state conditions and seasonal position.

From 27 raw variables, 165 candidate features are engineered. Selection
is confined to the training partition, retaining 17 features at the
three-month horizon and 10 at six months, the six-month count chosen by
forward-chaining validation on 2015 to 2022 data.
        """)

    with b:
        eyebrow("Models")
        st.markdown("""
Four base learners are combined by averaging their predicted phase
probabilities (soft voting), giving an expected phase:

— Long Short-Term Memory network
— XGBoost
— Random Forest
— Multinomial logistic regression

Training uses 2015 to 2022. Evaluation uses a strict 2023 to 2025 holdout
the models never see during training.
        """)

        st.write("")
        eyebrow("Validation")
        st.markdown("""
— Temporal holdout on unseen years
— Region-level spatial holdout on unseen administrative units
— Domain ablation measuring each source's contribution
— Bootstrap confidence intervals on all metrics
— Calibration of predicted crisis probabilities
        """)

        st.write("")
        eyebrow("Known limitations")
        st.markdown("""
Market price coverage reaches 28 to 30 percent of state-months, and is
sparsest in conflict-affected areas where markets have closed.

Cadre Harmonisé assesses approximately twice yearly; monthly targets are
derived by expanding each assessment across its reference period.

Phase 4 is represented by 60 observations in the full panel. No claim
regarding Emergency-phase detection performance is made.

Forecasts use the averaged ensemble of all four models. Driver
explanations come from SHAP on its XGBoost member.

A naive "same phase as now" forecast scores higher overall (Kappa 0.835
at three months, 0.733 at six) because phases rarely change between
assessments. The models add skill mainly where the phase changes.
        """)

    st.markdown(
        '<div class="caveat">Nigeria Food Security Early Warning System · '
        'MSc research, African Institute for Mathematical Sciences (AIMS) '
        'Senegal · Data: Cadre Harmonisé, CHIRPS, MODIS, UCDP GED, WFP VAM, '
        'ERA5-Land</div>',
        unsafe_allow_html=True)

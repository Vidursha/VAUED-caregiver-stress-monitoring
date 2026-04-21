import html as html_module
import os
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_plotly_events import plotly_events
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots

API_BASE = os.environ.get("VAUED_API_BASE", "http://127.0.0.1:5000")

APR_THROUGH_DEC = list(range(4, 13))

st.set_page_config(
    page_title="Care-Sync AI | Stress Monitor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_MAP = {
    # Muted, healthcare-appropriate tones (lower contrast, still intuitive)
    "Low": "#2f8f6b",  # muted green
    "Medium": "#d2a33a",  # muted amber
    "High": "#cf5f5f",  # muted red
}

HEATMAP_COLORSCALE = [
    [0.0, "#2ca02c"],  # label 0 = Low (green)
    [0.5, "#ffcc00"],  # label 1 = Medium (yellow)
    [1.0, "#d62728"],  # label 2 = High (red)
]

KPI_STYLES = [
    # consistent green shades (light → dark gradient for hierarchy)
    ("#16a34a", "#f0fdf4", "Caregivers"),
    ("#15803d", "#ecfdf5", "Temperature"),
    ("#166534", "#f0fdf4", "Stress index"),
    ("#14532d", "#ecfdf5", "Heart rate"),
]

POPUP_CSS = """
<style>
div[data-testid="stDialog"] > div {
    border-radius: 16px !important;
    box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25) !important;
}
div[data-testid="stDialog"] div[data-testid="stMarkdownContainer"] p.popup-metric-card {
    margin: 0;
}
</style>
"""

DASHBOARD_CSS = """
<style>
:root{
    --bg0: #f7fbf9;
    --bg1: #ffffff;
    --ink: #0f172a;
    --muted: #475569;
    --muted2: #64748b;
    --card: #ffffff;
    --cardBorder: rgba(15, 23, 42, 0.08);
    --shadow: 0 12px 35px rgba(2, 6, 23, 0.07);
    --shadowSoft: 0 6px 18px rgba(2, 6, 23, 0.06);
    --brandA: #0f766e;   /* teal-green */
    --brandB: #16a34a;   /* green */
    --brandC: #047857;   /* emerald */
    --focus: rgba(16, 185, 129, 0.35);

    /* Button palette (match sidebar theme) */
    --btnA: #16a34a; /* green-600 */
    --btnB: #14b8a6; /* teal-500 */
    --btnHoverA: #15803d; /* green-700 */
    --btnHoverB: #0d9488; /* teal-600 */
}

.stApp, .stApp * { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
.stApp { color: var(--ink); }

.stApp {
    background:
        radial-gradient(1100px 520px at 10% 0%, rgba(16, 185, 129, 0.14), transparent 58%),
        radial-gradient(900px 520px at 90% 14%, rgba(20, 184, 166, 0.10), transparent 54%),
        linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 42%, var(--bg1) 100%);
}
.dash-wrap {
    background: linear-gradient(180deg, rgba(236, 253, 245, 0.92) 0%, rgba(255,255,255,0.92) 58%, #ffffff 100%);
    border-radius: 20px;
    padding: 20px 22px 8px;
    margin-bottom: 18px;
    border: 1px solid var(--cardBorder);
    box-shadow: var(--shadow);
}
.dash-title {
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, var(--brandA), var(--brandB), var(--brandC));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
/* Make Plotly charts blend in (Material-ish cards) */
div[data-testid="stPlotlyChart"] > div {
    border-radius: 16px;
    border: 1px solid rgba(15, 23, 42, 0.10);
    box-shadow: var(--shadowSoft);
    background: var(--card);
    transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
}
div[data-testid="stPlotlyChart"] > div:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 34px rgba(2, 6, 23, 0.10);
    border-color: rgba(16, 185, 129, 0.25);
}

/* KPI card hover */
.kpi-card {
    transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
}
.kpi-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 36px rgba(2, 6, 23, 0.10) !important;
    border-color: rgba(16, 185, 129, 0.28) !important;
}
div[data-testid="stTabs"] button { font-weight: 600 !important; }

/* Headings + captions */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
    letter-spacing: -0.01em;
}
div[data-testid="stCaptionContainer"] { color: var(--muted2); }

/* Controls (select/radio/text input) */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 12px !important;
    border-color: rgba(15, 23, 42, 0.14) !important;
    box-shadow: none !important;
    background: rgba(255,255,255,0.85) !important;
}
div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover,
div[data-baseweb="textarea"] > div:hover {
    border-color: rgba(16, 185, 129, 0.55) !important;
}
div[data-baseweb="select"] > div:has(input:focus),
div[data-baseweb="input"] > div:has(input:focus),
div[data-baseweb="textarea"] > div:has(textarea:focus) {
    border-color: rgba(16, 185, 129, 0.75) !important;
    box-shadow: 0 0 0 4px var(--focus) !important;
}

/* Buttons */
button[kind="primary"] {
    border-radius: 12px !important;
    background: linear-gradient(90deg, var(--btnA), var(--btnB)) !important;
    border: 1px solid rgba(15, 23, 42, 0.10) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(90deg, var(--btnHoverA), var(--btnHoverB)) !important;
    filter: saturate(1.05);
    box-shadow: 0 12px 26px rgba(2, 6, 23, 0.14) !important;
    transform: translateY(-1px);
}
button[kind="primary"]:active {
    transform: translateY(0px);
    box-shadow: 0 8px 18px rgba(2, 6, 23, 0.12) !important;
}
button[kind="secondary"] {
    border-radius: 12px !important;
    border: 1px solid rgba(20, 184, 166, 0.30) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(240, 253, 250, 0.72)) !important;
    color: #0f766e !important;
    font-weight: 750 !important;
    transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease !important;
}
button[kind="secondary"]:hover {
    border-color: rgba(13, 148, 136, 0.55) !important;
    box-shadow: 0 10px 22px rgba(2, 6, 23, 0.10) !important;
    transform: translateY(-1px);
}
button[kind="secondary"]:active {
    transform: translateY(0px);
    box-shadow: 0 7px 16px rgba(2, 6, 23, 0.09) !important;
}
</style>
"""
def _stress_trend_series(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    """Bucket sensor rows; trend uses % high-stress readings (label==2) and volume — no mean label."""
    d = df.dropna(subset=["datetime"]).copy()
    if d.empty:
        return pd.DataFrame()
    d["date_key"] = d["date_key"].astype(str)
    if granularity == "Month":
        d["_p"] = d["year_month"].astype(str)
    else:
        d["_p"] = d["date_key"]

    def _high_count(s: pd.Series) -> int:
        return int((s == 2).sum())

    g = d.groupby("_p", dropna=False)
    out = g.agg(readings=("label", "count"), high_stress=("label", _high_count)).reset_index()
    out["high_stress_pct"] = np.where(out["readings"] > 0, 100.0 * out["high_stress"] / out["readings"], 0.0)
    if granularity == "Month":
        out["_sort"] = pd.to_datetime(out["_p"] + "-01", errors="coerce")
    else:
        out["_sort"] = pd.to_datetime(out["_p"], errors="coerce")
    out = out.sort_values("_sort")
    return out.rename(columns={"_p": "period"})


def _month_stress_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly counts by Low/Medium/High stress (Apr–Dec slice expected)."""
    if df is None or df.empty:
        return pd.DataFrame()
    if "year_month" not in df.columns or "Stress_Category" not in df.columns:
        return pd.DataFrame()
    d = df.dropna(subset=["year_month", "Stress_Category"]).copy()
    if d.empty:
        return pd.DataFrame()
    out = (
        d.groupby(["year_month", "Stress_Category"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    out["year_month"] = out["year_month"].astype(str)
    out["Stress_Category"] = out["Stress_Category"].astype(str)
    out["_sort"] = pd.to_datetime(out["year_month"] + "-01", errors="coerce")
    return out.sort_values(["_sort", "Stress_Category"]).drop(columns=["_sort"])


def _stress_month_interpretation(high_pct: float) -> str:
    try:
        v = float(high_pct)
    except (TypeError, ValueError):
        return "Stress level unclear"
    if v >= 40:
        return "High-stress month"
    if v >= 20:
        return "Moderate-stress month"
    return "Lower-stress month"


def _trend_direction_label(month_trend: pd.DataFrame) -> tuple[str, float]:
    """Return (plain-language label, slope per month) for % high stress trend."""
    if month_trend is None or month_trend.empty or len(month_trend) < 2:
        return "No clear trend yet", 0.0
    d = month_trend.dropna(subset=["high_stress_pct", "_sort"]).copy()
    if len(d) < 2:
        return "No clear trend yet", 0.0
    x = np.arange(len(d), dtype=float)
    y = d["high_stress_pct"].astype(float).to_numpy()
    try:
        slope = float(np.polyfit(x, y, 1)[0])
    except Exception:
        slope = 0.0
    if abs(slope) < 0.5:
        return "Overall, stress looks fairly stable month-to-month", slope
    if slope > 0:
        return "Overall, high-stress readings are increasing over time", slope
    return "Overall, high-stress readings are decreasing over time", slope


def _daily_trend_label(day_trend: pd.DataFrame) -> tuple[str, float, float]:
    """Return (label, slope per day, volatility stddev) for daily % high stress in a month."""
    if day_trend is None or day_trend.empty or len(day_trend) < 2:
        return "Not enough daily data to describe a trend", 0.0, 0.0
    d = day_trend.dropna(subset=["high_stress_pct", "_sort"]).copy()
    if len(d) < 2:
        return "Not enough daily data to describe a trend", 0.0, 0.0
    x = np.arange(len(d), dtype=float)
    y = d["high_stress_pct"].astype(float).to_numpy()
    try:
        slope = float(np.polyfit(x, y, 1)[0])
    except Exception:
        slope = 0.0
    vol = float(np.nanstd(y)) if len(y) else 0.0
    if vol >= 18:
        return "Volatile month (stress swings day-to-day)", slope, vol
    if abs(slope) < 0.9:
        return "Stable month overall (small day-to-day change)", slope, vol
    if slope > 0:
        return "Rising stress across the month", slope, vol
    return "Easing stress across the month", slope, vol


def _correlation_matrix_fig(df: pd.DataFrame) -> go.Figure:
    cols = ["HR", "EDA", "TEMP", "MovementMagnitude"]
    sub = df[cols].dropna()
    if len(sub) < 3:
        fig = go.Figure()
        fig.add_annotation(text="Not enough rows", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    c = sub.corr().round(2)
    fig = go.Figure(
        data=go.Heatmap(
            z=c.values,
            x=c.columns.tolist(),
            y=c.columns.tolist(),
            text=c.values,
            texttemplate="%{text}",
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            colorbar=dict(title="r"),
        )
    )
    fig.update_layout(
        title="Correlation between body signals (Pearson r)",
        xaxis=dict(side="bottom"),
        yaxis=dict(autorange="reversed"),
        height=380,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#fafafa",
    )
    return fig


def _prepare_sensor_df(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], dayfirst=True, errors="coerce")
    if "id" in df.columns:
        df["id"] = df["id"].astype(str)
    if "label" in df.columns:
        df["label_num"] = pd.to_numeric(df["label"], errors="coerce")
        df["Stress_Category"] = df["label"].map({0: "Low", 1: "Medium", 2: "High"})
    if "datetime" in df.columns:
        df["year_month"] = df["datetime"].dt.strftime("%Y-%m")
        df["date_key"] = df["datetime"].dt.strftime("%Y-%m-%d")
    return df


def filter_apr_through_dec(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "datetime" not in df.columns:
        return df
    m = df["datetime"].dt.month
    return df[m.isin(APR_THROUGH_DEC)].copy()


def month_filter_options(df: pd.DataFrame) -> list[str]:
    d = filter_apr_through_dec(df)
    ys = sorted(d["year_month"].dropna().unique())
    return list(ys)


def default_month_choice(month_choices: list[str]) -> str | None:
    """Prefer April in the available set; otherwise pick the earliest month."""
    if not month_choices:
        return None
    april = [m for m in month_choices if str(m).endswith("-04")]
    if april:
        return sorted(april)[0]
    return month_choices[0]


def slice_for_dashboard(df: pd.DataFrame, month_choice: str) -> pd.DataFrame:
    out = filter_apr_through_dec(df)
    if month_choice:
        out = out[out["year_month"] == month_choice]
    return out


def signal_means_by_stress(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """Average EDA/HR/TEMP/Movement by stress label for the current filter."""
    if filtered_df is None or filtered_df.empty:
        return pd.DataFrame()
    cols = ["label_num", "EDA", "HR", "TEMP", "MovementMagnitude"]
    if any(c not in filtered_df.columns for c in cols):
        return pd.DataFrame()
    signal_df = filtered_df.dropna(subset=cols)
    signal_df = signal_df[signal_df["label_num"].isin([0, 1, 2])]
    if signal_df.empty:
        return pd.DataFrame()
    return (
        signal_df.groupby("label_num", as_index=False)[["EDA", "HR", "TEMP", "MovementMagnitude"]]
        .mean()
        .rename(columns={"label_num": "label"})
        .sort_values("label")
    )


def high_stress_contribution_by_month(df: pd.DataFrame, selected_month: str) -> pd.DataFrame:
    """High-stress reading contribution counts by caregiver for a selected month."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["id", "high_count", "pct"])
    month_data = slice_for_dashboard(df, selected_month)
    if month_data.empty or "label_num" not in month_data.columns:
        return pd.DataFrame(columns=["id", "high_count", "pct"])
    high_month = month_data[month_data["label_num"] == 2]
    if high_month.empty:
        return pd.DataFrame(columns=["id", "high_count", "pct"])
    contrib = (
        high_month.groupby("id", as_index=False)
        .size()
        .rename(columns={"size": "high_count"})
        .sort_values(["high_count", "id"], ascending=[False, True])
    )
    total_high = int(contrib["high_count"].sum())
    contrib["pct"] = np.where(total_high > 0, (contrib["high_count"] / total_high) * 100.0, 0.0)
    contrib["id"] = contrib["id"].astype(str)
    return contrib


def label_to_stress_phrase(label: float) -> str:
    try:
        v = int(round(float(label)))
    except (TypeError, ValueError):
        return "Unknown"
    return {0: "Low stress", 1: "Medium stress", 2: "High stress"}.get(v, "Unknown")


def stress_badge_label(label: float) -> tuple[str, str, str]:
    """(display text, bg hex, text hex)"""
    try:
        v = int(round(float(label)))
    except (TypeError, ValueError):
        return "Unknown", "#f1f5f9", "#64748b"
    m = {
        0: ("Stable", "#dcfce7", "#166534"),
        1: ("Elevated", "#fef9c3", "#854d0e"),
        2: ("Critical stress", "#ffe4e6", "#be123c"),
    }
    return m.get(v, ("Unknown", "#f1f5f9", "#64748b"))


def pick_representative_reading(cell_df: pd.DataFrame) -> pd.Series | None:
    if cell_df is None or cell_df.empty:
        return None
    return cell_df.sort_values(["label", "datetime"], ascending=[False, False]).iloc[0]


def row_to_popup_record(row: pd.Series, motion_max: float) -> dict:
    trec = row["time"] if "time" in row.index and pd.notna(row["time"]) else ""
    if trec == "" and pd.notna(row.get("datetime")):
        trec = str(row["datetime"])
    mag = float(row["MovementMagnitude"])
    mm = float(motion_max) if motion_max and motion_max > 0 else 1.0
    motion_pct = min(100.0, (mag / mm) * 100.0)
    lbl = int(round(float(row["label"])))
    stress_pct = (lbl / 2.0) * 100.0
    eda = float(row["EDA"])
    eda_max = 10.0
    eda_pct = min(100.0, (eda / eda_max) * 100.0) if eda_max else 0.0
    try:
        xyz = float(np.sqrt(float(row["X"]) ** 2 + float(row["Y"]) ** 2 + float(row["Z"]) ** 2))
    except Exception:
        xyz = 0.0
    return {
        "id": str(row["id"]),
        "HR": float(row["HR"]),
        "time_recorded": trec,
        "datetime_full": str(row["datetime"]) if pd.notna(row.get("datetime")) else "",
        "stress_level": label_to_stress_phrase(row["label"]),
        "motion_activity": mag,
        "motion_pct": motion_pct,
        "temperature": float(row["TEMP"]),
        "EDA": eda,
        "eda_pct": eda_pct,
        "stress_pct": stress_pct,
        "label": lbl,
        "date": str(row["date"]) if "date" in row.index and pd.notna(row.get("date")) else "",
        "xyz_mag": xyz,
    }


def _metric_tile(icon: str, label: str, value: str, icon_bg: str) -> str:
    label_e = html_module.escape(label)
    value_e = html_module.escape(value)
    return f"""
    <div style="display:flex;align-items:flex-start;gap:12px;background:#f8fafc;border-radius:12px;padding:14px 16px;border:1px solid #e2e8f0;">
      <div style="min-width:40px;height:40px;border-radius:10px;background:{icon_bg};display:flex;align-items:center;justify-content:center;font-size:1.1rem;">{icon}</div>
      <div style="flex:1;">
        <div style="font-size:0.72rem;color:#64748b;font-weight:600;letter-spacing:0.04em;">{label_e}</div>
        <div style="font-size:1.2rem;font-weight:700;color:#0f172a;margin-top:4px;">{value_e}</div>
      </div>
    </div>
    """


def render_sensor_popup_html(rec: dict) -> str:
    cid = html_module.escape(rec["id"])
    initials = html_module.escape(rec["id"][:2].upper() if len(rec["id"]) >= 2 else rec["id"].upper())
    badge_text, badge_bg, badge_fg = stress_badge_label(float(rec["label"]))
    badge_text_e = html_module.escape(badge_text)
    sub = html_module.escape("Wearable reading · sensor file only")
    return f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;color:#0f172a;">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:14px;">
          <div style="width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,#06b6d4,#0891b2);display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:1rem;">{initials}</div>
          <div>
            <div style="font-size:1.15rem;font-weight:700;">Caregiver ID {cid}</div>
            <div style="font-size:0.85rem;color:#64748b;margin-top:2px;">{sub}</div>
            <span style="display:inline-block;margin-top:8px;padding:4px 12px;border-radius:999px;font-size:0.75rem;font-weight:600;background:{badge_bg};color:{badge_fg};">{badge_text_e}</span>
          </div>
        </div>
      </div>
      <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;color:#94a3b8;margin:8px 0 12px 0;">VITAL METRICS</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        {_metric_tile("📈", "Stress index", f"{rec['stress_pct']:.0f}%", "#fee2e2")}
        {_metric_tile("❤️", "Heart rate", f"{rec['HR']:.0f} bpm", "#ffe4e6")}
        {_metric_tile("〰️", "Motion activity", f"{rec['motion_pct']:.0f}%", "#dbeafe")}
        {_metric_tile("⚡", "EDA (arousal)", f"{rec['eda_pct']:.0f}%", "#ede9fe")}
        {_metric_tile("🌡️", "Temperature", f"{rec['temperature']:.1f} °C", "#ffedd5")}
        {_metric_tile("📍", "Accel. magnitude", f"{rec['xyz_mag']:.1f}", "#ccfbf1")}
      </div>
      <p style="font-size:0.75rem;color:#94a3b8;margin-top:14px;margin-bottom:0;">Representative row for cell · time {html_module.escape(rec['time_recorded'] or rec['datetime_full'])}</p>
    </div>
    """


def _heatmap_matrix_bundle(exec_df: pd.DataFrame):
    lookup = {}
    motion_max = float(exec_df["MovementMagnitude"].max()) if not exec_df.empty else 1.0
    if exec_df.empty:
        return [], [], [], [], lookup, 360

    ex = exec_df.copy()
    ex["id"] = ex["id"].astype(str)
    ex["datetime"] = pd.to_datetime(ex["datetime"], errors="coerce")
    ex = ex.dropna(subset=["datetime"])
    ex["date_key"] = ex["datetime"].dt.strftime("%Y-%m-%d")
    ex = ex.sort_values("datetime")

    last_per_day = ex.groupby(["id", "date_key"], as_index=False).tail(1)

    ids = sorted(last_per_day["id"].unique().tolist())
    raw_days = last_per_day["date_key"].dropna().astype(str).unique().tolist()
    days = sorted(raw_days, key=lambda s: pd.Timestamp(s))

    z = []
    text = []
    for cid in ids:
        row_z = []
        row_t = []
        sub_c = last_per_day[last_per_day["id"] == cid]
        for day in days:
            cell = sub_c[sub_c["date_key"].astype(str) == str(day)]
            if cell.empty:
                row_z.append(np.nan)
                row_t.append("")
            else:
                row = cell.iloc[0]
                lbl = float(row["label"])
                row_z.append(lbl)
                row_t.append(str(int(lbl)))
                lookup[(str(cid), str(day))] = row_to_popup_record(row, motion_max)
        z.append(row_z)
        text.append(row_t)

    h = max(380, 40 * len(ids) + 160)
    return ids, days, z, text, lookup, h


def build_heatmap_bundle(exec_df: pd.DataFrame, month_choice: str):
    ids, days, z, text, lookup, h = _heatmap_matrix_bundle(exec_df)
    if not ids or not days:
        fig = go.Figure()
        fig.add_annotation(
            text="No data",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#94a3b8"),
        )
        fig.update_layout(height=360, paper_bgcolor="#f8fafc", plot_bgcolor="#f8fafc")
        return fig, lookup, 360

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[str(d) for d in days],
            y=[str(i) for i in ids],
            text=text,
            texttemplate="%{text}",
            textfont={"size": 9},
            colorscale=HEATMAP_COLORSCALE,
            zmin=0,
            zmax=2,
            colorbar=dict(title="Stress (label)", tickvals=[0, 1, 2], ticktext=["Low", "Med", "High"], len=0.5),
            hoverongaps=False,
            xgap=1,
            ygap=1,
        )
    )
    fig.update_layout(
        title=f"Stress — {month_choice}",
        xaxis=dict(side="bottom", tickangle=-40, type="category"),
        yaxis=dict(autorange="reversed", type="category"),
        height=h,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        margin=dict(l=60, r=30, t=50, b=100),
    )
    return fig, lookup, h


def _coverage_month_prep(month_trend: pd.DataFrame, month_dist: pd.DataFrame):
    hover_lookup = month_trend[["period", "readings", "high_stress_pct"]].rename(columns={"period": "year_month"})
    month_dist2 = month_dist.merge(hover_lookup, on="year_month", how="left")
    month_dist2["interpretation"] = month_dist2["high_stress_pct"].map(_stress_month_interpretation)

    mwide = (
        month_dist2.pivot_table(index="year_month", columns="Stress_Category", values="count", aggfunc="sum")
        .fillna(0)
        .reset_index()
    )
    for col in ["Low", "Medium", "High"]:
        if col not in mwide.columns:
            mwide[col] = 0
    mwide["total_readings"] = (mwide["Low"] + mwide["Medium"] + mwide["High"]).astype(int)
    mwide = mwide.merge(
        month_trend[["period", "high_stress_pct"]].rename(columns={"period": "year_month"}),
        on="year_month",
        how="left",
    )
    fallback_pct = pd.Series(
        np.where(mwide["total_readings"] > 0, 100.0 * (mwide["High"] / mwide["total_readings"]), 0.0),
        index=mwide.index,
        dtype="float64",
    )
    mwide["high_stress_pct"] = mwide["high_stress_pct"].astype("float64").fillna(fallback_pct)
    mwide["interpretation"] = mwide["high_stress_pct"].map(_stress_month_interpretation)
    mwide["month_label"] = pd.to_datetime(mwide["year_month"] + "-01", errors="coerce").dt.strftime("%b %Y")
    mwide["month_label"] = mwide["month_label"].fillna(mwide["year_month"].astype(str))
    month_tip = {
        str(r["year_month"]): (
            str(r["month_label"]),
            int(r["total_readings"]),
        )
        for _, r in mwide.iterrows()
    }
    return month_dist2, mwide, month_tip


def _coverage_daily_prep(sub_m: pd.DataFrame, day_trend: pd.DataFrame) -> pd.DataFrame:
    dd = sub_m.dropna(subset=["date_key", "Stress_Category"]).copy()
    day_dist = (
        dd.groupby(["date_key", "Stress_Category"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    piv = (
        day_dist.pivot_table(index="date_key", columns="Stress_Category", values="count", aggfunc="sum")
        .fillna(0)
        .reset_index()
    )
    for col in ["Low", "Medium", "High"]:
        if col not in piv.columns:
            piv[col] = 0
    piv["date_key"] = piv["date_key"].astype(str)

    daily = day_trend.merge(piv, left_on="period", right_on="date_key", how="left").fillna(0)
    daily["interpretation"] = daily["high_stress_pct"].map(_stress_month_interpretation)
    daily["high_count"] = daily["High"].astype(int)
    return daily

@st.cache_data(ttl=300)
def load_sensor_data() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/api/sensor/records", timeout=4)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
    except Exception:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "..", "data", "caregiver_stress_prediction_sensor_data.csv")
        df = pd.read_csv(path)
    return _prepare_sensor_df(df)


@st.cache_data(ttl=300)
def load_caregiver_details() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/api/caregivers", timeout=4)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception:
        base = os.path.dirname(__file__)
        path = os.path.join(base, "..", "data", "caregiver_details.csv")
        return pd.read_csv(path)


def post_chat(message: str, ui_state: dict, heatmap_cell: dict | None = None) -> str:
    try:
        payload = {"message": message, "ui_state": ui_state}
        if heatmap_cell is not None:
            payload["heatmap_cell"] = heatmap_cell
        r = requests.post(
            f"{API_BASE}/api/chat",
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return r.json().get("reply", "No reply from assistant.")
    except Exception as exc:
        return f"Could not reach the chat API ({exc}). Is the Flask server running on {API_BASE}?"


def _chat_inline_md_to_html(text: str) -> str:
    """Minimal markdown for chat bubbles: **bold** and newlines. Escapes HTML first."""
    t = html_module.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t.replace("\n", "<br/>")


# Inline SVG avatars (Ward Supervisor vs assistant bot) — no gradient IDs so rows can repeat safely
_AVATAR_SUPERVISOR_SVG = """
<svg class="msg-avatar-svg" viewBox="0 0 44 44" width="44" height="44" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="22" cy="22" r="20" fill="#0d9488"/>
  <circle cx="22" cy="22" r="20" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
  <path fill="rgba(255,255,255,0.95)" d="M22 12a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Zm-6.2 9.8c0-1.1.9-2 2-2h8.4c1.1 0 2 .9 2 2v.3c0 2.4-2.4 4.4-6.2 4.4s-6.2-2-6.2-4.4v-.3Z"/>
  <path fill="rgba(255,255,255,0.88)" d="M14 28.5h16v1.6c0 .8-.7 1.5-1.5 1.5h-13c-.8 0-1.5-.7-1.5-1.5v-1.6Z"/>
</svg>
""".strip()

_AVATAR_BOT_SVG = """
<svg class="msg-avatar-svg" viewBox="0 0 44 44" width="44" height="44" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="22" cy="22" r="20" fill="#16a34a"/>
  <circle cx="22" cy="22" r="20" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1"/>
  <rect x="13" y="16" width="18" height="12" rx="3" fill="rgba(255,255,255,0.92)"/>
  <circle cx="17.5" cy="22" r="1.6" fill="#047857"/>
  <circle cx="26.5" cy="22" r="1.6" fill="#047857"/>
  <path fill="none" stroke="#047857" stroke-width="1.4" stroke-linecap="round" d="M18 26.5h8"/>
  <path fill="rgba(255,255,255,0.85)" d="M19 14h6v2.2a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1V14Z"/>
</svg>
""".strip()

_HEADER_BOT_ICON = _AVATAR_BOT_SVG.replace('width="44" height="44"', 'width="42" height="42"', 1).replace(
    'class="msg-avatar-svg"', 'class="msg-avatar-svg header-bot-icon"', 1
)


def _render_chat_thread_html(messages: list[dict]) -> str:
    """Build scrollable messaging-style thread with bubbles and avatars."""
    parts: list[str] = []
    for m in messages:
        body = _chat_inline_md_to_html(m["content"])
        if m["role"] == "user":
            parts.append(
                f"""
<div class="msg-row msg-row-user" role="article">
  <div class="msg-meta msg-meta-user">Ward Supervisor</div>
  <div class="msg-row-inner">
    <div class="msg-bubble msg-bubble-user">{body}</div>
    <div class="msg-avatar msg-avatar-user" title="Ward Supervisor">{_AVATAR_SUPERVISOR_SVG}</div>
  </div>
</div>
""".strip()
            )
        else:
            parts.append(
                f"""
<div class="msg-row msg-row-assistant" role="article">
  <div class="msg-meta msg-meta-assistant">Care-Sync assistant</div>
  <div class="msg-row-inner">
    <div class="msg-avatar msg-avatar-assistant" title="Chatbot">{_AVATAR_BOT_SVG}</div>
    <div class="msg-bubble msg-bubble-assistant">{body}</div>
  </div>
</div>
""".strip()
            )
    return "\n".join(parts)


def _append_chat_exchange(prompt: str, ui_state: dict) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": post_chat(prompt, ui_state)})


def jump_to_assistant(prompt: str, month_label: str | None, selected_caregiver_id: str | None = None, heatmap_cell: dict | None = None):
    st.session_state.nav_menu = "Assistant"
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask anything about **this wearable dataset** or the **dashboard**—I’ll ground "
                    "answers in live stats. Questions outside that scope get a short “not for this dataset” reply."
                ),
            },
        ]
    st.session_state.messages.append({"role": "user", "content": prompt})
    ui_state = {
        "selected_caregiver_id": selected_caregiver_id,
        "month_label": month_label,
        "active_view": "assistant",
    }
    st.session_state.messages.append({"role": "assistant", "content": post_chat(prompt, ui_state, heatmap_cell)})
    st.rerun()


@st.dialog("Sensor reading")
def _heatmap_dialog(rec: dict, filter_month: str):
    st.markdown(POPUP_CSS, unsafe_allow_html=True)
    st.markdown(render_sensor_popup_html(rec), unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💬 Message", use_container_width=True, key="dlg_msg"):
            lbl = int(rec.get("label", -1))
            if lbl == 2:
                prompt = (
                    "Explain why this heatmap cell is **critical (High) stress**, using the sensor values "
                    "and the **exact date and time** of the reading, and how they compare to the rest of the dataset."
                )
                heat_payload = dict(rec)
            else:
                prompt = (
                    f"Sensor cell · ID **{rec['id']}** · {rec['time_recorded'] or rec['datetime_full']} · "
                    f"stress index {rec['stress_pct']:.0f}% · HR {rec['HR']:.0f} · motion {rec['motion_pct']:.0f}% · "
                    f"EDA {rec['EDA']:.2f} · temp {rec['temperature']:.2f}°C. What should I check next?"
                )
                heat_payload = None
            st.session_state.nav_menu = "Assistant"
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": (
                            "I answer questions about **this project’s sensor dataset** and dashboard "
                            "(stress labels, HR/EDA/temp/movement, heatmap, trends). "
                            "Anything else isn’t in scope—ask me about the data instead."
                        ),
                    },
                ]
            st.session_state.messages.append({"role": "user", "content": prompt})
            ui_jump = {
                "selected_caregiver_id": rec["id"],
                "month_label": filter_month,
                "active_view": "assistant",
            }
            st.session_state.messages.append(
                {"role": "assistant", "content": post_chat(prompt, ui_jump, heat_payload)}
            )
            st.rerun()
    with c2:
        if st.button("✓ Done", type="primary", use_container_width=True, key="dlg_done"):
            st.rerun()


def _kpi_card(col, accent: str, bg: str, title: str, value_str: str, subtitle: str):
    col.markdown(
        f"""
        <div class="kpi-card" style="
            background: linear-gradient(135deg, {bg} 0%, #ffffff 120%);
            border-left: 4px solid {accent};
            border-radius: 12px;
            padding: 16px 18px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 8px 22px rgba(2, 6, 23, 0.06);
            min-height: 108px;
        ">
            <div style="font-size: 0.75rem; font-weight: 600; color: #64748b; letter-spacing: 0.02em; text-transform: uppercase;">{title}</div>
            <div style="font-size: 1.75rem; font-weight: 700; color: {accent}; margin-top: 6px;">{value_str}</div>
            <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _cg_val(row: pd.Series, *keys: str) -> str:
    for k in keys:
        if k in row.index and pd.notna(row[k]) and str(row[k]).strip():
            return str(row[k])
    return ""


def _caregiver_card_html(row: pd.Series) -> str:
    e = html_module.escape
    name = e(_cg_val(row, "Name", "name"))
    cid = e(_cg_val(row, "ID", "id"))
    role = e(_cg_val(row, "Role", "role"))
    dept = e(_cg_val(row, "Department", "department"))
    exp = e(_cg_val(row, "Experience", "experience"))
    shift = e(_cg_val(row, "Shift Time", "shift_time"))
    certs = _cg_val(row, "Certifications", "certifications")
    cert_parts = [c.strip() for c in certs.split(",") if c.strip()][:5]
    cert_tags = "".join(
        f'<span style="display:inline-block;margin:3px 4px 0 0;padding:3px 8px;border-radius:999px;font-size:0.68rem;background:#e0f2fe;color:#0369a1;">{e(c)}</span>'
        for c in cert_parts
    )
    role_tag = f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:0.72rem;font-weight:600;background:#f1f5f9;color:#475569;">{role}</span>'
    dept_tag = f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:0.72rem;font-weight:600;background:#ecfdf5;color:#047857;">{dept}</span>'
    shift_tag = f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:0.72rem;font-weight:600;background:#fef3c7;color:#b45309;">{shift}</span>'
    return f"""
    <div style="font-family:system-ui,-apple-system,sans-serif;background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:20px 20px 18px;box-shadow:0 4px 14px rgba(15,23,42,0.06);height:100%;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
        <div style="min-width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#0d9488,#0f766e);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:0.95rem;">{cid[:2] if len(cid)>=2 else cid}</div>
        <span style="font-size:0.75rem;font-weight:700;color:#64748b;background:#f1f5f9;padding:4px 10px;border-radius:8px;">ID {cid}</span>
      </div>
      <div style="font-size:1.1rem;font-weight:700;color:#0f172a;margin-top:14px;">{name}</div>
      <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;">{role_tag}{dept_tag}{shift_tag}</div>
      <div style="font-size:0.8rem;color:#64748b;margin-top:12px;line-height:1.45;">{e(exp)}</div>
      <div style="margin-top:10px;">{cert_tags}</div>
    </div>
    """


sensor_df = load_sensor_data()
month_choices = month_filter_options(sensor_df)
if not month_choices:
    st.error("No Apr–Dec months were found in the dataset.")
    st.stop()

SIDEBAR_CSS = """
<style>
:root{
  --sbBgA: rgba(236, 253, 245, 0.78); /* mint */
  --sbBgB: rgba(240, 253, 244, 0.55); /* light green */
  --sbBgC: rgba(204, 251, 241, 0.35); /* teal tint */
  --sbBorder: rgba(15, 23, 42, 0.08);
  --sbInk: rgba(15, 23, 42, 0.92);
  --sbInkSoft: rgba(71, 85, 105, 0.92);
  --sbCard: rgba(255, 255, 255, 0.62);
  --sbCardBorder: rgba(15, 23, 42, 0.10);
  --sbHover: rgba(16, 185, 129, 0.12);
  --sbActiveA: #16a34a; /* green-600 */
  --sbActiveB: #14b8a6; /* teal-500 */
  --sbRing: rgba(16, 185, 129, 0.22);
}
section[data-testid="stSidebar"] {
    background:
      radial-gradient(1100px 520px at 12% 0%, rgba(16, 185, 129, 0.18), transparent 60%),
      radial-gradient(900px 520px at 88% 10%, rgba(20, 184, 166, 0.16), transparent 55%),
      linear-gradient(180deg, var(--sbBgA) 0%, var(--sbBgB) 52%, rgba(255,255,255,0.30) 100%) !important;
    border-right: 1px solid var(--sbBorder);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
}
section[data-testid="stSidebar"] > div { background: transparent !important; }

/* Profile header */
.csb-header { padding: 14px 14px 6px; }
.csb-brand {
  display:flex; align-items:center; gap:10px;
  font-weight: 900; letter-spacing:-0.02em; color: var(--sbInk);
  font-size: 1.28rem;
}
.csb-sub { color: var(--sbInkSoft); font-size:0.78rem; margin-top:2px; }
.csb-logo {
  width: 44px; height: 44px; border-radius: 16px;
  background: linear-gradient(135deg, #16a34a, #14b8a6);
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 14px 34px rgba(2, 6, 23, 0.14);
  border: 1px solid rgba(255,255,255,0.35);
  flex: 0 0 auto;
}
.csb-logo svg { width: 24px; height: 24px; }
.csb-logo path { fill: #ffffff; }
.csb-avatar {
  width:40px; height:40px; border-radius:14px;
  background: linear-gradient(135deg, #22c55e, #14b8a6);
  display:flex; align-items:center; justify-content:center;
  color:#fff; font-weight:900;
  box-shadow: 0 12px 26px rgba(2, 6, 23, 0.18);
}

/* Month select */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: var(--sbCard) !important;
    border: 1px solid var(--sbCardBorder) !important;
    border-radius: 14px !important;
    box-shadow: 0 14px 34px rgba(2, 6, 23, 0.10);
}
section[data-testid="stSidebar"] .stSelectbox label { color: var(--sbInk) !important; font-weight: 800 !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] span { color: var(--sbInk) !important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:has(input:focus) {
  box-shadow: 0 0 0 4px var(--sbRing) !important;
  border-color: rgba(34, 197, 94, 0.55) !important;
}

/* Option menu (navigation) */
section[data-testid="stSidebar"] .nav.nav-pills {
  padding: 4px 10px 8px !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] .nav-link {
  border-radius: 14px !important;
  padding: 10px 12px !important;
  margin: 2px 6px !important;
  color: rgba(15, 23, 42, 0.78) !important;
  font-weight: 800 !important;
  background: transparent !important;
}
section[data-testid="stSidebar"] .nav-link:hover {
  background: var(--sbHover) !important;
}
section[data-testid="stSidebar"] .nav-link.active {
  background: linear-gradient(90deg, var(--sbActiveA), var(--sbActiveB)) !important;
  color: #ffffff !important;
  box-shadow: 0 16px 34px rgba(2, 6, 23, 0.18) !important;
}
section[data-testid="stSidebar"] .nav-link .icon { margin-right: 10px !important; }
section[data-testid="stSidebar"] .nav-link .icon svg { fill: currentColor !important; }

/* Force override any default red selected styles from option-menu */
section[data-testid="stSidebar"] a.nav-link.active,
section[data-testid="stSidebar"] a.nav-link.active:hover {
  background: linear-gradient(90deg, var(--sbActiveA), var(--sbActiveB)) !important;
  color: #ffffff !important;
}
section[data-testid="stSidebar"] a.nav-link:hover:not(.active) {
  background: var(--sbHover) !important;
}

/* Small badge on menu items (optional) */
.csb-badge {
  display:inline-block; min-width: 24px;
  padding: 2px 8px; border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: rgba(236, 254, 255, 0.92);
  font-size: 0.72rem;
  font-weight: 900;
  float: right;
}

/* Global buttons — match sidebar color family everywhere */
button[kind="primary"] {
  background: linear-gradient(90deg, var(--sbActiveA), var(--sbActiveB)) !important;
  border: 1px solid rgba(15, 23, 42, 0.10) !important;
  color: #ffffff !important;
  font-weight: 850 !important;
  border-radius: 12px !important;
  transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease !important;
}
button[kind="primary"]:hover {
  filter: saturate(1.05);
  box-shadow: 0 12px 26px rgba(2, 6, 23, 0.14) !important;
  transform: translateY(-1px);
}
button[kind="primary"]:active {
  transform: translateY(0px);
}
button[kind="secondary"] {
  border-radius: 12px !important;
  border: 1px solid rgba(20, 184, 166, 0.30) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(240, 253, 250, 0.72)) !important;
  color: #0f766e !important;
  font-weight: 750 !important;
  transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease !important;
}
button[kind="secondary"]:hover {
  border-color: rgba(13, 148, 136, 0.55) !important;
  box-shadow: 0 10px 22px rgba(2, 6, 23, 0.10) !important;
  transform: translateY(-1px);
}
button[kind="secondary"]:active {
  transform: translateY(0px);
}
</style>
"""

st.markdown(
    "<style>.block-container { padding-top: 1.1rem; }</style>" + SIDEBAR_CSS,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div class="csb-header">
      <div class="csb-brand">
        <div class="csb-logo" aria-label="Care-Sync logo">
          <svg viewBox="0 0 24 24" role="img" aria-hidden="true">
            <path d="M3 12h4l2-5 3 10 2-5h7v2h-6l-3 7-3-10-1.5 4H3v-3Z"/>
          </svg>
        </div>
        <div>
          <div>Care-Sync</div>
          <div class="csb-sub">Stress intelligence · VAUED</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation
nav_labels = ["Dashboard", "Caregivers", "Assistant"]
nav_icons = ["house", "person-badge", "chat-dots-fill"]
legacy_map = {
    "📊  Dashboard": "Dashboard",
    "👤  Caregivers": "Caregivers",
    "✨  Assistant": "Assistant",
    "📊 Dashboard": "Dashboard",
    "👤 Caregiver details": "Caregivers",
    "🤖 Assistant": "Assistant",
}
if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "Dashboard"
st.session_state.nav_menu = legacy_map.get(st.session_state.nav_menu, st.session_state.nav_menu)
if st.session_state.nav_menu not in nav_labels:
    st.session_state.nav_menu = "Dashboard"

default_idx = nav_labels.index(st.session_state.nav_menu)
with st.sidebar:
    menu = option_menu(
        menu_title=None,
        options=nav_labels,
        icons=nav_icons,
        menu_icon=None,
        default_index=default_idx,
        orientation="vertical",
        styles={
            "container": {"padding": "0px", "background-color": "transparent"},
            "icon": {"color": "rgba(15,23,42,0.45)", "font-size": "18px"},
            "nav-link": {
                "font-size": "0.98rem",
                "text-align": "left",
                "color": "rgba(15,23,42,0.78)",
                "border-radius": "14px",
            },
            # This is the key bit: prevent the component default (red) selected color.
            "nav-link-selected": {
                "font-size": "0.98rem",
                "background": "linear-gradient(90deg, #16a34a, #14b8a6)",
                "color": "#ffffff",
                "border-radius": "14px",
            },
        },
    )
st.session_state.nav_menu = menu

if "filter_month" not in st.session_state:
    st.session_state.filter_month = default_month_choice(month_choices)
if st.session_state.filter_month not in month_choices:
    st.session_state.filter_month = default_month_choice(month_choices)

if menu == "Dashboard":
    filter_month = st.selectbox("Month", month_choices, key="filter_month")
elif menu == "Assistant":
    filter_month = st.sidebar.selectbox("Month", month_choices, key="filter_month")
else:
    filter_month = st.session_state.filter_month

filtered = slice_for_dashboard(sensor_df, filter_month)

_dash_sig = (filter_month, menu)
if "_dash_filter_sig" in st.session_state and st.session_state._dash_filter_sig != _dash_sig:
    st.session_state.pop("_heatmap_click_sig", None)
st.session_state._dash_filter_sig = _dash_sig

if menu == "Dashboard":
    st.session_state.active_view = "dashboard"

    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    st.markdown('<p class="dash-title">Stress intelligence</p>', unsafe_allow_html=True)
    st.caption("Wearable sensor data · Apr–Dec window")

    exec_df = filtered
    empty = exec_df.empty
    n_caregivers = 0 if empty else int(exec_df["id"].nunique())
    avg_temp = 0.0 if empty else float(exec_df["TEMP"].mean())
    avg_hr = 0.0 if empty else float(exec_df["HR"].mean())
    stress_pct = 0.0 if empty else float((exec_df["label"].mean() / 2.0) * 100)

    k1, k2, k3, k4 = st.columns(4)
    subs = ("Distinct IDs", "°C (mean)", "0–100 scale", "bpm (mean)")
    vals = (str(n_caregivers), f"{avg_temp:.2f}", f"{stress_pct:.1f}%", f"{avg_hr:.1f}")
    for col, (accent, bg, _t), title, val, sub in zip(
        (k1, k2, k3, k4), KPI_STYLES, ("Caregivers", "Avg temperature", "Stress index", "Avg heart rate"), vals, subs
    ):
        _kpi_card(col, accent, bg, title, val, sub)

    st.markdown("<br>", unsafe_allow_html=True)
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("##### 🧩 Stress heatmap")
        st.caption(
            "Shows the **daily stress label** (Low/Medium/High) per caregiver (y-axis) for the selected month (x-axis). "
            "Darker colors indicate higher stress. Click a cell for the underlying reading."
        )
    with h2:
        if st.button("Ask AI", use_container_width=True, key="ask_ai_heatmap"):
            jump_to_assistant(
                prompt=(
                    f"Explain the stress heatmap for **{filter_month}**. "
                    "Which caregivers look most frequently **High stress (label 2)**, and are there any notable day clusters?"
                ),
                month_label=filter_month,
            )

    heat_fig, cell_lookup, heat_h = build_heatmap_bundle(exec_df, filter_month)
    events = plotly_events(
        heat_fig,
        click_event=True,
        select_event=False,
        hover_event=False,
        override_height=min(900, max(420, heat_h + 100)),
        key="heatmap_evt", 
    )

    if events:
        pt = events[0]
        x_val, y_val = pt.get("x"), pt.get("y")
        sig = (x_val, y_val)
        if sig != st.session_state.get("_heatmap_click_sig"):
            st.session_state._heatmap_click_sig = sig
            rec = cell_lookup.get((str(y_val), str(x_val)))
            if rec is None:
                rec = cell_lookup.get((str(x_val), str(y_val)))
            if rec:
                _heatmap_dialog(rec, filter_month)

    st.markdown("---")
    tab_cov, tab_a, tab_b = st.tabs(["Coverage", "Comparison", "Signal relationships"])

    cov_df = filter_apr_through_dec(sensor_df)

    with tab_cov:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown("**📊 Coverage** · monthly stress dynamics")
            st.caption(
                "This view summarizes **how stress is distributed each month** (Low/Medium/High). "
                "It helps a ward manager quickly see **which months were most concerning** and whether things are getting better or worse."
            )
        with c2:
            if st.button("Ask AI", use_container_width=True, key="ask_ai_coverage"):
                jump_to_assistant(
                    prompt=(
                        "Explain the Coverage chart: which months have the highest **% High-stress readings**, "
                        "and how should we interpret spikes when the number of readings is low?"
                    ),
                    month_label=None,
                )
        month_trend = _stress_trend_series(cov_df, "Month")
        month_dist = _month_stress_distribution(cov_df)
        if month_trend.empty or month_dist.empty:
            st.caption("No rows in Apr–Dec slice.")
        else:
            # Plain-language summary + key insights
            highest_row = month_trend.sort_values("high_stress_pct", ascending=False).iloc[0]
            lowest_row = month_trend.sort_values("high_stress_pct", ascending=True).iloc[0]
            trend_label, slope = _trend_direction_label(month_trend)
            st.markdown(
                f"""
                **How to read this:** Each month is split into **Low (green)**, **Medium (amber)**, and **High (red)** readings.
                A taller red section means **more high-stress readings that month**. Click a month to see its daily pattern below.

                **Quick insight:** Highest stress was **{highest_row['period']}** ({highest_row['high_stress_pct']:.1f}% high stress, {int(highest_row['readings'])} readings).
                Lowest stress was **{lowest_row['period']}** ({lowest_row['high_stress_pct']:.1f}% high stress, {int(lowest_row['readings'])} readings).
                {trend_label} (about {slope:+.1f} percentage points per month).
                """
            )

            # Build stacked bar with rich hover content
            hover_lookup = (
                month_trend[["period", "readings", "high_stress_pct"]]
                .rename(columns={"period": "year_month"})
                .copy()
            )
            month_dist2 = month_dist.merge(hover_lookup, on="year_month", how="left")
            month_dist2["interpretation"] = month_dist2["high_stress_pct"].map(_stress_month_interpretation)

            # Month-level summary for tooltips: low/med/high + totals + % high
            mwide = (
                month_dist2.pivot_table(index="year_month", columns="Stress_Category", values="count", aggfunc="sum")
                .fillna(0)
                .reset_index()
            )
            for col in ["Low", "Medium", "High"]:
                if col not in mwide.columns:
                    mwide[col] = 0
            mwide["total_readings"] = (mwide["Low"] + mwide["Medium"] + mwide["High"]).astype(int)
            mwide = mwide.merge(
                month_trend[["period", "high_stress_pct"]].rename(columns={"period": "year_month"}),
                on="year_month",
                how="left",
            )
            fallback_pct = pd.Series(
                np.where(mwide["total_readings"] > 0, 100.0 * (mwide["High"] / mwide["total_readings"]), 0.0),
                index=mwide.index,
                dtype="float64",
            )
            mwide["high_stress_pct"] = mwide["high_stress_pct"].astype("float64").fillna(fallback_pct)
            mwide["interpretation"] = mwide["high_stress_pct"].map(_stress_month_interpretation)
            # Monthly hover: month/year + total only (segment hover shows just its own count)
            mwide["month_label"] = pd.to_datetime(mwide["year_month"] + "-01", errors="coerce").dt.strftime("%b %Y")
            mwide["month_label"] = mwide["month_label"].fillna(mwide["year_month"].astype(str))
            month_tip = {
                str(r["year_month"]): (
                    str(r["month_label"]),
                    int(r["total_readings"]),
                )
                for _, r in mwide.iterrows()
            }

            tfig = go.Figure()
            for cat in ["Low", "Medium", "High"]:
                sub = month_dist2[month_dist2["Stress_Category"] == cat]
                if sub.empty:
                    continue
                # For each stacked segment, show full month context in hover (counts, readings, % high)
                custom = np.array([month_tip.get(str(m), ("", 0)) for m in sub["year_month"].astype(str)])
                tfig.add_trace(
                    go.Bar(
                        x=sub["year_month"].astype(str),
                        y=sub["count"].astype(int),
                        name=cat,
                        marker=dict(color=COLOR_MAP.get(cat, "#94a3b8")),
                        customdata=custom,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            f"{cat} count: %{{y}}<br>"
                            "Total readings: %{customdata[1]}"
                            "<extra></extra>"
                        ),
                    )
                )

            tfig.update_layout(
                title="Monthly stress trend (distribution of readings)",
                barmode="stack",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                yaxis=dict(title="Readings (count)", showgrid=True, gridcolor="#f1f5f9"),
                xaxis=dict(title="Month", tickangle=-35),
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                height=460,
                margin=dict(b=88),
            )
            tfig.update_traces(marker_line_width=0)
            ev_cov = plotly_events(
                tfig,
                click_event=True,
                select_event=False,
                hover_event=False,
                override_height=460,
                key="cov_month_bar_evt",
            )
            if ev_cov:
                xm_raw = ev_cov[0].get("x", "")
                xm = str(xm_raw)
                valid = set(month_trend["period"].astype(str))

                # Plotly can return values like "Apr 2020" depending on axis formatting.
                if xm not in valid:
                    dt_guess = pd.to_datetime(xm, errors="coerce")
                    if pd.notna(dt_guess):
                        xm = dt_guess.strftime("%Y-%m")

                # Sometimes x arrives as a datetime-like object.
                if xm not in valid:
                    dt_guess = pd.to_datetime(xm_raw, errors="coerce")
                    if pd.notna(dt_guess):
                        xm = dt_guess.strftime("%Y-%m")

                if xm in valid:
                    st.session_state.cov_daily_month = xm

            months = month_trend["period"].astype(str).tolist()
            if "cov_daily_month" not in st.session_state:
                st.session_state.cov_daily_month = None

            # If the previously clicked month is no longer present, clear it.
            if st.session_state.cov_daily_month is not None and str(st.session_state.cov_daily_month) not in months:
                st.session_state.cov_daily_month = None

            if st.session_state.cov_daily_month is None:
                st.info("Click a month bar above to show the daily pattern for that month.")
            else:
                sel_m = str(st.session_state.cov_daily_month)
                sub_m = cov_df[cov_df["year_month"].astype(str) == sel_m]
                day_trend = _stress_trend_series(sub_m, "Day")
                st.markdown(f"##### Daily pattern · **{sel_m}**")
                if day_trend.empty:
                    st.caption("No daily rows for this month.")
                else:
                    # Build daily distribution for hover summaries (low/med/high counts per day)
                    dd = sub_m.dropna(subset=["date_key", "Stress_Category"]).copy()
                    day_dist = (
                        dd.groupby(["date_key", "Stress_Category"], as_index=False)
                        .size()
                        .rename(columns={"size": "count"})
                    )
                    piv = (
                        day_dist.pivot_table(index="date_key", columns="Stress_Category", values="count", aggfunc="sum")
                        .fillna(0)
                        .reset_index()
                    )
                    for col in ["Low", "Medium", "High"]:
                        if col not in piv.columns:
                            piv[col] = 0
                    piv["date_key"] = piv["date_key"].astype(str)

                    daily = day_trend.merge(piv, left_on="period", right_on="date_key", how="left").fillna(0)
                    daily["interpretation"] = daily["high_stress_pct"].map(_stress_month_interpretation)
                    daily["high_count"] = daily["High"].astype(int)

                    # Two-row chart: top = % high stress, bottom = readings volume (no dual axis)
                    dfig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.10,
                        row_heights=[0.65, 0.35],
                        subplot_titles=("High-stress share by day", "Readings volume (context)"),
                    )
                    custom = np.stack(
                        [
                            daily["readings"].astype(int).to_numpy(),
                            daily["high_count"].astype(int).to_numpy(),
                            daily["Low"].astype(int).to_numpy(),
                            daily["Medium"].astype(int).to_numpy(),
                            daily["High"].astype(int).to_numpy(),
                            daily["interpretation"].astype(str).to_numpy(),
                        ],
                        axis=-1,
                    )
                    dfig.add_trace(
                        go.Scatter(
                            x=daily["period"],
                            y=daily["high_stress_pct"],
                            name="% High stress",
                            mode="lines+markers",
                            line=dict(color=COLOR_MAP["High"], width=3),
                            marker=dict(size=8, color=COLOR_MAP["High"]),
                            customdata=custom,
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "High-stress readings: %{customdata[1]}<br>"
                                "% High stress: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        ),
                        row=1,
                        col=1,
                    )
                    dfig.add_trace(
                        go.Bar(
                            x=daily["period"],
                            y=daily["readings"],
                            name="Readings",
                            marker=dict(
                                # Calm, cool-toned green/teal volume color (healthcare-friendly)
                                # Base: #2E7D6E (46, 125, 110) with softened opacity
                                color="rgba(46, 125, 110, 0.78)",
                                line=dict(color="rgba(46, 125, 110, 0.42)", width=1),
                            ),
                            hovertemplate="<b>%{x}</b><br>Total readings: %{y}<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )
                    dfig.update_yaxes(title_text="% High stress", range=[0, 105], showgrid=True, gridcolor="#f1f5f9", row=1, col=1)
                    dfig.update_yaxes(title_text="Readings", showgrid=True, gridcolor="#f1f5f9", row=2, col=1)
                    dfig.update_xaxes(title_text="Date", tickangle=-35, row=2, col=1)

                    dfig.update_layout(
                        height=520,
                        legend=dict(orientation="h", y=1.02, x=0),
                        paper_bgcolor="#ffffff",
                        plot_bgcolor="#ffffff",
                        margin=dict(b=84),
                    )
                    st.plotly_chart(dfig, use_container_width=True)

                    # Insight summary for selected month (day-level)
                    d2 = daily.copy()
                    d2["_sort"] = pd.to_datetime(d2["period"], errors="coerce")
                    d2 = d2.dropna(subset=["_sort"])
                    if len(d2) >= 2:
                        hi_day = d2.sort_values(["high_stress_pct", "readings"], ascending=[False, False]).iloc[0]
                        lo_day = d2.sort_values(["high_stress_pct", "readings"], ascending=[True, False]).iloc[0]
                        day_label, day_slope, day_vol = _daily_trend_label(d2.rename(columns={"period": "period"}))
                        st.markdown(
                            f"""
                            **Selected month insight ({sel_m})**
                            - **Highest-stress day**: {hi_day['period']} · {hi_day['high_stress_pct']:.1f}% high stress ({int(hi_day['high_count'])}/{int(hi_day['readings'])} readings)
                            - **Lowest-stress day**: {lo_day['period']} · {lo_day['high_stress_pct']:.1f}% high stress ({int(lo_day['high_count'])}/{int(lo_day['readings'])} readings)
                            - **Pattern**: {day_label} (slope {day_slope:+.1f} pp/day, volatility ±{day_vol:.0f} pp)
                            """
                        )

    with tab_a:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown("**🧑‍⚕️ Comparison** · physiological signals across stress levels")
            st.caption(
                "This chart shows how body signals and movement change from Low to High stress."
            )
        with c2:
            if st.button("Ask AI", use_container_width=True, key="ask_ai_comparison"):
                jump_to_assistant(
                    prompt=(
                        f"For **{filter_month}**, explain which signals (EDA, HR, TEMP, Movement) "
                        "change the most from Low Stress to High Stress, and what a ward supervisor should watch."
                    ),
                    month_label=filter_month,
                )
        if empty:
            st.caption("No data for this month.")
        else:
            stress_name_map = {0: "Low Stress", 1: "Mild Stress", 2: "High Stress"}
            signal_map = {
                "EDA": "Skin Conductance (EDA)",
                "HR": "Heart Rate (HR)",
                "TEMP": "Body Temperature (TEMP)",
                "MovementMagnitude": "Movement",
            }
            signal_colors = {
                "Skin Conductance (EDA)": "#6f8fb8",  # muted blue
                "Heart Rate (HR)": "#c97b7b",         # muted red
                "Body Temperature (TEMP)": "#82b29a", # muted green
                "Movement": "#a487c8",                # muted purple
            }

            means = signal_means_by_stress(filtered)

            if means.empty:
                st.caption("Not enough physiological signal data to build this comparison chart.")
            else:
                # Baseline-index each signal for easy comparison across different units/scales.
                for col in ["EDA", "HR", "TEMP", "MovementMagnitude"]:
                    baseline_row = means.loc[means["label"] == 0, col]
                    baseline = float(baseline_row.iloc[0]) if not baseline_row.empty else float(means[col].mean())
                    if pd.isna(baseline) or baseline == 0:
                        baseline = float(means[col].mean()) if not pd.isna(means[col].mean()) and means[col].mean() != 0 else 1.0
                    means[col] = (means[col] / baseline) * 100.0

                plot_df = means.melt(
                    id_vars="label",
                    value_vars=["EDA", "HR", "TEMP", "MovementMagnitude"],
                    var_name="signal",
                    value_name="index_value",
                )
                plot_df["Stress_Level"] = plot_df["label"].map(stress_name_map)
                plot_df["Signal"] = plot_df["signal"].map(signal_map)
                plot_df["Raw_Feature"] = plot_df["signal"]

                def _bar_interpretation(raw_feature: str, stress_level: str, idx_val: float) -> str:
                    level_term = {
                        "Low Stress": "near baseline",
                        "Mild Stress": "elevated",
                        "High Stress": "markedly elevated",
                    }.get(stress_level, "changed")
                    if raw_feature == "EDA":
                        if stress_level == "Low Stress":
                            return "EDA is near baseline, suggesting lower physiological arousal."
                        if stress_level == "Mild Stress":
                            return "EDA is elevated here, suggesting stronger physiological arousal at Mild Stress."
                        return "EDA is highest here, indicating strong sympathetic activation under High Stress."
                    if raw_feature == "HR":
                        if stress_level == "Low Stress":
                            return "Heart rate remains near baseline, consistent with lower strain."
                        if stress_level == "Mild Stress":
                            return "Heart rate rises at Mild Stress, showing an early cardiovascular stress response."
                        return "Heart rate is strongly elevated at High Stress, supporting higher caregiver strain."
                    if raw_feature == "TEMP":
                        if stress_level == "Low Stress":
                            return "Body temperature is stable at low stress."
                        if stress_level == "Mild Stress":
                            return "Body temperature changes modestly at Mild Stress."
                        return "Body temperature shifts less than HR and EDA, so treat it as a supporting cue."
                    if raw_feature == "MovementMagnitude":
                        if stress_level == "Low Stress":
                            return "Movement is near baseline, suggesting routine activity load."
                        if stress_level == "Mild Stress":
                            return "Movement increases at Mild Stress, which may reflect workload and task intensity."
                        return "Movement is high here and helps explain physical workload alongside stress signals."
                    return f"This feature is {level_term} at this stress level."

                plot_df["Interpretation"] = plot_df.apply(
                    lambda r: _bar_interpretation(r["Raw_Feature"], r["Stress_Level"], float(r["index_value"])),
                    axis=1,
                )

                fig_grouped = px.bar(
                    plot_df,
                    x="Stress_Level",
                    y="index_value",
                    color="Signal",
                    barmode="group",
                    category_orders={"Stress_Level": ["Low Stress", "Mild Stress", "High Stress"]},
                    color_discrete_map=signal_colors,
                    title="Average Physiological Signals Across Stress Levels",
                    text="index_value",
                    custom_data=["Signal", "Stress_Level", "index_value", "Interpretation"],
                )
                fig_grouped.update_traces(
                    texttemplate="%{text:.0f}",
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>Feature:</b> %{customdata[0]}<br>"
                        "<b>Stress level:</b> %{customdata[1]}<br>"
                        "<b>Average value:</b> %{customdata[2]:.1f} (index, Low Stress = 100)<br>"
                        "<b>Interpretation:</b> %{customdata[3]}"
                        "<extra></extra>"
                    ),
                )
                fig_grouped.update_layout(
                    height=500,
                    paper_bgcolor="#ffffff",
                    plot_bgcolor="#ffffff",
                    bargap=0.28,
                    bargroupgap=0.10,
                    legend=dict(orientation="h", y=1.08, x=0, title=None),
                    margin=dict(t=85, b=55),
                )
                fig_grouped.update_xaxes(title_text="Stress level", showgrid=False)
                fig_grouped.update_yaxes(
                    title_text="Signal index (No Stress = 100)",
                    showgrid=True,
                    gridcolor="#edf2f7",
                    zeroline=False,
                )
                st.plotly_chart(fig_grouped, use_container_width=True)
                st.caption(
                    "EDA and HR are key physiological stress indicators. "
                    "Temperature often changes less, while movement adds activity and workload context."
                )

                # Insight summary for quick non-technical interpretation.
                high_vals = means.loc[means["label"] == 2, ["EDA", "HR", "TEMP", "MovementMagnitude"]]
                if not high_vals.empty:
                    growth = (high_vals.iloc[0] - 100.0).to_dict()
                    friendly = {
                        "EDA": "Skin Conductance (EDA)",
                        "HR": "Heart Rate (HR)",
                        "TEMP": "Body Temperature (TEMP)",
                        "MovementMagnitude": "Movement",
                    }
                    top_signal = max(growth, key=lambda k: growth[k])
                    low_signal = min(growth, key=lambda k: growth[k])
                    movement_delta = growth.get("MovementMagnitude", 0.0)
                    st.markdown(
                        f"""
                        **Quick insight for supervisors**
                        - **Strongest changing feature:** {friendly[top_signal]} shows the largest increase from Low Stress to High Stress (**{growth[top_signal]:+.1f}%**).
                        - **Most stable signal:** {friendly[low_signal]} changes the least (**{growth[low_signal]:+.1f}%**), often making it a secondary cue.
                        - **Movement context:** Movement shifts by **{movement_delta:+.1f}%** from Low to High Stress, which helps confirm whether higher stress may also be linked to workload intensity.
                        """
                    )

                st.markdown("---")
                st.markdown("**High Stress Contribution by Caregiver**")
                st.caption(
                    "Explore which caregivers contribute the largest share of high-stress readings in a selected month."
                )

                contrib_months = month_filter_options(sensor_df)
                if contrib_months:
                    if "comparison_high_month" not in st.session_state:
                        st.session_state.comparison_high_month = (
                            filter_month if filter_month in contrib_months else contrib_months[-1]
                        )
                    if st.session_state.comparison_high_month not in contrib_months:
                        st.session_state.comparison_high_month = contrib_months[-1]

                    selected_contrib_month = st.selectbox(
                        "Month (High stress caregiver contribution)",
                        contrib_months,
                        key="comparison_high_month",
                    )

                    contrib = high_stress_contribution_by_month(sensor_df, selected_contrib_month)

                    month_label_fmt = pd.to_datetime(
                        str(selected_contrib_month) + "-01", errors="coerce"
                    ).strftime("%B %Y")
                    if month_label_fmt == "NaT":
                        month_label_fmt = str(selected_contrib_month)

                    if contrib.empty:
                        st.info(
                            f"No High stress readings were found for {month_label_fmt}. "
                            "Try another month to compare caregiver contribution."
                        )
                    else:
                        total_high = int(contrib["high_count"].sum())

                        # Refined high-stress (non-red) palette for a calm dashboard style.
                        contrib_palette = [
                            "#0f766e",  # deep teal
                            "#a16207",  # dark amber/gold
                            "#7c3a8f",  # muted plum
                            "#9a5b2e",  # coral-brown / burnt orange
                            "#155e75",  # slate teal-blue
                            "#8b5e34",  # warm bronze
                            "#5b3b73",  # muted violet-plum
                            "#2f6f67",  # moss teal
                            "#6b7280",  # cool neutral
                        ]
                        contrib["color"] = [contrib_palette[i % len(contrib_palette)] for i in range(len(contrib))]
                        top_id = str(contrib.iloc[0]["id"]) if not contrib.empty else None
                        contrib["hover_interp"] = contrib.apply(
                            lambda r: (
                                "Largest contributor to high-stress readings this month."
                                if str(r["id"]) == top_id
                                else "Meaningful contributor; monitor alongside shift workload and recent trend."
                            ),
                            axis=1,
                        )

                        fig_contrib = go.Figure(
                            data=[
                                go.Pie(
                                    labels=contrib["id"],
                                    values=contrib["high_count"],
                                    hole=0.58,
                                    marker=dict(
                                        colors=contrib["color"].tolist(),
                                        line=dict(color="#ffffff", width=1.6),
                                    ),
                                    hovertemplate=(
                                        "<b>Caregiver ID:</b> %{label}<br>"
                                        "<b>High-stress readings:</b> %{value}<br>"
                                        "<b>Contribution:</b> %{percent:.1%}"
                                        "<extra></extra>"
                                    ),
                                    textinfo="percent",
                                    textposition="inside",
                                )
                            ]
                        )
                        fig_contrib.update_layout(
                            title=f"High Stress Contribution by Caregiver — {month_label_fmt}",
                            height=460,
                            margin=dict(t=72, b=24, l=10, r=10),
                            paper_bgcolor="#ffffff",
                            legend=dict(orientation="h", y=-0.05, x=0, title=None),
                        )

                        pie_events = plotly_events(
                            fig_contrib,
                            click_event=True,
                            hover_event=True,
                            select_event=False,
                            override_height=460,
                            key="high_contrib_evt", 
                        )

                        selected_id = None
                        if pie_events:
                            event = pie_events[0]
                            selected_id = event.get("label")
                            if selected_id is None and "pointNumber" in event:
                                pnum = event.get("pointNumber")
                                if isinstance(pnum, int) and 0 <= pnum < len(contrib):
                                    selected_id = str(contrib.iloc[pnum]["id"])
                            if selected_id:
                                st.session_state["_high_contrib_selected_id"] = str(selected_id)
                                st.session_state["_high_contrib_selected_month"] = str(selected_contrib_month)

                        if (
                            st.session_state.get("_high_contrib_selected_month") == str(selected_contrib_month)
                            and st.session_state.get("_high_contrib_selected_id")
                        ):
                            selected_id = str(st.session_state.get("_high_contrib_selected_id"))

                        if selected_id is None:
                            st.caption("Hover or click a caregiver slice to view a plain-language interpretation.")
                        else:
                            picked = contrib[contrib["id"] == str(selected_id)]
                            if not picked.empty:
                                picked_row = picked.iloc[0]
                                if str(picked_row["id"]) == top_id:
                                    interp = "This caregiver contributed the largest share of high-stress readings for the selected month."
                                else:
                                    interp = "This caregiver contributes a notable share of high-stress readings and should be reviewed alongside overall workload."
                                st.markdown(
                                    f"""
                                    **Selected caregiver detail**
                                    - **Caregiver ID:** {str(picked_row["id"])}
                                    - **High stress readings:** {int(picked_row["high_count"])}
                                    - **Contribution:** {float(picked_row["pct"]):.1f}%
                                    - **Interpretation:** {interp}
                                    """
                                )

                        if total_high < 12:
                            st.caption("This month has limited data. Interpret results with caution.")

                        top_two = contrib.head(2)
                        if len(top_two) == 1:
                            r0 = top_two.iloc[0]
                            st.markdown(
                                f"In **{month_label_fmt}**, caregiver **{r0['id']}** contributed the highest share of high-stress readings (**{r0['pct']:.1f}%**)."
                            )
                        elif len(top_two) >= 2:
                            r0 = top_two.iloc[0]
                            r1 = top_two.iloc[1]
                            st.markdown(
                                f"In **{month_label_fmt}**, caregiver **{r0['id']}** contributed the highest share of high-stress readings, "
                                f"followed by **{r1['id']}** ({r0['pct']:.1f}% vs {r1['pct']:.1f}%)."
                            )

    with tab_b:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown("### 🧠 Relationship between body signals")
            st.caption(
                "Explores how **HR, EDA, temperature, and movement** relate to stress labels. "
                "Look for separation between Low/Medium/High clusters and strong correlations."
            )
        with c2:
            if st.button("Ask AI", use_container_width=True, key="ask_ai_signals"):
                jump_to_assistant(
                    prompt=(
                        f"For **{filter_month}**, explain what the signal-relationship charts suggest: "
                        "which signals move most with stress labels, and what patterns stand out?"
                    ),
                    month_label=filter_month,
                )
        if empty:
            st.caption("No data for this month.")
        else:
            samp = filtered.dropna(subset=["HR", "EDA", "TEMP", "MovementMagnitude", "label"])
            if len(samp) > 800:
                samp = samp.sample(800, random_state=42)
            fig3d = px.scatter_3d(
                samp,
                x="HR",
                y="MovementMagnitude",
                z="EDA",
                color="Stress_Category",
                color_discrete_map=COLOR_MAP,
                symbol="Stress_Category",
                size_max=12,
                opacity=0.85,
                title="Stress vs heart rate vs movement (point color = stress level)",
                height=520,
            )
            fig3d.update_layout(scene=dict(xaxis_title="HR", yaxis_title="Movement", zaxis_title="EDA"))
            st.plotly_chart(fig3d, use_container_width=True)

            st.plotly_chart(_correlation_matrix_fig(filtered), use_container_width=True)

            st.plotly_chart(
                px.scatter(
                    filtered,
                    x="HR",
                    y="MovementMagnitude",
                    color="Stress_Category",
                    color_discrete_map=COLOR_MAP,
                    size="EDA",
                    hover_data=["id", "TEMP", "year_month"],
                    title="Heart rate vs movement (size = EDA)",
                    opacity=0.78,
                ),
                use_container_width=True,
            )

elif menu == "Caregivers":
    st.session_state.active_view = "caregiver_details"
    st.markdown("## Caregivers")
    st.caption("Profiles from caregiver_details.csv")

    cg = load_caregiver_details()
    if cg.empty:
        st.warning("No rows.")
    else:
        cg = cg.copy()
        cg["ID"] = cg["ID"].astype(str)
        id_list = sorted(cg["ID"].unique().tolist())
        filter_opt = ["All"] + id_list
        if "cg_id_filter" not in st.session_state:
            st.session_state.cg_id_filter = "All"
        if st.session_state.cg_id_filter not in filter_opt:
            st.session_state.cg_id_filter = "All"

        c_f1, c_f2 = st.columns([1, 2])
        with c_f1:
            st.selectbox("Filter by ID", filter_opt, key="cg_id_filter")

        fid = st.session_state.cg_id_filter
        show_df = cg if fid == "All" else cg[cg["ID"] == fid]

        st.markdown(f"<p style='color:#64748b;font-size:0.9rem;'>Showing <b>{len(show_df)}</b> of {len(cg)}</p>", unsafe_allow_html=True)

        n_cols = 3
        rows = [show_df.iloc[i : i + n_cols] for i in range(0, len(show_df), n_cols)]
        for chunk in rows:
            cols = st.columns(n_cols)
            for j in range(n_cols):
                with cols[j]:
                    if j < len(chunk):
                        st.markdown(_caregiver_card_html(chunk.iloc[j]), unsafe_allow_html=True)

elif menu == "Assistant":
    st.session_state.active_view = "assistant"
    BOT_NAME = "Care-Sync Bot"
    CHAT_SUGGESTIONS = [
        "Summarize stress trends for the selected month.",
        "Which caregiver IDs show the most High-stress readings?",
        "How should I interpret HR vs movement on the dashboard?",
        "What does EDA suggest when stress is elevated?",
        "Explain the heatmap colors and daily stress labels.",
        "What limitations should I keep in mind for this dataset?",
    ]

    CHAT_CSS = """
    <style>
    :root {
      --chat-teal-900: #0f766e;
      --chat-teal-700: #0d9488;
      --chat-teal-500: #14b8a6;
      --chat-teal-200: #99f6e4;
      --chat-teal-100: #ccfbf1;
      --chat-teal-50: #f0fdfa;
      --chat-ink: #0f172a;
      --chat-muted: #64748b;
      --chat-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
      --chat-shadow-soft: 0 4px 14px rgba(15, 23, 42, 0.06);
    }

    .msg-app {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      color: var(--chat-ink);
      margin-bottom: 0.35rem;
    }

    .msg-app-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 14px 16px;
      border-radius: 20px;
      border: 1px solid rgba(15, 23, 42, 0.08);
      background: linear-gradient(135deg, rgba(240, 253, 250, 0.95) 0%, rgba(255, 255, 255, 0.98) 55%, rgba(236, 253, 245, 0.75) 100%);
      box-shadow: var(--chat-shadow-soft);
      margin-bottom: 12px;
    }
    .msg-app-title {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .msg-app-title-text {
      font-weight: 850;
      letter-spacing: -0.02em;
      font-size: 1.15rem;
      color: var(--chat-ink);
      line-height: 1.2;
    }
    .msg-app-sub {
      color: var(--chat-muted);
      font-size: 0.82rem;
      font-weight: 600;
      margin-top: 3px;
    }
    .msg-app-badge {
      flex: 0 0 auto;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 800;
      color: #065f46;
      background: rgba(16, 185, 129, 0.14);
      border: 1px solid rgba(16, 185, 129, 0.22);
    }
    .msg-month-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.75);
      border: 1px solid rgba(15, 23, 42, 0.07);
      color: #475569;
      font-weight: 750;
      font-size: 0.88rem;
      margin: 4px 0 12px;
    }
    .msg-month-pill span {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(20, 184, 166, 0.16), rgba(16, 185, 129, 0.12));
      border: 1px solid rgba(20, 184, 166, 0.28);
      color: #0f766e;
      font-weight: 850;
    }

    .msg-scroll {
      max-height: min(58vh, 560px);
      overflow-y: auto;
      overflow-x: hidden;
      padding: 16px 14px 18px;
      border-radius: 20px;
      border: 1px solid rgba(15, 23, 42, 0.07);
      background:
        radial-gradient(900px 420px at 12% 0%, rgba(20, 184, 166, 0.10), transparent 55%),
        radial-gradient(700px 380px at 96% 18%, rgba(16, 185, 129, 0.08), transparent 52%),
        linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65), var(--chat-shadow-soft);
      scroll-behavior: smooth;
    }
    .msg-scroll::-webkit-scrollbar { width: 8px; }
    .msg-scroll::-webkit-scrollbar-thumb {
      background: rgba(15, 118, 110, 0.28);
      border-radius: 999px;
    }
    .msg-scroll::-webkit-scrollbar-track { background: transparent; }

    .msg-row { margin-bottom: 14px; }
    .msg-row:last-child { margin-bottom: 2px; }
    .msg-meta {
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: rgba(100, 116, 139, 0.92);
      margin: 0 52px 6px;
    }
    .msg-meta-user { text-align: right; }
    .msg-meta-assistant { text-align: left; }

    .msg-row-inner {
      display: flex;
      align-items: flex-end;
      gap: 10px;
      width: 100%;
    }
    .msg-row-user .msg-row-inner { justify-content: flex-end; }
    .msg-row-assistant .msg-row-inner { justify-content: flex-start; }

    .msg-avatar {
      flex: 0 0 auto;
      width: 44px;
      height: 44px;
      filter: drop-shadow(0 8px 16px rgba(15, 23, 42, 0.12));
    }
    .msg-avatar-svg { display: block; width: 44px; height: 44px; }

    .msg-bubble {
      max-width: min(78%, 560px);
      padding: 12px 14px 12px;
      border-radius: 18px;
      font-size: 0.98rem;
      line-height: 1.55;
      word-wrap: break-word;
    }
    .msg-bubble strong { color: inherit; font-weight: 800; }

    /* User: deeper teal tint (same family as assistant, darker/s richer) */
    .msg-bubble-user {
      color: #042f2e;
      background: linear-gradient(180deg, rgba(45, 212, 191, 0.42) 0%, rgba(20, 184, 166, 0.30) 100%);
      border: 1px solid rgba(13, 148, 136, 0.35);
      box-shadow: var(--chat-shadow-soft);
      border-bottom-right-radius: 8px;
    }
    /* Assistant: soft mint/teal wash */
    .msg-bubble-assistant {
      color: #0f172a;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(240, 253, 250, 0.92) 100%);
      border: 1px solid rgba(20, 184, 166, 0.22);
      box-shadow: var(--chat-shadow-soft);
      border-bottom-left-radius: 8px;
    }

    @media (max-width: 900px) {
      .msg-bubble { max-width: 88%; font-size: 0.95rem; }
      .msg-scroll { max-height: 52vh; padding: 14px 12px 16px; }
      .msg-meta { margin: 0 46px 6px; }
    }

    /* Composer: chat input */
    div[data-testid="stChatInput"] textarea {
      min-height: 44px !important;
      line-height: 1.45 !important;
    }
    div[data-testid="stChatInput"] > div {
      border-radius: 16px !important;
      border: 1px solid rgba(15, 23, 42, 0.10) !important;
      box-shadow: 0 14px 34px rgba(2, 6, 23, 0.08) !important;
      background: rgba(255, 255, 255, 0.95) !important;
    }
    div[data-testid="stChatInput"] > div:has(textarea:focus) {
      border-color: rgba(20, 184, 166, 0.55) !important;
      box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.18) !important;
    }

    .msg-app-header .header-bot-icon { flex: 0 0 auto; }

    /* Suggestion chips — scope to Assistant page (same view as .msg-app) */
    section.main div.block-container:has(.msg-app) div[data-testid="stVerticalBlockBorder"] {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(240, 253, 250, 0.55)) !important;
      border-color: rgba(15, 23, 42, 0.08) !important;
      border-radius: 16px !important;
      box-shadow: var(--chat-shadow-soft) !important;
    }
    section.main div.block-container:has(.msg-app) div[data-testid="stVerticalBlockBorder"] button[kind="secondary"] {
      border-radius: 999px !important;
      border: 1px solid rgba(20, 184, 166, 0.28) !important;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(240, 253, 250, 0.65)) !important;
      color: #0f766e !important;
      font-weight: 700 !important;
      font-size: 0.86rem !important;
      padding: 0.45rem 0.75rem !important;
      box-shadow: 0 6px 16px rgba(2, 6, 23, 0.05) !important;
      transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease !important;
    }
    section.main div.block-container:has(.msg-app) div[data-testid="stVerticalBlockBorder"] button[kind="secondary"]:hover {
      border-color: rgba(13, 148, 136, 0.55) !important;
      box-shadow: 0 10px 22px rgba(2, 6, 23, 0.08) !important;
      transform: translateY(-1px);
    }
    </style>
    """
    st.markdown(CHAT_CSS, unsafe_allow_html=True)

    ui_state = {
        "selected_caregiver_id": None,
        "month_label": filter_month,
        "active_view": "assistant",
    }

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask anything about **this wearable dataset** or the **dashboard**—I’ll ground "
                    "answers in live stats. Questions outside that scope get a short “not for this "
                    "dataset” reply."
                ),
            },
        ]

    filter_month_e = html_module.escape(str(filter_month))
    thread_html = _render_chat_thread_html(st.session_state.messages)
    st.markdown(
        f"""
        <div class="msg-app">
          <div class="msg-app-header">
            <div class="msg-app-title">
              {_HEADER_BOT_ICON}
              <div style="min-width:0;">
                <div class="msg-app-title-text">{html_module.escape(BOT_NAME)}</div>
                <div class="msg-app-sub">Clinical decision support · wearable stress intelligence</div>
              </div>
            </div>
            <div class="msg-app-badge" title="Assistant is available">Online</div>
          </div>
          <div class="msg-month-pill" role="status">Data month <span>{filter_month_e}</span></div>
          <div class="msg-scroll" id="caresync-chat-thread" aria-label="Conversation">
            {thread_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.caption("Suggested questions — tap to send")
        n_cols = 3
        for row in range(0, len(CHAT_SUGGESTIONS), n_cols):
            cols = st.columns(n_cols, gap="small")
            for j in range(n_cols):
                idx = row + j
                if idx < len(CHAT_SUGGESTIONS):
                    label = CHAT_SUGGESTIONS[idx]
                    with cols[j]:
                        if st.button(label, key=f"chat_sugg_{idx}", use_container_width=True, type="secondary"):
                            _append_chat_exchange(label, ui_state)

    if prompt := st.chat_input("Message the assistant…"):
        _append_chat_exchange(prompt, ui_state)

import html as html_module
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_plotly_events import plotly_events
from streamlit_option_menu import option_menu

API_BASE = os.environ.get("VAUED_API_BASE", "http://127.0.0.1:5000")

APR_THROUGH_DEC = list(range(4, 13))

st.set_page_config(
    page_title="Care-Sync AI | Stress Monitor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_MAP = {"Low": "#2ca02c", "Medium": "#ff7f0e", "High": "#d62728"}

HEATMAP_COLORSCALE = [
    [0.0, "#2ca02c"],  # label 0 = Low (green)
    [0.5, "#ffcc00"],  # label 1 = Medium (yellow)
    [1.0, "#d62728"],  # label 2 = High (red)
]

KPI_STYLES = [
    ("#0f766e", "#ecfdf5", "Caregivers"),
    ("#15803d", "#f0fdf4", "Temperature"),
    ("#047857", "#ecfdf5", "Stress index"),
    ("#065f46", "#f0fdf4", "Heart rate"),
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
    background: linear-gradient(90deg, var(--brandA), var(--brandB)) !important;
    border: 1px solid rgba(15, 23, 42, 0.08) !important;
}
button[kind="secondary"] {
    border-radius: 12px !important;
    border: 1px solid rgba(15, 23, 42, 0.12) !important;
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
    return ["All (April–December)"] + list(ys)


def slice_for_dashboard(df: pd.DataFrame, month_choice: str) -> pd.DataFrame:
    out = filter_apr_through_dec(df)
    if month_choice and month_choice != "All (April–December)":
        out = out[out["year_month"] == month_choice]
    return out


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


def build_heatmap_bundle(exec_df: pd.DataFrame, month_choice: str):
    lookup = {}
    motion_max = float(exec_df["MovementMagnitude"].max()) if not exec_df.empty else 1.0
    if exec_df.empty:
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

    if month_choice == "All (April–December)":
        # For aggregated view, show the latest available reading (end-of-shift proxy) per caregiver.
        x_labels = ["Apr–Dec (latest reading)"]
        ex = exec_df.copy()
        ex["id"] = ex["id"].astype(str)
        ex = ex.dropna(subset=["datetime"])
        ex = ex.sort_values("datetime")
        last_rows = ex.groupby("id", as_index=False).tail(1)
        ids = sorted(last_rows["id"].unique().tolist())

        z = []
        text = []
        for cid in ids:
            row = last_rows[last_rows["id"] == cid].iloc[0]
            lbl = float(row["label"])
            z.append([lbl])
            when = row["datetime"].strftime("%Y-%m-%d") if pd.notna(row["datetime"]) else ""
            text.append([f"{int(lbl)}<br>{when}"])
            lookup[(str(cid), x_labels[0])] = row_to_popup_record(row, motion_max)

        fig = go.Figure(
            data=go.Heatmap(
                z=z,
                x=x_labels,
                y=[str(i) for i in ids],
                text=text,
                texttemplate="%{text}",
                textfont={"size": 10},
                colorscale=HEATMAP_COLORSCALE,
                zmin=0,
                zmax=2,
                colorbar=dict(
                    title="Stress (label)",
                    tickvals=[0, 1, 2],
                    ticktext=["Low", "Med", "High"],
                    len=0.5,
                ),
                hoverongaps=False,
                xgap=1,
                ygap=1,
            )
        )
        h = max(320, 40 * len(ids) + 120)
        fig.update_layout(
            title="Stress by caregiver (latest reading in Apr–Dec)",
            xaxis=dict(side="bottom", type="category"),
            yaxis=dict(autorange="reversed", type="category"),
            height=h,
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            margin=dict(l=60, r=30, t=50, b=60),
        )
        return fig, lookup, h

    # Month view: Use only the last record of each day per caregiver (shift ending proxy).
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
    h = max(380, 40 * len(ids) + 160)
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


@st.cache_data(ttl=30)
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


@st.cache_data(ttl=30)
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
            st.session_state.nav_menu = "✨  Assistant"
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
                "month_label": None if filter_month == "All (April–December)" else filter_month,
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
        <div style="
            background: linear-gradient(135deg, {bg} 0%, #ffffff 120%);
            border-left: 4px solid {accent};
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(15,23,42,0.08);
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
    st.session_state.filter_month = "All (April–December)"
if st.session_state.filter_month in ("All months",):
    st.session_state.filter_month = "All (April–December)"
if st.session_state.filter_month not in month_choices:
    st.session_state.filter_month = month_choices[0]

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
    st.markdown("##### Stress heatmap")
    st.caption("Click a cell for details.")

    heat_fig, cell_lookup, heat_h = build_heatmap_bundle(exec_df, filter_month)
    events = plotly_events(
        heat_fig,
        click_event=True,
        select_event=False,
        hover_event=False,
        override_height=min(900, max(420, heat_h + 100)),
        key=f"heatmap_evt_{filter_month}",
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
        st.markdown("**Coverage** · monthly stress dynamics")
        st.caption(
            "Bars = readings per calendar month · line = share of **High** stress readings. "
            "**Click a month bar** (chart below) or pick a month to open the **daily** trend."
        )
        month_trend = _stress_trend_series(cov_df, "Month")
        if month_trend.empty:
            st.caption("No rows in Apr–Dec slice.")
        else:
            tfig = go.Figure()
            tfig.add_trace(
                go.Bar(
                    x=month_trend["period"],
                    y=month_trend["readings"],
                    name="Readings",
                    marker=dict(color="#5eead4", line=dict(color="#0f766e", width=1)),
                )
            )
            tfig.add_trace(
                go.Scatter(
                    x=month_trend["period"],
                    y=month_trend["high_stress_pct"],
                    name="% High-stress readings",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#e11d48", width=3),
                    marker=dict(size=11, color="#fda4af"),
                    fill="tozeroy",
                    fillcolor="rgba(225,29,72,0.07)",
                )
            )
            tfig.update_layout(
                title="Stress level changes over time (by month)",
                yaxis=dict(title="Readings", showgrid=True, gridcolor="#f1f5f9"),
                yaxis2=dict(title="% readings = High (label 2)", overlaying="y", side="right", range=[0, 105], showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                paper_bgcolor="#fafafa",
                plot_bgcolor="#ffffff",
                height=440,
                margin=dict(b=88),
            )
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
                    dfig = go.Figure()
                    dfig.add_trace(
                        go.Scatter(
                            x=day_trend["period"],
                            y=day_trend["high_stress_pct"],
                            name="% High-stress",
                            mode="lines+markers",
                            line=dict(color="#be123c", width=3),
                            marker=dict(size=9),
                        )
                    )
                    dfig.add_trace(
                        go.Scatter(
                            x=day_trend["period"],
                            y=day_trend["readings"],
                            name="Readings",
                            yaxis="y2",
                            mode="lines+markers",
                            line=dict(color="#0d9488", width=2.5),
                            marker=dict(size=8),
                        )
                    )
                    dfig.update_layout(
                        title="Daily stress pattern (lines)",
                        yaxis=dict(title="% High-stress", range=[0, 105], showgrid=True, gridcolor="#f1f5f9"),
                        yaxis2=dict(title="Readings", overlaying="y", side="right", showgrid=False),
                        legend=dict(orientation="h", y=1.02),
                        paper_bgcolor="#ffffff",
                        plot_bgcolor="#f8fafc",
                        height=400,
                        margin=dict(b=70),
                    )
                    st.plotly_chart(dfig, use_container_width=True)

    with tab_a:
        st.markdown("**Caregiver stress comparison** · who shows more high-stress readings?")
        if empty:
            st.caption("No data for this month.")
        else:
            rows_c = []
            for cid, sub in filtered.groupby("id"):
                rows_c.append(
                    {
                        "id": cid,
                        "readings": len(sub),
                        "high": int((sub["label"] == 2).sum()),
                        "med": int((sub["label"] == 1).sum()),
                        "low": int((sub["label"] == 0).sum()),
                    }
                )

            dist = (
                filtered.groupby(["id", "Stress_Category"], as_index=False)
                .size()
                .rename(columns={"size": "count"})
            )
            fig_stack = px.bar(
                dist,
                x="id",
                y="count",
                color="Stress_Category",
                color_discrete_map=COLOR_MAP,
                title="Stress level distribution — readings per caregiver",
                category_orders={"Stress_Category": ["Low", "Medium", "High"]},
            )
            fig_stack.update_layout(barmode="stack", paper_bgcolor="#fafafa", height=400, xaxis=dict(title="Caregiver ID"))
            st.plotly_chart(fig_stack, use_container_width=True)

            pie_df = filtered.groupby("Stress_Category", as_index=False).size().rename(columns={"size": "n"})
            fig_pie = px.pie(
                pie_df,
                names="Stress_Category",
                values="n",
                color="Stress_Category",
                color_discrete_map=COLOR_MAP,
                hole=0.45,
                title="Overall stress mix (current filter)",
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption("Stacked bars: readings per caregiver by stress level. Pie: share across the current filter.")

    with tab_b:
        st.markdown("### Relationship between body signals")
        st.caption("Multi-dimensional view · HR, EDA, TEMP, movement vs stress label")
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
    CHAT_CSS = """
    <style>
    /* Chat page shell */
    .chat-shell {
      max-width: none;
      margin: 0;
    }
    .chat-header {
      display:flex; align-items:center; justify-content:space-between;
      padding: 12px 14px;
      border-radius: 18px;
      border: 1px solid rgba(15,23,42,0.10);
      background: linear-gradient(180deg, rgba(240, 253, 244, 0.92), rgba(255,255,255,0.96));
      box-shadow: 0 10px 30px rgba(2,6,23,0.06);
      margin-bottom: 10px;
    }
    .assistant-bg {
      background: linear-gradient(180deg, rgba(236, 253, 245, 0.50) 0%, rgba(255,255,255,0.0) 40%);
      border-radius: 18px;
      padding: 14px 14px 10px;
      border: 1px solid rgba(15,23,42,0.06);
    }
    .chat-title {
      display:flex; align-items:center; gap:12px;
      font-weight: 900;
      letter-spacing: -0.02em;
      color: #0f172a;
    }
    .chat-sub { color:#64748b; font-size: 0.82rem; font-weight: 700; margin-top: 2px; }
    .bot-avatar {
      width: 42px; height: 42px; border-radius: 14px;
      background: linear-gradient(135deg, #16a34a, #14b8a6);
      display:flex; align-items:center; justify-content:center;
      color:#fff; font-weight: 950;
      box-shadow: 0 12px 26px rgba(2,6,23,0.12);
      flex: 0 0 auto;
    }
    .chat-chip {
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 900;
      color: #065f46;
      background: rgba(16,185,129,0.14);
      border: 1px solid rgba(16,185,129,0.25);
    }

    /* Streamlit chat message bubbles */
    div[data-testid="stChatMessage"] {
      border: 0 !important;
      background: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    div[data-testid="stChatMessage"] > div {
      border: 0 !important;
      background: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
    }

    /* message container */
    .chat-shell div[data-testid="stChatMessageContent"] {
      padding: 10px 12px !important;
      border-radius: 16px !important;
      border: 1px solid rgba(15,23,42,0.08) !important;
      box-shadow: 0 10px 24px rgba(2,6,23,0.05) !important;
      font-size: 0.98rem !important;
      line-height: 1.45 !important;
    }

    /* assistant bubble */
    .chat-shell div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stChatMessageContent"] {
      background: rgba(255,255,255,0.92) !important;
    }

    /* user bubble */
    .chat-shell div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) div[data-testid="stChatMessageContent"] {
      background: linear-gradient(180deg, rgba(22,163,74,0.18), rgba(20,184,166,0.14)) !important;
      border-color: rgba(16,185,129,0.25) !important;
    }

    /* Chat input */
    div[data-testid="stChatInput"] textarea {
      border-radius: 999px !important;
    }
    div[data-testid="stChatInput"] > div {
      border-radius: 999px !important;
      border: 1px solid rgba(15,23,42,0.12) !important;
      box-shadow: 0 16px 40px rgba(2,6,23,0.08) !important;
      background: rgba(255,255,255,0.92) !important;
    }
    </style>
    """
    st.markdown(CHAT_CSS, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="chat-shell">
          <div class="assistant-bg">
          <div class="chat-header">
            <div class="chat-title">
              <div class="bot-avatar">🤖</div>
              <div>
                <div>{BOT_NAME}</div>
                <div class="chat-sub">Chat about the caregiver stress dataset</div>
              </div>
            </div>
            <div class="chat-chip">Online</div>
          </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ui_state = {
        "selected_caregiver_id": None,
        "month_label": None if filter_month == "All (April–December)" else filter_month,
        "active_view": "assistant",
    }
    st.markdown(
        f"<div class='chat-shell'><div style='color:#475569;font-weight:900;margin:6px 2px 8px;'>Month: <span style='display:inline-block;padding:3px 10px;border-radius:999px;background:rgba(16,185,129,0.14);border:1px solid rgba(16,185,129,0.22);color:#065f46;'><b>{filter_month}</b></span></div></div>",
        unsafe_allow_html=True,
    )

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

    st.markdown("<div class='chat-shell'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Message…"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        reply = post_chat(prompt, ui_state)
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

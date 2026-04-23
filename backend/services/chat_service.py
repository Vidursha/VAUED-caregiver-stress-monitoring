import os
import re
from statistics import mean

from backend.database import get_db_connection

_DATA_TOPIC = re.compile(
    r"\b(stress|caregiver|sensor|wearable|reading|readings|label|eda|hr\b|heart\s*rate|"
    r"temp(erature)?|movement|motion|magnitude|dashboard|heatmap|dataset|data\b|"
    r"month|trend|correlation|anonym|burnout|anxiety|high\s*stress|low\s*stress|"
    r"medium|prediction|plot|chart|distribution|average|mean|median|count|how\s+many|"
    r"what\s+is|describe|explain|summarize|summary|overview|scope|records|samples|"
    r"fields|columns|variables|vaued|care[\s-]?sync|this\s+app|april|may|june|july|august|september|october|"
    r"november|december|sqlite|csv|plotly|streamlit|flask|kpi|accel|gyro|xyz|"
    r"electrodermal|physio|wear|bpm|arousal|critical|burnout)\b",
    re.I,
)
_META_TOPIC = re.compile(
    r"\b(hello|hi\b|hey|thanks|thank\s+you|help\b|capabilities|what\s+can\s+you|"
    r"who\s+are\s+you|good\s+morning|good\s+afternoon)\b",
    re.I,
)
_OFF_TOPIC = re.compile(
    r"\b(recipe|cook|weather\s+forecast|lottery|bitcoin|stock\s+tip|movie\s+recommend|"
    r"dating|homework\s+help|debug\s+my|leetcode|translate\s+this\s+poem|capital\s+of)\b",
    re.I,
)

OFF_TOPIC_REPLY = (
    "- This question is outside the scope of the caregiver stress dataset.\n"
    "- I can help with stress patterns, sensor readings, and dashboard insights.\n"
    "- Please ask something related to caregiver stress, trends, or the dashboard."
)


def _stress_label_name(v):
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return "unknown"
    return {0: "Low", 1: "Medium", 2: "High"}.get(n, "unknown")


def _month_num_from_text(message: str) -> str | None:
    m = (message or "").lower()
    month_map = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }
    for name, num in month_map.items():
        if re.search(rf"\b{name}\b", m):
            return num
    # Accept "jul" etc (avoid matching "may" inside words by requiring word boundary)
    short_map = {
        "jan": "01",
        "feb": "02",
        "mar": "03",
        "apr": "04",
        "jun": "06",
        "jul": "07",
        "aug": "08",
        "sep": "09",
        "sept": "09",
        "oct": "10",
        "nov": "11",
        "dec": "12",
    }
    for name, num in short_map.items():
        if re.search(rf"\b{name}\b", m):
            return num
    return None


def _infer_month_label_from_db(message: str) -> tuple[str | None, str | None]:
    """
    If the user mentions a month name (e.g. July) but UI didn't provide YYYY-MM,
    infer the YYYY-MM that exists in the DB (prefers a unique match).

    Returns (month_label, note) where note explains any disambiguation.
    """
    month_num = _month_num_from_text(message)
    if not month_num:
        return None, None

    conn = get_db_connection()
    c = conn.cursor()
    months = c.execute(
        """
        SELECT DISTINCT
          (2000 + CAST(substr(datetime, 7, 2) AS INTEGER)) || '-' || substr(datetime, 4, 2) AS ym
        FROM sensor_data
        ORDER BY ym
        """
    ).fetchall()
    conn.close()

    ym_list = [str(r["ym"]) for r in months if r is not None and r["ym"] is not None]
    matches = [ym for ym in ym_list if ym.endswith(f"-{month_num}")]
    if not matches:
        return None, None
    if len(matches) == 1:
        return matches[0], f"Inferred month from your text: **{matches[0]}**."

    # Multiple years have the same month; pick the latest in the dataset.
    chosen = sorted(matches)[-1]
    return chosen, (
        f"Your message mentions month **{month_num}**, which appears in multiple years: {', '.join(matches)}. "
        f"I used the latest available: **{chosen}**."
    )


def _month_label_sql_expr() -> str:
    # Stored datetimes are strings like dd-mm-yy; convert to YYYY-MM consistently.
    return "(2000 + CAST(substr(datetime, 7, 2) AS INTEGER)) || '-' || substr(datetime, 4, 2)"


def build_sensor_only_context(ui_state=None, message: str | None = None):
    """
    Analytics context derived strictly from sensor_data (no PII).
    ui_state may include: selected_caregiver_id (str), month_label (e.g. '2020-07').
    """
    ui_state = ui_state or {}
    sel_id = ui_state.get("selected_caregiver_id")
    month = ui_state.get("month_label")
    active_view = ui_state.get("active_view", "dashboard")

    inferred_note = None
    if not month and message:
        inferred, inferred_note = _infer_month_label_from_db(message)
        if inferred:
            month = inferred

    conn = get_db_connection()
    cursor = conn.cursor()

    def q(sql, params=()):
        return cursor.execute(sql, params).fetchall()

    total = q("SELECT COUNT(*) AS c FROM sensor_data")[0]["c"]
    ids = [str(r["id"]) for r in q("SELECT DISTINCT id FROM sensor_data ORDER BY id")]

    where = []
    params = []
    if sel_id:
        where.append("id = ?")
        params.append(sel_id)
    if month:
        where.append(f"{_month_label_sql_expr()} = ?")
        params.append(month)
    wh = (" WHERE " + " AND ".join(where)) if where else ""

    rows = q(f"SELECT EDA, HR, TEMP, MovementMagnitude, label FROM sensor_data{wh}", params)

    monthly = q(
        """
        SELECT
            """
        + _month_label_sql_expr()
        + """ AS ym,
            COUNT(DISTINCT id) AS n_ids,
            COUNT(*) AS n_readings
        FROM sensor_data
        GROUP BY ym
        ORDER BY ym
        """
    )

    least_block = None
    if month:
        least = q(
            """
            SELECT
              id,
              COUNT(*) AS n_readings,
              SUM(CASE WHEN label = 0 THEN 1 ELSE 0 END) AS low_n,
              SUM(CASE WHEN label = 1 THEN 1 ELSE 0 END) AS med_n,
              SUM(CASE WHEN label = 2 THEN 1 ELSE 0 END) AS high_n,
              AVG(label) AS mean_label
            FROM sensor_data
            WHERE """
            + _month_label_sql_expr()
            + """ = ?
            GROUP BY id
            ORDER BY mean_label ASC, high_n ASC, n_readings DESC, id ASC
            LIMIT 5
            """,
            (month,),
        )
        if least:
            best = least[0]
            least_block = (
                "Least-stressed caregiver IDs for this month (computed from `sensor_data`, lower mean label = less stress):\n"
                f"- **Least stressed:** id **{best['id']}** · mean label **{float(best['mean_label']):.2f}** · "
                f"Low/Med/High = **{int(best['low_n'])}/{int(best['med_n'])}/{int(best['high_n'])}** "
                f"out of **{int(best['n_readings'])}** readings.\n"
                + "\n".join(
                    f"- id **{r['id']}** · mean {float(r['mean_label']):.2f} · L/M/H {int(r['low_n'])}/{int(r['med_n'])}/{int(r['high_n'])} · n={int(r['n_readings'])}"
                    for r in least
                )
            )
    conn.close()

    if not rows:
        month_bits = [
            f"{r['ym']}: {r['n_ids']} caregiver id(s), {r['n_readings']} readings"
            for r in monthly
        ]
        lines = [
            "Subset: no rows match the current filters.",
            f"Global: {total} sensor rows; anonymized caregiver ids: {', '.join(ids)}.",
            "Monthly coverage (distinct anonymized ids vs readings): "
            + ("; ".join(month_bits) if month_bits else "n/a"),
        ]
        return "\n".join(lines)

    subset_n = len(rows)
    eda = [float(r["EDA"]) for r in rows]
    hr = [float(r["HR"]) for r in rows]
    temp = [float(r["TEMP"]) for r in rows]
    mov = [float(r["MovementMagnitude"]) for r in rows]
    labels = [_stress_label_name(r["label"]) for r in rows]

    from collections import Counter

    dist = Counter(labels)
    high_share = dist.get("High", 0) / subset_n if subset_n else 0

    month_bits = [
        f"{r['ym']}: {r['n_ids']} caregiver id(s), {r['n_readings']} readings"
        for r in monthly
    ]
    lines = [
        "Data scope: wearable sensor file only (no names, roles, or departments).",
        f"Active UI view: {active_view}.",
        f"Rows in current filter: {subset_n} (of {total} total in dataset).",
        f"Anonymized caregiver ids present in full dataset: {', '.join(ids)}.",
        "Monthly coverage (distinct anonymized ids vs readings): "
        + ("; ".join(month_bits) if month_bits else "n/a"),
        f"Stress label counts in current filter: Low={dist.get('Low', 0)}, "
        f"Medium={dist.get('Medium', 0)}, High={dist.get('High', 0)}.",
        f"Share of High stress readings in current filter: {high_share:.1%}.",
        f"Means in current filter — EDA: {mean(eda):.3f}, HR: {mean(hr):.1f} bpm, "
        f"TEMP: {mean(temp):.2f}, MovementMagnitude: {mean(mov):.2f}.",
    ]
    if inferred_note:
        lines.append(inferred_note)
    if sel_id:
        lines.append(f"Filter: anonymized caregiver id = {sel_id}.")
    if month:
        lines.append(f"Filter: calendar month (YYYY-MM) = {month}.")
    if least_block:
        lines.append(least_block)
    lines.append(
        "Interpretation hint: EDA and HR often move together with stress labels; "
        "compare distributions on the dashboard charts."
    )
    return "\n".join(lines)


def is_dataset_related(message: str, heatmap_cell: dict | None) -> bool:
    if heatmap_cell and isinstance(heatmap_cell, dict):
        return True
    m = (message or "").strip()
    if not m:
        return False
    if _OFF_TOPIC.search(m) and not _DATA_TOPIC.search(m):
        return False
    if _META_TOPIC.search(m) or _DATA_TOPIC.search(m):
        return True
    if len(m) <= 72 and "?" in m:
        return True
    short_ok = {
        "ok",
        "yes",
        "no",
        "cool",
        "nice",
        "got it",
        "thanks",
        "ty",
        "👍",
    }
    return m.lower() in short_ok


def build_dataset_digest() -> str:
    """Aggregate facts over the full sensor table for LLM grounding."""
    conn = get_db_connection()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) AS n FROM sensor_data").fetchone()["n"]
    n_ids = c.execute("SELECT COUNT(DISTINCT id) AS n FROM sensor_data").fetchone()["n"]
    span = c.execute("SELECT MIN(datetime) AS lo, MAX(datetime) AS hi FROM sensor_data").fetchone()
    means = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda, AVG(TEMP) AS te, "
        "AVG(MovementMagnitude) AS mv FROM sensor_data"
    ).fetchone()
    by_lbl = c.execute(
        "SELECT label, COUNT(*) AS c FROM sensor_data GROUP BY label ORDER BY label"
    ).fetchall()
    hi = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda FROM sensor_data WHERE label = 2"
    ).fetchone()
    lo = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda FROM sensor_data WHERE label = 0"
    ).fetchone()
    top_hi = c.execute(
        """
        SELECT id, SUM(CASE WHEN label = 2 THEN 1 ELSE 0 END) AS hi_n
        FROM sensor_data
        GROUP BY id
        ORDER BY hi_n DESC
        LIMIT 3
        """
    ).fetchall()
    hr_mm = c.execute(
        "SELECT MIN(HR) AS lo, MAX(HR) AS hi FROM sensor_data"
    ).fetchone()
    conn.close()

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    tot = max(int(total), 1)
    lbl_lines = []
    bar_parts = []
    for r in by_lbl:
        cnt = int(r["c"])
        lb = int(r["label"])
        pct = 100.0 * cnt / tot
        lbl_lines.append(f"  - label **{lb}** ({_stress_label_name(lb)}): **{cnt}** rows ({pct:.1f}% of all rows)")
        bar = "#" * max(1, int(round(pct / 5)))
        bar_parts.append(f"  L{lb} {bar} {pct:.0f}%")
    lbl_block = "\n".join(lbl_lines)
    ascii_bars = "Approximate label mix (each # ~5% of rows):\n" + "\n".join(bar_parts)
    top_bits = ", ".join(f"id {r['id']} ({int(r['hi_n'])} High readings)" for r in top_hi)
    return (
        f"**Proof snapshot — `sensor_data` table**\n"
        f"- **{total}** wearable rows, **{n_ids}** distinct anonymized caregiver ids.\n"
        f"- Timestamp span: **{span['lo']}** to **{span['hi']}**.\n"
        f"- HR range across all rows: **{_f(hr_mm['lo']):.1f}** - **{_f(hr_mm['hi']):.1f}** bpm.\n"
        f"{ascii_bars}\n"
        f"Exact counts:\n{lbl_block}\n"
        f"Global means — HR {_f(means['hr']):.1f} bpm, EDA {_f(means['eda']):.3f}, "
        f"TEMP {_f(means['te']):.2f}, MovementMagnitude {_f(means['mv']):.2f}.\n"
        f"Cohort reference — label **0 (Low)** mean HR {_f(lo['hr']):.1f}, EDA {_f(lo['eda']):.3f}; "
        f"label **2 (High)** mean HR {_f(hi['hr']):.1f}, EDA {_f(hi['eda']):.3f}.\n"
        f"IDs with the most High-stress (label 2) rows: {top_bits}."
    )


def _cell_float(cell: dict, *keys, default=0.0) -> float:
    for k in keys:
        if k in cell and cell[k] is not None:
            try:
                return float(cell[k])
            except (TypeError, ValueError):
                continue
    return default


def format_heatmap_cell_snippet(cell: dict | None) -> str:
    if not cell or not isinstance(cell, dict):
        return ""
    when = cell.get("datetime_full") or cell.get("time_recorded") or cell.get("date") or "n/a"
    mov = _cell_float(cell, "motion_activity", "MovementMagnitude")
    lines = [
        "User opened a heatmap cell (representative row for that cell):",
        f"- anonymized id: {cell.get('id', 'n/a')}",
        f"- date/time: {when}",
        f"- label: {cell.get('label', 'n/a')} ({cell.get('stress_level', '')})",
        f"- HR: {_cell_float(cell, 'HR'):.1f} bpm, EDA: {_cell_float(cell, 'EDA'):.3f}, "
        f"TEMP: {_cell_float(cell, 'temperature', 'TEMP'):.2f}, "
        f"MovementMagnitude: {mov:.2f}, stress_pct: {_cell_float(cell, 'stress_pct'):.0f}%",
    ]
    return "\n".join(lines)


def _is_critical_heatmap_cell(cell: dict | None) -> bool:
    if not cell or not isinstance(cell, dict):
        return False
    try:
        return int(float(cell.get("label", -1))) == 2
    except (TypeError, ValueError):
        return False


def build_critical_stress_narrative(cell: dict) -> str:
    """Deterministic explanation for label-2 (High) heatmap Message clicks."""
    cid = str(cell.get("id", ""))
    when = cell.get("datetime_full") or cell.get("time_recorded") or cell.get("date") or "unknown"
    hr = _cell_float(cell, "HR")
    eda = _cell_float(cell, "EDA")
    temp = _cell_float(cell, "temperature", "TEMP")
    mov = _cell_float(cell, "motion_activity", "MovementMagnitude")

    conn = get_db_connection()
    c = conn.cursor()
    g = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda, AVG(TEMP) AS te, "
        "AVG(MovementMagnitude) AS mv FROM sensor_data"
    ).fetchone()
    hi = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda, AVG(TEMP) AS te, "
        "AVG(MovementMagnitude) AS mv FROM sensor_data WHERE label = 2"
    ).fetchone()
    lo = c.execute(
        "SELECT AVG(HR) AS hr, AVG(EDA) AS eda, AVG(TEMP) AS te, "
        "AVG(MovementMagnitude) AS mv FROM sensor_data WHERE label = 0"
    ).fetchone()
    conn.close()

    def _f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    ghr, geda, gte, gmv = _f(g["hr"]), _f(g["eda"]), _f(g["te"]), _f(g["mv"])
    hhr, heda, hte, hmv = _f(hi["hr"]), _f(hi["eda"]), _f(hi["te"]), _f(hi["mv"])
    lhr, leda, lte, lmv = _f(lo["hr"]), _f(lo["eda"]), _f(lo["te"]), _f(lo["mv"])

    parts = [
        "### Critical stress — why this caregiver reading is **High (label 2)**",
        "",
        f"**When:** {when}  ",
        f"**Who (anonymized ID):** {cid}  ",
        "",
        "At this **date and time**, the wearable row behind this heatmap cell is classified as "
        "**critical stress** because the dataset assigns **label 2 (High)** — the top band on "
        "the 0–2 stress scale (100% stress index in the UI). Below is how **this row’s sensors** "
        "compare to the rest of the table so you can see *why* it sits in that band.",
        "",
        "**Sensor values for this moment vs the cohort**",
        f"- **Heart rate:** **{hr:.1f} bpm** — all-row mean {ghr:.1f}; Low-stress (label 0) mean {lhr:.1f}; "
        f"**High-stress (label 2) mean {hhr:.1f}**.",
        f"- **EDA:** **{eda:.3f}** — all-row mean {geda:.3f}; Low-stress mean {leda:.3f}; "
        f"**High-stress mean {heda:.3f}** (higher EDA usually reflects stronger arousal load).",
        f"- **Temperature:** **{temp:.2f} °C** — all-row mean {gte:.2f}; Low mean {lte:.2f}; High mean {hte:.2f}.",
        f"- **Movement magnitude:** **{mov:.2f}** — all-row mean {gmv:.2f}; Low mean {lmv:.2f}; High mean {hmv:.2f}.",
        "",
    ]
    cues = []
    if hr >= hhr - 0.5:
        cues.append("HR is at or above the cohort’s **High-stress** average, matching a strained cardiovascular load.")
    if eda >= heda - 0.02:
        cues.append("EDA is in line with **High-stress** rows, consistent with elevated arousal.")
    if hr < lhr and eda < leda:
        cues.append(
            "This row is still labeled High by the model; other features or sequence context in the "
            "full model may dominate—compare nearby readings for the same ID on the dashboard."
        )
    if not cues:
        cues.append(
            "Together, these signals sit in the **High** class relative to typical Low-stress readings; "
            "use Coverage / Comparison tabs to see how this ID behaves across months."
        )
    parts.append("**Interpretation:** " + " ".join(cues))
    return "\n".join(parts)
_SYSTEM_PROMPT = (
    "You are the Care-Sync clinical analytics assistant for senior caregivers and ward supervisors.\n"
    "Always respond in concise explainable format:\n"
    "- 3 to 5 short bullet points total.\n"
    "- Plain language, operational, easy to scan.\n"
    "- Use only facts from provided CONTEXT; do not invent values.\n"
    "- Briefly explain why and include one next-step action when useful.\n"
    "- Avoid long paragraphs, markdown headings, and large context dumps.\n"
    "If the question is out of scope, respond exactly with:\n"
    "- This question is outside the scope of the caregiver stress dataset.\n"
    "- I can help with stress patterns, sensor readings, and dashboard insights.\n"
    "- Please ask something related to caregiver stress, trends, or the dashboard."
)


def _to_short_bullets(text: str, *, min_points: int = 3, max_points: int = 5) -> str:
    raw = (text or "").replace("\r", "").strip()
    if not raw:
        return "- No clear answer was generated.\n- Please rephrase your question with month, caregiver, or stress trend."

    cleaned_lines = []
    for ln in raw.split("\n"):
        line = ln.strip()
        if not line:
            continue
        if line.startswith("###") or line.startswith("##"):
            continue
        if line.startswith("**Provider:**"):
            continue
        if line == "---":
            continue
        line = re.sub(r"^\s*[-*•]\s*", "", line)
        line = line.replace("**", "").strip()
        if line:
            cleaned_lines.append(line)

    if not cleaned_lines:
        cleaned_lines = [raw]

    pieces = []
    for line in cleaned_lines:
        split_parts = re.split(r"(?<=[.?!])\s+", line)
        for part in split_parts:
            p = part.strip(" -")
            if len(p) >= 12:
                pieces.append(p)

    if not pieces:
        pieces = cleaned_lines

    compact = []
    for p in pieces:
        t = re.sub(r"\s+", " ", p).strip()
        if len(t) > 170:
            t = t[:169].rstrip() + "…"
        if t and t not in compact:
            compact.append(t)

    selected = compact[:max_points]
    if len(selected) < min_points:
        fallback = [
            "Interpret this month and caregiver pattern first.",
            "Check stress label distribution and high-stress share.",
            "Use Coverage or Comparison views for next-step validation.",
        ]
        for item in fallback:
            if len(selected) >= min_points:
                break
            if item not in selected:
                selected.append(item)

    return "\n".join(f"- {x}" for x in selected[:max_points])


def _context_snapshot(context: str) -> str:
    wanted = (
        "Rows in current filter:",
        "Stress label counts in current filter:",
        "Share of High stress readings in current filter:",
        "Means in current filter",
        "Filter: calendar month",
        "Filter: anonymized caregiver id",
    )
    lines = []
    for line in (context or "").split("\n"):
        ln = line.strip()
        if not ln:
            continue
        if any(w in ln for w in wanted):
            lines.append(ln)
    return "\n".join(lines[:4])

def _is_quota_or_rate_limit(exc: BaseException) -> bool:
    s = str(exc).lower()
    if "429" in s or "quota" in s or "resource exhausted" in s or ("rate" in s and "limit" in s):
        return True
    try:
        from google.api_core import exceptions as gexc

        return isinstance(exc, (gexc.ResourceExhausted, gexc.TooManyRequests))
    except Exception:
        return False


def _is_model_not_found_or_unsupported(exc: BaseException) -> bool:
    s = str(exc).lower()
    # Common Gemini responses when a model name is invalid or not enabled for generateContent
    return (
        "not found" in s
        or "is not supported for generatecontent" in s
        or "unsupported for generatecontent" in s
        or "response modalities" in s
        or "not supported by the model" in s
        or "(text)" in s
        or "404" in s
        or "listmodels" in s
    )


def _is_text_chat_model_name(model_name: str) -> bool:
    """
    Keep models suitable for normal text chat and exclude audio/TTS variants.
    """
    name = (model_name or "").lower()
    blocked_tokens = ("tts", "audio", "preview-tts")
    return not any(token in name for token in blocked_tokens)


def _gemini_list_generate_models() -> list[str]:
    """
    Discover available Gemini models that support generateContent.

    We do this to avoid hardcoding a single model name that may not exist
    for the current API version / project / region.
    """
    import google.generativeai as genai

    key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    genai.configure(api_key=key)
    out: list[str] = []
    try:
        for m in genai.list_models():
            # m.name often looks like "models/gemini-1.5-flash"
            methods = getattr(m, "supported_generation_methods", None) or []
            if any(str(mm).lower() == "generatecontent" for mm in methods):
                name = getattr(m, "name", None)
                if name and _is_text_chat_model_name(str(name)):
                    out.append(str(name))
    except Exception:
        return []
    return out


def _gemini_try_model(model_name: str, message: str, context: str) -> str:
    import google.generativeai as genai

    key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    genai.configure(api_key=key)
    user = f"CONTEXT:\n{context}\n\nUSER QUESTION:\n{message}"
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=_SYSTEM_PROMPT,
    )
    r = model.generate_content(
        user,
        generation_config={"temperature": 0.3},
    )
    if not r.candidates:
        return (
            "[Gemini returned no text — possibly blocked by safety settings.]\n\n"
            f"{context}"
        )
    return (r.text or "").strip()


def _gemini_reply(message: str, context: str) -> str:
    preferred = os.environ.get("GEMINI_MODEL", "").strip()

    # 1) Discover models that support generateContent for this key/project.
    discovered = _gemini_list_generate_models()

    # 2) Build candidate list:
    #    - Try explicit env var first (accept both "gemini-*" and "models/gemini-*")
    #    - Then prefer smaller/faster "flash" family if present
    #    - Finally, try anything discovered that can generate content
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
        if not preferred.startswith("models/"):
            candidates.append("models/" + preferred)

    # Prefer "flash" then others, but never rely on these existing.
    if discovered:
        text_discovered = [m for m in discovered if _is_text_chat_model_name(m)]
        flash_first = [m for m in text_discovered if "flash" in m.lower()]
        others = [m for m in text_discovered if m not in flash_first]
        candidates.extend(flash_first + others)
    else:
        # If discovery fails (network / permissions), fall back to a small, modern set.
        # We still try multiple options and allow GEMINI_MODEL to override.
        candidates.extend(
            [
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-2.0-flash-lite",
                "models/gemini-1.5-flash",
            ]
        )

    # De-dupe while preserving order
    seen = set()
    candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
    last_err: BaseException | None = None
    for model_name in candidates:
        try:
            return _gemini_try_model(model_name, message, context)
        except Exception as exc:
            last_err = exc
            # If a particular model isn't available/supported, try the next one.
            if _is_model_not_found_or_unsupported(exc):
                continue
            # If quota/rate limited, also try the next one (some models may still have quota).
            if _is_quota_or_rate_limit(exc):
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("Gemini: no model candidates configured")


def _openai_reply(message: str, context: str) -> str:
    from openai import OpenAI

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip()
    client = OpenAI(api_key=key)
    user = f"CONTEXT:\n{context}\n\nUSER QUESTION:\n{message}"
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    return r.choices[0].message.content.strip()


def chat_reply(message: str, ui_state=None, heatmap_cell=None):
    message = (message or "").strip()
    hc = heatmap_cell if isinstance(heatmap_cell, dict) else None

    if _is_critical_heatmap_cell(hc):
        return _to_short_bullets(build_critical_stress_narrative(hc))

    if not message:
        return "Please type a question about the sensor data, stress labels, or the dashboard."

    if not is_dataset_related(message, hc):
        return OFF_TOPIC_REPLY

    digest = build_dataset_digest()
    cell_block = format_heatmap_cell_snippet(hc)
    base = build_sensor_only_context(ui_state, message=message)
    extra = ""
    if cell_block:
        extra = "\n\n" + cell_block
    context = (
        base
        + extra
        + "\n\nDATASET DIGEST (full-table facts; use for general dataset questions):\n"
        + digest
    )

    gemini_key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    chat_debug = os.environ.get("CHAT_DEBUG", "").strip().lower() in ("1", "true", "yes", "on")
    provider_prefix = ""

    if gemini_key:
        try:
            provider_prefix = "**Provider:** Gemini (Google Generative AI)\n\n" if chat_debug else ""
            return provider_prefix + _to_short_bullets(_gemini_reply(message, context))
        except Exception as exc:
            if _is_quota_or_rate_limit(exc):
                return (
                    "**Gemini could not run — Google returned a quota / rate limit (HTTP 429).**  \n"
                    "Your API key is valid, but this **project has no remaining free-tier requests** for the "
                    "models you tried (or you hit per-minute limits). The app still **called** Gemini; "
                    "Google refused the request before any answer was generated.\n\n"
                    "**Fix (pick one):** enable billing in [Google AI Studio](https://aistudio.google.com/), "
                    "wait for the daily reset, set `GEMINI_MODEL` to a model that still has quota, or set "
                    "`OPENAI_API_KEY` to use OpenAI instead. Unset both keys to use offline answers only.\n\n"
                    "---\n\n"
                    + _to_short_bullets(_fallback_conversational(message, context))
                )
            return (
                f"[Gemini error: {exc}]\n\n"
                + _to_short_bullets(_fallback_conversational(message, context))
            )

    if openai_key:
        try:
            provider_prefix = "**Provider:** OpenAI\n\n" if chat_debug else ""
            return provider_prefix + _to_short_bullets(_openai_reply(message, context))
        except Exception as exc:
            return (
                f"[OpenAI error: {exc}]\n\n" + _to_short_bullets(_fallback_conversational(message, context))
            )

    provider_prefix = "**Provider:** Offline (rule-based)\n\n" if chat_debug else ""
    return provider_prefix + _to_short_bullets(_fallback_conversational(message, context))


def _fallback_conversational(message: str, context: str) -> str:
    """Rule-based answer that always responds to the user's words (no cloud LLM)."""
    intro = f"Question: {message.strip()[:180]}"
    body = _offline_reply(message, context)
    return intro + body


def _offline_reply(message: str, context: str):
    m = message.lower()
    snapshot = _context_snapshot(context)
    if any(k in m for k in ("hello", "hi ", "hey", "thanks", "thank you")):
        return (
            "\nI can help with stress patterns, signal behavior, and month-level dashboard interpretation."
        )
    if any(k in m for k in ("name", "who is", "role", "department")):
        return (
            "\nThe dashboard intentionally hides names and roles."
            "\nUse anonymized caregiver IDs and stress trends for decision support."
        )
    if any(k in m for k in ("factor", "influence", "correlate", "important")):
        return (
            "\nEDA and HR are typically the strongest stress-related signals in this dataset."
            "\nMovement and temperature provide context for activity and physiological state."
            "\nUse Comparison and Signal Relationships views to validate this pattern."
        )
    if any(k in m for k in ("trend", "anomal", "spike", "pattern")):
        return (
            "\nFocus on high-stress share over time and identify repeat spikes."
            "\nCompare anonymized IDs side by side for persistence vs isolated events."
            + (f"\n{snapshot}" if snapshot else "")
        )
    if any(
        k in m
        for k in (
            "describe the",
            "summarize",
            "summary of",
            "overview",
            "what is in the",
            "what's in the",
            "whats in the",
            "tell me about the data",
            "tell me about the dataset",
            "how big is",
            "how many rows",
        )
    ):
        return (
            "\nHere is a concise snapshot from your live sensor dataset."
            + (f"\n{snapshot}" if snapshot else "\nNo filtered rows available in the current scope.")
            + "\nAsk a focused follow-up by month or caregiver ID."
        )
    return (
        "\nAsk about one month, one caregiver, or one stress trend for best clarity."
        "\nI can summarize high-stress share, sensor signals, and practical next actions."
        + (f"\n{snapshot}" if snapshot else "")
    )

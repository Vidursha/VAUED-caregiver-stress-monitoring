from backend.database import get_db_connection
import re

SENSOR_COLUMNS = (
    "id, date, time, datetime, X, Y, Z, EDA, HR, TEMP, MovementMagnitude, label"
)
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _month_label_sql_expr() -> str:
    # Stored datetimes are strings like dd-mm-yy; convert to YYYY-MM consistently.
    return "(2000 + CAST(substr(datetime, 7, 2) AS INTEGER)) || '-' || substr(datetime, 4, 2)"


def _clean_month(month):
    if month is None:
        return None
    value = str(month).strip()
    if not MONTH_PATTERN.match(value):
        return None
    return value


def _build_filters(caregiver_id=None, month=None):
    where = []
    params = []

    if caregiver_id:
        where.append("CAST(id AS TEXT) = ?")
        params.append(str(caregiver_id).strip())

    clean_month = _clean_month(month)
    if clean_month:
        where.append(f"{_month_label_sql_expr()} = ?")
        params.append(clean_month)

    where_sql = ""
    if where:
        where_sql = " WHERE " + " AND ".join(where)

    return where_sql, params


def list_sensor_records(caregiver_id=None, month=None):
    """Wearable readings with optional filtering for React-friendly API use."""
    conn = get_db_connection()
    cursor = conn.cursor()

    where_sql, params = _build_filters(caregiver_id=caregiver_id, month=month)

    rows = cursor.execute(
        f"""
        SELECT {SENSOR_COLUMNS}
        FROM sensor_data
        {where_sql}
        ORDER BY datetime
        """,
        params,
    ).fetchall()

    conn.close()
    return [_row_to_jsonable(dict(row)) for row in rows]


def _row_to_jsonable(row):
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = None
        else:
            out[k] = v
    return out
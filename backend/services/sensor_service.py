from backend.database import get_db_connection

SENSOR_COLUMNS = (
    "id, date, time, datetime, X, Y, Z, EDA, HR, TEMP, MovementMagnitude, label"
)


def list_sensor_records():
    """All wearable readings; no join to caregiver_details (dashboard-safe)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        f"""
        SELECT {SENSOR_COLUMNS}
        FROM sensor_data
        ORDER BY datetime
        """
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

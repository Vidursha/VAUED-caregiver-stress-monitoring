from backend.database import get_db_connection
import re

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _month_label_sql_expr() -> str:
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


def get_dashboard_summary(stress_column="label", caregiver_id=None, month=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    where_sql, params = _build_filters(caregiver_id=caregiver_id, month=month)

    total_records = cursor.execute(
        f"SELECT COUNT(*) AS count FROM sensor_data{where_sql}",
        params
    ).fetchone()["count"]

    avg_stress = cursor.execute(
        f"SELECT AVG({stress_column}) AS avg_stress FROM sensor_data{where_sql}",
        params
    ).fetchone()["avg_stress"]

    conn.close()

    return {
        "total_records": total_records,
        "average_stress": avg_stress
    }


def get_stress_distribution(stress_column="label", caregiver_id=None, month=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    where_sql, params = _build_filters(caregiver_id=caregiver_id, month=month)

    rows = cursor.execute(
        f"""
        SELECT {stress_column} AS stress_value, COUNT(*) AS count
        FROM sensor_data
        {where_sql}
        GROUP BY {stress_column}
        ORDER BY {stress_column}
        """,
        params
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_monthly_stress_trend(caregiver_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    where = []
    params = []

    if caregiver_id:
        where.append("CAST(id AS TEXT) = ?")
        params.append(str(caregiver_id).strip())

    where_sql = ""
    if where:
        where_sql = " WHERE " + " AND ".join(where)

    rows = cursor.execute(
        f"""
        SELECT
            {_month_label_sql_expr()} AS month,
            COUNT(*) AS total_readings,
            AVG(label) AS average_stress
        FROM sensor_data
        {where_sql}
        GROUP BY month
        ORDER BY month
        """,
        params
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]
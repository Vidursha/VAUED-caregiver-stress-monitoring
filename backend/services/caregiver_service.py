from backend.database import get_db_connection


def _stress_agg_subquery():
    return """
        SELECT
            CAST(id AS TEXT) AS sid,
            COUNT(*) AS sensor_readings,
            AVG(label) AS avg_stress_label,
            SUM(CASE WHEN label = 2 THEN 1 ELSE 0 END) AS high_stress_readings
        FROM sensor_data
        GROUP BY CAST(id AS TEXT)
    """


def get_caregiver_stress_list():
    """Caregiver profiles joined with sensor aggregates (same anonymized ID)."""
    conn = get_db_connection()
    cur = conn.cursor()
    rows = cur.execute(
        f"""
        SELECT
            cd.*,
            COALESCE(ag.sensor_readings, 0) AS sensor_readings,
            ag.avg_stress_label,
            COALESCE(ag.high_stress_readings, 0) AS high_stress_readings
        FROM caregiver_details cd
        LEFT JOIN ({_stress_agg_subquery()}) ag
            ON ag.sid = CAST(cd.ID AS TEXT)
        ORDER BY CAST(cd.ID AS TEXT)
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_caregiver_by_id(caregiver_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    row = cur.execute(
        f"""
        SELECT
            cd.*,
            COALESCE(ag.sensor_readings, 0) AS sensor_readings,
            ag.avg_stress_label,
            COALESCE(ag.high_stress_readings, 0) AS high_stress_readings
        FROM caregiver_details cd
        LEFT JOIN ({_stress_agg_subquery()}) ag
            ON ag.sid = CAST(cd.ID AS TEXT)
        WHERE CAST(cd.ID AS TEXT) = ?
        LIMIT 1
        """,
        (str(caregiver_id).strip(),),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

from backend.database import get_db_connection

def get_dashboard_summary(stress_column="label"):
    conn = get_db_connection()
    cursor = conn.cursor()

    total_records = cursor.execute(
        "SELECT COUNT(*) AS count FROM sensor_data"
    ).fetchone()["count"]

    avg_stress = cursor.execute(
        f"SELECT AVG({stress_column}) AS avg_stress FROM sensor_data"
    ).fetchone()["avg_stress"]

    conn.close()

    return {
        "total_records": total_records,
        "average_stress": avg_stress
    }

def get_stress_distribution(stress_column="label"):
    conn = get_db_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        f"""
        SELECT {stress_column} AS stress_value, COUNT(*) AS count
        FROM sensor_data
        GROUP BY {stress_column}
        ORDER BY {stress_column}
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]
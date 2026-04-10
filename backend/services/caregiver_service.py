from backend.database import get_db_connection

def get_caregiver_stress_list(stress_column="label"):
    conn = get_db_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        f"""
        SELECT
            c.ID,
            c.Name,
            c.Role,
            c.Department,
            c.Experience,
            c."Shift Time" AS shift_time,
            c.Certifications,
            AVG(s.{stress_column}) AS average_stress,
            MAX(s.{stress_column}) AS max_stress
        FROM caregiver_details c
        LEFT JOIN sensor_data s
            ON c.ID = s.id
        GROUP BY
            c.ID, c.Name, c.Role, c.Department,
            c.Experience, c."Shift Time", c.Certifications
        ORDER BY c.ID
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_caregiver_by_id(caregiver_id, stress_column="label"):
    conn = get_db_connection()
    cursor = conn.cursor()

    profile = cursor.execute(
        f"""
        SELECT
            c.ID,
            c.Name,
            c.Role,
            c.Department,
            c.Experience,
            c."Shift Time" AS shift_time,
            c.Certifications,
            AVG(s.{stress_column}) AS average_stress,
            MAX(s.{stress_column}) AS max_stress,
            COUNT(s.id) AS sensor_records
        FROM caregiver_details c
        LEFT JOIN sensor_data s
            ON c.ID = s.id
        WHERE c.ID = ?
        GROUP BY
            c.ID, c.Name, c.Role, c.Department,
            c.Experience, c."Shift Time", c.Certifications
        """,
        (caregiver_id,)
    ).fetchone()

    conn.close()

    return dict(profile) if profile else None
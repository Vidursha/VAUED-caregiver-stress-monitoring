"""Load CSV sensor and caregiver tables into SQLite (used by CLI and auto-init)."""

from pathlib import Path

import pandas as pd

from backend.database import BASE_DIR, DB_PATH

DATA_DIR = BASE_DIR / "data"
SENSOR_CSV = DATA_DIR / "caregiver_stress_prediction_sensor_data.csv"
CAREGIVER_CSV = DATA_DIR / "caregiver_details.csv"


def seed_from_csv() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SENSOR_CSV.is_file():
        raise FileNotFoundError(f"Missing sensor CSV: {SENSOR_CSV}")
    if not CAREGIVER_CSV.is_file():
        raise FileNotFoundError(f"Missing caregiver CSV: {CAREGIVER_CSV}")

    sensor_df = pd.read_csv(SENSOR_CSV)
    caregiver_df = pd.read_csv(CAREGIVER_CSV)

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS sensor_data")
    cursor.execute("DROP TABLE IF EXISTS caregiver_details")
    caregiver_df.to_sql("caregiver_details", conn, if_exists="replace", index=False)
    sensor_df.to_sql("sensor_data", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def main():
    seed_from_csv()
    print("Database created successfully at:", DB_PATH)


if __name__ == "__main__":
    main()

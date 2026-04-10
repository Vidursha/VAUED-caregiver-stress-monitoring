import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "nurse_stress.db"

SENSOR_CSV = DATA_DIR / "caregiver_stress_prediction_sensor_data.csv"
CAREGIVER_CSV = DATA_DIR / "caregiver_details.csv"

def main():
    sensor_df = pd.read_csv(SENSOR_CSV)
    caregiver_df = pd.read_csv(CAREGIVER_CSV)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS sensor_data")
    cursor.execute("DROP TABLE IF EXISTS caregiver_details")

    caregiver_df.to_sql("caregiver_details", conn, if_exists="replace", index=False)
    sensor_df.to_sql("sensor_data", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

    print("Database created successfully at:", DB_PATH)

if __name__ == "__main__":
    main()
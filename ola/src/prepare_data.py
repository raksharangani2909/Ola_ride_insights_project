"""
Ola Ride Insights - data cleaning & preprocessing.

Reads the raw OLA workbook, cleans it, derives features and writes:
  data/ola_rides_clean.csv   -> for Power BI / MySQL import
  data/ola.db                -> SQLite database used by the Streamlit app

Usage:
    python src/prepare_data.py path/to/OLA_DataSet.xlsx
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    # --- standardise column names / drop the image-url column (kept in a lookup table)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df = df.drop(columns=["Vehicle_Images"], errors="ignore")

    # --- types
    df["Date"] = pd.to_datetime(df["Date"])               # holds date + time
    df["Time"] = df["Time"].astype(str)                    # HH:MM:SS
    for c in ["Booking_ID", "Customer_ID", "Booking_Status", "Vehicle_Type",
              "Pickup_Location", "Drop_Location", "Payment_Method"]:
        df[c] = df[c].astype("string").str.strip()

    # --- duplicates
    df = df.drop_duplicates(subset="Booking_ID").reset_index(drop=True)

    # --- derived features
    df["Ride_Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["Ride_Datetime"] = df["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Hour"] = df["Date"].dt.hour
    df["Day_Of_Month"] = df["Date"].dt.day
    df["Day_Name"] = df["Date"].dt.day_name()
    df["Week_Number"] = df["Date"].dt.isocalendar().week.astype(int)
    df["Is_Weekend"] = df["Date"].dt.dayofweek.ge(5).astype(int)
    df["Time_Of_Day"] = pd.cut(
        df["Hour"], bins=[-1, 5, 11, 16, 20, 23],
        labels=["Night (0-5)", "Morning (6-11)", "Afternoon (12-16)",
                "Evening (17-20)", "Late Night (21-23)"]).astype(str)
    df["Is_Success"] = (df["Booking_Status"] == "Success").astype(int)
    # revenue only counts for completed bookings
    df["Revenue"] = df["Booking_Value"].where(df["Is_Success"] == 1, 0)
    df["Distance_Bucket"] = pd.cut(
        df["Ride_Distance"], bins=[-1, 0, 10, 20, 30, 40, 50],
        labels=["0 (no ride)", "1-10", "11-20", "21-30", "31-40", "41-50"]).astype(str)

    # Date column now only needs the calendar date; ISO string is portable to SQL/Power BI
    df["Date"] = df["Ride_Date"]
    df = df.drop(columns=["Ride_Date"])
    return df


def main(xlsx: str) -> None:
    DATA.mkdir(exist_ok=True)
    raw = pd.read_excel(xlsx, sheet_name="July")
    print(f"raw rows: {len(raw):,}")

    df = clean(raw)
    print(f"clean rows: {len(df):,}")

    # vehicle -> icon lookup (Sheet2 of the workbook)
    veh = (pd.read_excel(xlsx, sheet_name="Sheet2", header=None, names=["Vehicle_Type", "Image_URL"])
             .dropna().drop_duplicates("Vehicle_Type"))

    df.to_csv(DATA / "ola_rides_clean.csv", index=False)
    veh.to_csv(DATA / "vehicle_images.csv", index=False)

    db = DATA / "ola.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    df.to_sql("ola_rides", con, index=False)
    veh.to_sql("vehicle_images", con, index=False)
    for col in ["Booking_Status", "Vehicle_Type", "Customer_ID", "Date", "Payment_Method"]:
        con.execute(f"CREATE INDEX idx_{col.lower()} ON ola_rides({col})")
    con.commit()
    con.close()
    print("wrote:", *(p.name for p in DATA.iterdir()), sep="\n  ")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "OLA_DataSet.xlsx")

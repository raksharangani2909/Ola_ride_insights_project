# Ola Ride Insights

SQL + Power BI + Streamlit analytics project on 103,024 Ola bookings (July 2024).

```
app.py                      Streamlit app (10 pages, dark theme)
src/prepare_data.py         cleaning + feature engineering -> CSV + SQLite
sql/ola_queries.sql         the 10 required SQL queries (ANSI: MySQL + SQLite)
sql/schema_mysql.sql        MySQL table + load script (for Power BI -> MySQL)
data/ola_rides_clean.csv    cleaned dataset (Power BI / MySQL source)
data/ola.db                 SQLite DB used by the app
data/vehicle_images.csv     vehicle icon lookup
powerbi/Ola_Dashboard/      Power BI Project (.pbip) - open in Desktop, save as .pbix (see OPEN_ME.md)
powerbi/                    DAX measures, Power Query, theme, manual build guide
```

## Run locally
```bash
pip install -r requirements.txt
python src/prepare_data.py path/to/OLA_DataSet.xlsx   # optional: data/ already included
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (`git init && git add . && git commit -m "Ola insights" && git push`).
2. share.streamlit.io > New app > pick repo, branch `main`, file `app.py` > Deploy. To see the app working go through this link -->https://olarideinsightsproject-3h8994ewgvdnatznbprvhu.streamlit.app/ 
3. Settings > Secrets: `POWERBI_URL = "<publish-to-web link>"`.

## Cleaning applied
- Standardised column names, stripped text, parsed dates/times, removed duplicate Booking_IDs (none found).
- Nulls kept as NULL on purpose: ratings, payment, TAT and "incomplete" flags are blank for the 39,057 rides that never completed; cancel/incomplete reason columns are blank unless that event happened.
- Derived: Hour, Day_Name, Week_Number, Is_Weekend, Time_Of_Day, Is_Success, Revenue (booking value of successful rides only), Distance_Bucket.

## Key findings
- 62.1% of bookings succeed; 28.1% are cancelled (drivers 17.9%, customers 10.2%) and 9.8% never find a driver.
- Successful bookings are worth ₹35.08 M; ₹21.45 M of booking value was lost to non-completed rides.
- Cash 55% of revenue, UPI 40%; cards under 5%.
- Demand is nearly flat through the day (12:00, 15:00 and 08:00 are only marginally busiest); Tuesday is the busiest weekday, Sunday the quietest.
- Top customer cancel reason: driver not moving towards pickup (3,175). Top driver reason: personal & car issues (6,542).
- Ratings are flat (driver 4.00, customer 4.00 on average) and uncorrelated (r = -0.003); vehicle types perform near-identically, so the levers are operational (driver allocation, driver-side cancellations), not vehicle mix.

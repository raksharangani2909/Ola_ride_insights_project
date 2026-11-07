# Power BI dashboard - build guide (~30 min)

I could not generate the `.pbix` itself (Power BI Desktop is the only tool that writes that binary format).
Everything it needs is in this folder; following the steps gives the 5-page report your brief asks for.

## 1. Load data
1. Power BI Desktop > **Get data > Text/CSV** > `data/ola_rides_clean.csv` (or paste `powerquery.m`;
   or connect MySQL after running `sql/schema_mysql.sql`). Name the table **ola_rides**.
2. **View > Themes > Browse for themes** > `ola_theme.json`.
3. **Home > New measure**: paste each line of `measures.dax`.
4. Optional: add `data/vehicle_images.csv` and relate on `Vehicle_Type` for icons.
5. Weekday order: add a column `Day_No = WEEKDAY(ola_rides[Date], 2)`, then select `Day_Name` > Column tools > Sort by column > `Day_No`.

## 2. Pages & visuals (one page per view in the brief)
Add slicers on every page: **Date** (between), **Vehicle_Type**, **Booking_Status**. Sync slicers (View > Sync slicers).

| Page | Visual | Type | Fields |
|---|---|---|---|
| **1 Overall** | KPI cards | Card x5 | Total Bookings, Success Rate %, Total Revenue, Avg Ride Distance, Cancellation Rate % |
| | Ride volume over time | Line chart | X `Date`, Y `Total Bookings` |
| | Booking status breakdown | Donut | Legend `Booking_Status`, Values `Total Bookings` |
| **2 Vehicle Type** | Top 5 vehicle types by ride distance | Bar | Y `Vehicle_Type`, X `Total Distance (km)`, Filters: Top N = 5 by `Total Distance (km)` |
| | Avg customer rating by vehicle | Column | `Vehicle_Type`, `Avg Customer Rating` |
| **3 Revenue** | Revenue by payment method | Donut / column | `Payment_Method`, `Total Revenue` (filter out blank) |
| | Top 5 customers by booking value | Bar | `Customer_ID`, `Total Revenue`, Top N = 5 |
| | Ride distance per day | Column + avg line | X `Date`, Y `Total Distance (km)`; Analytics pane > Average line |
| **4 Cancellation** | Cancelled reasons (customer) | Bar | `Canceled_Rides_by_Customer`, `Total Bookings` (filter out blank) |
| | Cancelled reasons (driver) | Bar | `Canceled_Rides_by_Driver`, `Total Bookings` (filter out blank) |
| | Incomplete rides | Donut | `Incomplete_Rides_Reason`, `Incomplete Rides` |
| **5 Ratings** | Driver ratings distribution | Column | X `Driver_Ratings` (Don't summarize), Y Count of Booking_ID |
| | Customer ratings distribution | Column | X `Customer_Rating`, Y Count of Booking_ID |
| | Customer vs driver rating | Scatter | X `Avg Customer Rating`, Y `Avg Driver Rating`, Details `Vehicle_Type` |

## 3. Publish & embed in Streamlit
1. **Home > Publish** to Power BI Service (free work/school account - see the steps in your project doc).
2. In the Service: **File > Embed report > Publish to web (public)** > copy the link.
3. Paste it in the app's *Power BI Dashboard* page, or set `POWERBI_URL` in Streamlit secrets.
4. Save the file as `powerbi/Ola_Dashboard.pbix` and commit it with the rest.

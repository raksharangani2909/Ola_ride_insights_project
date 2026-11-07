"""
OLA Ride Insights - Bengaluru, July 2024  (Streamlit analytics app)
Pages: Overview | Overall | Vehicle Type | Revenue | Cancellation | Ratings |
       SQL Queries | Power BI Dashboard | Insights & Anomalies | Data Explorer
Run:   streamlit run app.py
"""
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "ola.db"
SQL_FILE = ROOT / "sql" / "ola_queries.sql"

# ------------------------------------------------------------------ page setup
st.set_page_config(page_title="OLA Ride Insights", page_icon="🚖", layout="wide")

GREEN, ORANGE, AMBER, SLATE = "#2E9F4F", "#E4572E", "#F5A623", "#7F95A3"
PALETTE = [GREEN, AMBER, "#3B82F6", ORANGE, "#A78BFA", "#22D3EE", "#A3E635"]
STATUS_COLORS = {"Success": GREEN, "Canceled by Driver": ORANGE,
                 "Canceled by Customer": AMBER, "Driver Not Found": SLATE}
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = PALETTE

st.markdown("""
<style>
.block-container {padding-top: 2.2rem;}
div[data-testid="stMetric"] {border:1px solid rgba(128,128,128,.28); border-radius:12px; padding:14px 18px;}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data layer
def _ensure_db() -> None:
    """Build the SQLite DB from the clean CSV if it is missing (fresh deploy)."""
    if DB_PATH.exists():
        return
    con = sqlite3.connect(DB_PATH)
    pd.read_csv(ROOT / "data" / "ola_rides_clean.csv").to_sql("ola_rides", con, index=False)
    con.close()


def _connect() -> sqlite3.Connection:
    """Read-only connection: SQL typed in the app can never modify data."""
    _ensure_db()
    return sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)


@st.cache_data(show_spinner="Loading rides...")
def load_data() -> pd.DataFrame:
    con = _connect()
    d = pd.read_sql("SELECT * FROM ola_rides", con, parse_dates=["Date"])
    con.close()
    return d


@st.cache_data
def vehicle_icons() -> dict:
    p = ROOT / "data" / "vehicle_images.csv"
    return dict(pd.read_csv(p).values) if p.exists() else {}


@st.cache_data
def load_queries() -> dict:
    """Parse sql/ola_queries.sql -> {'Q1': (question, sql), ...}"""
    parts = re.split(r"(?m)^-- (Q\d+)\. ", SQL_FILE.read_text(encoding="utf-8"))[1:]
    out = {}
    for key, body in zip(parts[0::2], parts[1::2]):
        question, sql = body.split("\n", 1)
        out[key] = (question.strip(), sql.strip().rstrip(";"))
    return out


@st.cache_data(show_spinner=False)
def run_sql(sql: str) -> pd.DataFrame:
    con = _connect()
    try:
        return pd.read_sql(sql, con)
    finally:
        con.close()


df_all = load_data()

# ------------------------------------------------------------------ sidebar
PAGES = {
    "🏠 Overview": "overview", "📈 Overall": "overall", "🚗 Vehicle Type": "vehicle",
    "💰 Revenue": "revenue", "❌ Cancellation": "cancel", "⭐ Ratings": "ratings",
    "🧮 SQL Queries": "sql", "📊 Power BI Dashboard": "powerbi",
    "🔍 Insights & Anomalies": "insights", "📁 Data Explorer": "explorer",
}
st.sidebar.title("🚖 OLA Ride Insights")
page = PAGES[st.sidebar.radio("Go to", list(PAGES))]

st.sidebar.divider()
st.sidebar.header("Filters")
dmin, dmax = df_all["Date"].min().date(), df_all["Date"].max().date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
all_veh = sorted(df_all["Vehicle_Type"].unique())
all_stat = sorted(df_all["Booking_Status"].unique())
vehicles = st.sidebar.multiselect("Vehicle type", all_veh, default=all_veh)
statuses = st.sidebar.multiselect("Booking status", all_stat, default=all_stat)
payments = st.sidebar.multiselect("Payment method (successful rides)",
                                  sorted(df_all["Payment_Method"].dropna().unique()))
pickups = st.sidebar.multiselect("Pickup location (blank = all)", sorted(df_all["Pickup_Location"].unique()))

mask = pd.Series(True, index=df_all.index)
if isinstance(date_range, tuple) and len(date_range) == 2:
    mask &= df_all["Date"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
if vehicles:
    mask &= df_all["Vehicle_Type"].isin(vehicles)
if statuses:
    mask &= df_all["Booking_Status"].isin(statuses)
if payments:  # payment only exists for successful rides, so it narrows those and leaves the rest alone
    mask &= df_all["Payment_Method"].isna() | df_all["Payment_Method"].isin(payments)
if pickups:
    mask &= df_all["Pickup_Location"].isin(pickups)
df = df_all[mask]
success = df[df["Booking_Status"] == "Success"]

st.sidebar.caption(f"Showing **{len(df):,}** of {len(df_all):,} bookings")
st.sidebar.caption("Filters apply to the dashboard pages. The SQL page queries the full table.")


# ------------------------------------------------------------------ helpers
def need_data() -> bool:
    if df.empty:
        st.warning("No rides match the current filters.")
        return False
    return True


def kpis(items, per_row=4):
    for i in range(0, len(items), per_row):
        chunk = items[i:i + per_row]
        for col, (label, value) in zip(st.columns(per_row), chunk):
            col.metric(label, value)


def money(x: float) -> str:
    return f"₹{x / 1e6:,.2f} M" if x >= 1e6 else f"₹{x:,.0f}"


def style(fig, h=380):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=50, b=10), legend_title_text="",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def show(fig, h=380):
    st.plotly_chart(style(fig, h), width="stretch")


def hbar(data, x, y, title, **kw):
    fig = px.bar(data, x=x, y=y, orientation="h", text_auto=kw.pop("text_auto", ",.0f"), title=title, **kw)
    fig.update_yaxes(categoryorder="total ascending", title="")
    return fig


# ------------------------------------------------------------------ pages
def page_overview():
    st.title("OLA Ride Insights — Bengaluru, July 2024")
    st.markdown(f"Interactive analysis of **{len(df_all) / 1000:,.0f}K OLA bookings**: demand patterns, revenue, "
                "cancellations and ratings. Use the sidebar to filter every chart.")
    if not need_data():
        return
    total = len(df)
    s = success
    kpis([
        ("Total bookings", f"{total:,}"),
        ("Success rate", f"{len(s) / total:.1%}"),
        ("Revenue (successful)", money(s["Booking_Value"].sum())),
        ("Avg fare / ride", f"₹{s['Booking_Value'].mean():,.0f}" if len(s) else "–"),
        ("Cancellation rate", f"{df['Booking_Status'].str.startswith('Canceled').mean():.1%}"),
        ("Avg ride distance", f"{s['Ride_Distance'].mean():.1f} km" if len(s) else "–"),
        ("Avg driver rating", f"{s['Driver_Ratings'].mean():.2f}" if len(s) else "–"),
        ("Avg customer rating", f"{s['Customer_Rating'].mean():.2f}" if len(s) else "–"),
    ])

    st.header("Snapshot")
    c1, c2 = st.columns([3, 2])
    d = df.groupby("Date").size().reset_index(name="Rides")
    fig = px.area(d, x="Date", y="Rides", title="Daily ride volume", color_discrete_sequence=[GREEN])
    fig.update_yaxes(rangemode="tozero")
    with c1:
        show(fig)
    d = df["Booking_Status"].value_counts().reset_index()
    with c2:
        show(px.pie(d, names="Booking_Status", values="count", hole=0.55, title="Booking status",
                    color="Booking_Status", color_discrete_map=STATUS_COLORS))

    st.subheader("Quick takeaways")
    hr = df.groupby("Hour").size()
    cust = df[df["Booking_Status"] == "Canceled by Customer"]["Canceled_Rides_by_Customer"].mode()
    drv = df[df["Booking_Status"] == "Canceled by Driver"]["Canceled_Rides_by_Driver"].mode()
    lines = [f"Busiest hour is **{hr.idxmax()}:00** ({hr.max():,} bookings); quietest is **{hr.idxmin()}:00**."]
    if len(s):
        pay = s.groupby("Payment_Method")["Booking_Value"].sum()
        lines.append(f"**{pay.idxmax()}** brings in the most revenue ({pay.max() / pay.sum():.0%} of successful bookings).")
    if len(cust):
        lines.append(f"Top customer cancellation reason: **{cust.iloc[0]}**.")
    if len(drv):
        lines.append(f"Top driver cancellation reason: **{drv.iloc[0]}**.")
    st.markdown("\n".join(f"- {x}" for x in lines))


def page_overall():
    st.title("Overall")
    if not need_data():
        return
    c1, c2 = st.columns([3, 2])
    with c1:
        by = st.radio("Ride volume split", ["Total", "By booking status"], horizontal=True)
        if by == "Total":
            d = df.groupby("Date").size().reset_index(name="Rides")
            fig = px.line(d, x="Date", y="Rides", markers=True, title="Ride volume over time")
        else:
            d = df.groupby(["Date", "Booking_Status"]).size().reset_index(name="Rides")
            fig = px.line(d, x="Date", y="Rides", color="Booking_Status", title="Ride volume over time",
                          color_discrete_map=STATUS_COLORS)
        fig.update_yaxes(rangemode="tozero")
        show(fig)
    with c2:
        d = df["Booking_Status"].value_counts().reset_index()
        show(px.pie(d, names="Booking_Status", values="count", hole=0.55, title="Booking status breakdown",
                    color="Booking_Status", color_discrete_map=STATUS_COLORS))

    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heat = df.groupby(["Day_Name", "Hour"]).size().unstack(fill_value=0).reindex(order)
    show(px.imshow(heat, aspect="auto", color_continuous_scale="Viridis",
                   labels=dict(x="Hour of day", y="", color="Rides"), title="Booking demand by weekday and hour"), 340)


def page_vehicle():
    st.title("Vehicle Type")
    if not need_data():
        return
    g = df.groupby("Vehicle_Type").agg(Bookings=("Booking_ID", "count"), Total_Distance=("Ride_Distance", "sum")).reset_index()
    s = success.groupby("Vehicle_Type").agg(Avg_Distance=("Ride_Distance", "mean"), Revenue=("Booking_Value", "sum")).reset_index()
    g = g.merge(s, on="Vehicle_Type", how="left").fillna(0)

    c1, c2 = st.columns(2)
    with c1:
        show(hbar(g.nlargest(5, "Total_Distance"), "Total_Distance", "Vehicle_Type",
                  "Top 5 vehicle types by total ride distance (km)"))
    with c2:
        show(px.bar(g.sort_values("Avg_Distance", ascending=False), x="Vehicle_Type", y="Avg_Distance",
                    text_auto=".1f", title="Average distance per completed ride (km)"))

    st.subheader("Fleet scorecard")
    icons = vehicle_icons()
    ranked = g.sort_values("Total_Distance", ascending=False)
    for col, (_, r) in zip(st.columns(len(ranked)), ranked.iterrows()):
        with col:
            if r["Vehicle_Type"] in icons:
                st.image(icons[r["Vehicle_Type"]], width=48)
            st.markdown(f"**{r['Vehicle_Type']}**")
            st.caption(f"{int(r['Bookings']):,} bookings\n\n{r['Total_Distance']:,.0f} km\n\n{money(r['Revenue'])}")


def page_revenue():
    st.title("Revenue")
    if not need_data():
        return
    if success.empty:
        st.warning("No successful rides in the current selection.")
        return
    kpis([("Total revenue", money(success["Booking_Value"].sum())),
          ("Avg booking value", f"₹{success['Booking_Value'].mean():,.0f}"),
          ("Total distance", f"{success['Ride_Distance'].sum():,.0f} km"),
          ("Revenue per km", f"₹{success['Booking_Value'].sum() / max(success['Ride_Distance'].sum(), 1):,.1f}")])
    c1, c2 = st.columns(2)
    pay = success.groupby("Payment_Method")["Booking_Value"].sum().reset_index().sort_values("Booking_Value", ascending=False)
    with c1:
        show(px.bar(pay, x="Payment_Method", y="Booking_Value", text_auto=".3s", title="Revenue by payment method"))
    cust = success.groupby("Customer_ID")["Booking_Value"].sum().nlargest(5).reset_index()
    with c2:
        show(hbar(cust, "Booking_Value", "Customer_ID", "Top 5 customers by total booking value"))

    st.subheader("Ride distance per day")
    view = st.radio("View", ["Daily total distance", "Distribution of ride distances"], horizontal=True)
    if view == "Daily total distance":
        d = success.groupby("Date")["Ride_Distance"].sum().reset_index()
        fig = px.bar(d, x="Date", y="Ride_Distance", title="Total ride distance per day (km)")
        fig.add_hline(y=d["Ride_Distance"].mean(), line_dash="dash", line_color=AMBER, annotation_text="daily average")
    else:
        fig = px.histogram(success, x="Ride_Distance", nbins=25, title="Distribution of ride distance (km)")
    show(fig)


def page_cancel():
    st.title("Cancellation")
    if not need_data():
        return
    cancelled = df[df["Booking_Status"].str.startswith("Canceled")]
    kpis([("Cancelled by customers", f"{(df['Booking_Status'] == 'Canceled by Customer').sum():,}"),
          ("Cancelled by drivers", f"{(df['Booking_Status'] == 'Canceled by Driver').sum():,}"),
          ("Driver not found", f"{(df['Booking_Status'] == 'Driver Not Found').sum():,}"),
          ("Revenue at risk", money(df.loc[df["Booking_Status"] != "Success", "Booking_Value"].sum()))])

    c1, c2 = st.columns(2)
    for col, field, title in [(c1, "Canceled_Rides_by_Customer", "Cancellation reasons - customers"),
                              (c2, "Canceled_Rides_by_Driver", "Cancellation reasons - drivers")]:
        d = df[field].dropna().value_counts().reset_index()
        d.columns = ["Reason", "Rides"]
        with col:
            if d.empty:
                st.info("No data for the current filters.")
            else:
                show(hbar(d, "Rides", "Reason", title, text_auto=","))
    c3, c4 = st.columns(2)
    inc = df[df["Incomplete_Rides"] == "Yes"]["Incomplete_Rides_Reason"].value_counts().reset_index()
    inc.columns = ["Reason", "Rides"]
    with c3:
        if not inc.empty:
            show(px.pie(inc, names="Reason", values="Rides", hole=0.5, title="Incomplete rides by reason"))
    v = cancelled.groupby(["Vehicle_Type", "Booking_Status"]).size().reset_index(name="Rides")
    with c4:
        if not v.empty:
            show(px.bar(v, x="Vehicle_Type", y="Rides", color="Booking_Status", barmode="stack",
                        title="Cancellations by vehicle type", color_discrete_map=STATUS_COLORS))


def page_ratings():
    st.title("Ratings")
    r = success.dropna(subset=["Driver_Ratings", "Customer_Rating"])
    if r.empty:
        st.warning("No rated rides in the current selection.")
        return
    kpis([("Avg driver rating", f"{r['Driver_Ratings'].mean():.2f}"),
          ("Avg customer rating", f"{r['Customer_Rating'].mean():.2f}"),
          ("Rated rides", f"{len(r):,}"),
          ("Driver ratings ≤ 3.5", f"{(r['Driver_Ratings'] <= 3.5).mean():.1%}")])
    c1, c2 = st.columns(2)
    with c1:
        show(px.histogram(r, x="Driver_Ratings", nbins=21, title="Driver ratings distribution"))
    with c2:
        show(px.histogram(r, x="Customer_Rating", nbins=21, title="Customer ratings distribution",
                          color_discrete_sequence=[AMBER]))
    c3, c4 = st.columns(2)
    avg = r.groupby("Vehicle_Type")[["Driver_Ratings", "Customer_Rating"]].mean().reset_index().melt(
        id_vars="Vehicle_Type", var_name="Rating type", value_name="Average")
    fig = px.bar(avg, x="Vehicle_Type", y="Average", color="Rating type", barmode="group", text_auto=".2f",
                 title="Average rating by vehicle type")
    fig.update_yaxes(range=[3, 5])
    with c3:
        show(fig)
    with c4:
        show(px.density_heatmap(r, x="Customer_Rating", y="Driver_Ratings", nbinsx=21, nbinsy=21,
                                color_continuous_scale="Viridis", title="Customer vs driver ratings"))
    st.caption(f"Correlation between customer and driver ratings: {r['Customer_Rating'].corr(r['Driver_Ratings']):+.3f}")


def page_sql():
    st.title("SQL Queries")
    st.caption("The ten project queries from `sql/ola_queries.sql`, run live against the database.")
    queries = load_queries()
    key = st.selectbox("Choose a question", list(queries), format_func=lambda k: f"{k}. {queries[k][0]}")
    _, sql = queries[key]
    st.code(sql + ";", language="sql")
    res = run_sql(sql)
    st.write(f"**{len(res):,} row(s)**")
    if len(res) == 1 and res.shape[1] <= 2:
        for col, (name, val) in zip(st.columns(res.shape[1]), res.iloc[0].items()):
            col.metric(name.replace("_", " "), f"{val:,}" if isinstance(val, (int, float)) else val)
    else:
        q = st.text_input("Search within results")
        view = res[res.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)] if q else res
        st.dataframe(view.head(1000), width="stretch", hide_index=True)
        if len(view) > 1000:
            st.caption(f"Showing first 1,000 of {len(view):,} rows - download for the full set.")
    st.download_button("Download result (CSV)", res.to_csv(index=False), f"{key}_result.csv", "text/csv")

    with st.expander("Run your own SQL (read-only)"):
        st.caption("Table `ola_rides`. Columns: " + ", ".join(df_all.columns))
        custom = st.text_area("SELECT query", "SELECT Vehicle_Type, COUNT(*) AS rides\nFROM ola_rides\nGROUP BY Vehicle_Type;", height=130)
        if st.button("Run query"):
            if not re.match(r"(?is)^\s*(select|with)\b", custom):
                st.error("Only SELECT queries are allowed.")
            else:
                try:
                    st.dataframe(run_sql(custom.strip().rstrip(";")).head(1000), width="stretch", hide_index=True)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Query failed: {e}")


def page_powerbi():
    st.title("Power BI Dashboard")
    try:
        url = st.secrets["POWERBI_URL"]
    except Exception:  # noqa: BLE001
        url = ""
    url = st.text_input("Power BI 'Publish to web' embed URL", url, placeholder="https://app.powerbi.com/view?r=...")
    if url.startswith("https://app.powerbi.com/"):
        st.components.v1.iframe(url, height=720, scrolling=True)
    else:
        st.info("Paste your report's embed link above, or set `POWERBI_URL` in `.streamlit/secrets.toml` "
                "(Streamlit Cloud: App settings → Secrets) so it loads automatically.")
        st.markdown("**How to get the link:** open the report in Power BI Service → *File → Embed report → "
                    "Publish to web (public)* → copy the link. Build steps: `powerbi/DASHBOARD_GUIDE.md`.")


def page_insights():
    st.title("Insights & Anomalies")
    st.caption("Business use cases from the brief: peak demand, pricing patterns and unusual activity.")
    if not need_data():
        return
    t1, t2, t3 = st.tabs(["Peak demand & driver allocation", "Pricing patterns", "Anomaly detection"])

    with t1:
        h = df.groupby("Hour").agg(Bookings=("Booking_ID", "size"),
                                   No_driver_rate=("Booking_Status", lambda x: (x == "Driver Not Found").mean()),
                                   Driver_cancel_rate=("Booking_Status", lambda x: (x == "Canceled by Driver").mean())).reset_index()
        c1, c2 = st.columns(2)
        with c1:
            show(px.bar(h, x="Hour", y="Bookings", title="Bookings by hour"))
        with c2:
            m = h.melt("Hour", ["No_driver_rate", "Driver_cancel_rate"], var_name="Metric", value_name="Rate")
            m["Metric"] = m["Metric"].map({"No_driver_rate": "Driver not found", "Driver_cancel_rate": "Cancelled by driver"})
            fig = px.line(m, x="Hour", y="Rate", color="Metric", title="Supply stress by hour")
            fig.update_yaxes(tickformat=".0%")
            show(fig)
        top = h.nlargest(3, "Bookings")
        worst = h.nlargest(3, "No_driver_rate")
        spread = h["Bookings"].max() / max(h["Bookings"].min(), 1) - 1
        if spread < 0.15:
            st.warning(f"Demand is nearly flat across the day (busiest hour is only {spread:.0%} above the quietest), "
                       "so staffing should be roughly even; the busiest hours are still listed below.")
        st.info("**Busiest hours (prioritise drivers):** " + ", ".join(f"{int(x)}:00" for x in top["Hour"])
                + ". **Highest unmet demand (no driver found):** "
                + ", ".join(f"{int(r.Hour)}:00 ({r.No_driver_rate:.1%})" for r in worst.itertuples()) + ".")

    with t2:
        if success.empty:
            st.warning("No successful rides in the current selection.")
        else:
            p = success[success["Ride_Distance"] > 0].copy()
            p["Fare_per_km"] = p["Booking_Value"] / p["Ride_Distance"]
            c1, c2 = st.columns(2)
            by_h = p.groupby("Hour")["Fare_per_km"].mean().reset_index()
            with c1:
                show(px.line(by_h, x="Hour", y="Fare_per_km", markers=True, title="Average fare per km by hour (surge proxy)"))
            by_v = p.groupby("Vehicle_Type")["Fare_per_km"].mean().reset_index().sort_values("Fare_per_km", ascending=False)
            with c2:
                show(px.bar(by_v, x="Vehicle_Type", y="Fare_per_km", text_auto=".1f", title="Average fare per km by vehicle type"))
            b = df.copy()
            b["Fare band"] = pd.qcut(b["Booking_Value"], 5, duplicates="drop")
            b["Fare band"] = b["Fare band"].astype(str)
            sr = b.groupby("Fare band", observed=True).agg(Success_rate=("Is_Success", "mean"),
                                                           low=("Booking_Value", "min")).reset_index().sort_values("low")
            fig = px.bar(sr, x="Fare band", y="Success_rate", text_auto=".1%", title="Success rate by booking-value band (price sensitivity)")
            fig.update_yaxes(tickformat=".0%", rangemode="tozero")
            show(fig, 320)
            spread = sr["Success_rate"].max() - sr["Success_rate"].min()
            st.info(f"Success rate varies by only {spread:.1%} across price bands, so booking value is **not** "
                    "a strong driver of completion in this data - surge pricing has little visible effect on conversion.")

    with t3:
        st.subheader("Unusual daily volume")
        dv = df.groupby("Date").size()
        z = (dv - dv.mean()) / dv.std(ddof=0)
        out = pd.DataFrame({"Rides": dv, "Z-score": z.round(2)}).reindex(z.abs().sort_values(ascending=False).index).head(5)
        out.index = out.index.date
        st.dataframe(out, width="stretch")
        st.caption("|z| above 2 would indicate an abnormal day; the five largest deviations are shown.")

        st.subheader("Repeat cancellers (customers)")
        thr = st.slider("Minimum customer-initiated cancellations", 1, 4, 2)
        cc = (df[df["Booking_Status"] == "Canceled by Customer"].groupby("Customer_ID").size()
              .rename("Cancellations").reset_index())
        cc = cc[cc["Cancellations"] >= thr].sort_values("Cancellations", ascending=False)
        st.write(f"**{len(cc):,}** customers")
        st.dataframe(cc.head(200), width="stretch", hide_index=True)

        st.subheader("Fare-per-km outliers (possible pricing errors or fraud)")
        if success.empty:
            st.warning("No successful rides in the current selection.")
        else:
            p = success[success["Ride_Distance"] > 0].copy()
            p["Fare_per_km"] = (p["Booking_Value"] / p["Ride_Distance"]).round(1)
            pct = st.slider("Flag the top x% highest fare-per-km rides", 0.1, 5.0, 1.0, 0.1)
            cut = p["Fare_per_km"].quantile(1 - pct / 100)
            flagged = p[p["Fare_per_km"] >= cut].sort_values("Fare_per_km", ascending=False)
            st.write(f"**{len(flagged):,}** rides at or above ₹{cut:,.0f}/km")
            st.dataframe(flagged[["Booking_ID", "Customer_ID", "Vehicle_Type", "Ride_Distance", "Booking_Value", "Fare_per_km"]].head(200),
                         width="stretch", hide_index=True)

        st.subheader("Data-integrity flag")
        inc = df[(df["Booking_Status"] == "Success") & (df["Incomplete_Rides"] == "Yes")]
        st.write(f"**{len(inc):,}** bookings are marked *Success* but also *Incomplete* "
                 f"({len(inc) / max(len(success), 1):.1%} of successful rides) - these are paid-for trips that did not finish "
                 "and are worth reviewing for refunds or fraud.")
        st.dataframe(inc[["Booking_ID", "Customer_ID", "Vehicle_Type", "Booking_Value", "Incomplete_Rides_Reason"]].head(200),
                     width="stretch", hide_index=True)


def page_explorer():
    st.title("Data Explorer")
    if not need_data():
        return
    c1, c2, c3 = st.columns(3)
    bid = c1.text_input("Booking ID contains")
    cid = c2.text_input("Customer ID contains")
    loc = c3.text_input("Pickup / drop location contains")
    v = df
    if bid:
        v = v[v["Booking_ID"].str.contains(bid, case=False, na=False)]
    if cid:
        v = v[v["Customer_ID"].str.contains(cid, case=False, na=False)]
    if loc:
        v = v[v["Pickup_Location"].str.contains(loc, case=False, na=False) | v["Drop_Location"].str.contains(loc, case=False, na=False)]
    st.write(f"**{len(v):,}** rides match")
    st.dataframe(v.assign(Date=v["Date"].dt.date).head(2000), width="stretch", hide_index=True)
    st.download_button("Download filtered rides (CSV)", v.to_csv(index=False), "ola_filtered.csv", "text/csv")


{"overview": page_overview, "overall": page_overall, "vehicle": page_vehicle, "revenue": page_revenue,
 "cancel": page_cancel, "ratings": page_ratings, "sql": page_sql, "powerbi": page_powerbi,
 "insights": page_insights, "explorer": page_explorer}[page]()

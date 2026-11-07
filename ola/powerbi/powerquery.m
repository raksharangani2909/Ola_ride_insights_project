// Power BI > Get data > Blank query > Advanced editor. Replace the path.
let
    Source   = Csv.Document(File.Contents("C:\path\to\ola_rides_clean.csv"),
                 [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
        {"Date", type date}, {"Time", type time}, {"Ride_Datetime", type datetime},
        {"Booking_ID", type text}, {"Booking_Status", type text}, {"Customer_ID", type text},
        {"Vehicle_Type", type text}, {"Pickup_Location", type text}, {"Drop_Location", type text},
        {"V_TAT", type number}, {"C_TAT", type number},
        {"Canceled_Rides_by_Customer", type text}, {"Canceled_Rides_by_Driver", type text},
        {"Incomplete_Rides", type text}, {"Incomplete_Rides_Reason", type text},
        {"Booking_Value", Int64.Type}, {"Payment_Method", type text}, {"Ride_Distance", Int64.Type},
        {"Driver_Ratings", type number}, {"Customer_Rating", type number},
        {"Hour", Int64.Type}, {"Day_Of_Month", Int64.Type}, {"Day_Name", type text},
        {"Week_Number", Int64.Type}, {"Is_Weekend", Int64.Type}, {"Time_Of_Day", type text},
        {"Is_Success", Int64.Type}, {"Revenue", Int64.Type}, {"Distance_Bucket", type text}})
in
    Typed
// MySQL alternative: Get data > MySQL database > server / "ola_project" > table ola_rides

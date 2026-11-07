-- =====================================================================
-- OLA RIDE INSIGHTS - SQL QUERIES
-- Table : ola_rides   (built from data/ola_rides_clean.csv)
-- Dialect: ANSI SQL - runs unchanged on MySQL 8 and SQLite.
-- Format : every query starts with "-- Qn. <question>" (the Streamlit
--          app reads this file and lists each query automatically).
-- =====================================================================

-- Q1. Retrieve all successful bookings
SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';

-- Q2. Find the average ride distance for each vehicle type
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Ride_Distance_Km
FROM ola_rides
GROUP BY Vehicle_Type
ORDER BY Avg_Ride_Distance_Km DESC;

-- Q3. Get the total number of cancelled rides by customers
SELECT COUNT(*) AS Total_Cancelled_By_Customers
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';

-- Q4. List the top 5 customers who booked the highest number of rides
SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;

-- Q5. Get the number of rides cancelled by drivers due to personal and car-related issues
SELECT COUNT(*) AS Driver_Cancels_Personal_Car_Issue
FROM ola_rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';

-- Q6. Find the maximum and minimum driver ratings for Prime Sedan bookings
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Driver_Ratings IS NOT NULL;

-- Q7. Retrieve all rides where payment was made using UPI
SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';

-- Q8. Find the average customer rating per vehicle type
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;

-- Q9. Calculate the total booking value of rides completed successfully
SELECT SUM(Booking_Value) AS Total_Booking_Value
FROM ola_rides
WHERE Booking_Status = 'Success';

-- Q10. List all incomplete rides along with the reason
SELECT Booking_ID,
       Customer_ID,
       Vehicle_Type,
       Incomplete_Rides,
       Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes'
ORDER BY Incomplete_Rides_Reason, Booking_ID;

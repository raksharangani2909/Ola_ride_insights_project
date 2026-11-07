-- MySQL 8 schema + load script (use this if you connect Power BI to MySQL)
CREATE DATABASE IF NOT EXISTS ola_project;
USE ola_project;

DROP TABLE IF EXISTS ola_rides;
CREATE TABLE ola_rides (
    Date                         DATE,
    Time                         TIME,
    Booking_ID                   VARCHAR(20) PRIMARY KEY,
    Booking_Status               VARCHAR(25),
    Customer_ID                  VARCHAR(15),
    Vehicle_Type                 VARCHAR(20),
    Pickup_Location              VARCHAR(60),
    Drop_Location                VARCHAR(60),
    V_TAT                        DECIMAL(8,2) NULL,
    C_TAT                        DECIMAL(8,2) NULL,
    Canceled_Rides_by_Customer   VARCHAR(60) NULL,
    Canceled_Rides_by_Driver     VARCHAR(60) NULL,
    Incomplete_Rides             VARCHAR(5)  NULL,
    Incomplete_Rides_Reason      VARCHAR(30) NULL,
    Booking_Value                INT,
    Payment_Method               VARCHAR(15) NULL,
    Ride_Distance                INT,
    Driver_Ratings               DECIMAL(3,1) NULL,
    Customer_Rating              DECIMAL(3,1) NULL,
    Ride_Datetime                DATETIME,
    Hour                         TINYINT,
    Day_Of_Month                 TINYINT,
    Day_Name                     VARCHAR(10),
    Week_Number                  TINYINT,
    Is_Weekend                   TINYINT,
    Time_Of_Day                  VARCHAR(25),
    Is_Success                   TINYINT,
    Revenue                      INT,
    Distance_Bucket              VARCHAR(15),
    INDEX idx_status (Booking_Status),
    INDEX idx_vehicle (Vehicle_Type),
    INDEX idx_customer (Customer_ID),
    INDEX idx_date (Date)
);

-- Empty cells in the CSV become NULL (the NULLIF / @var pattern handles that).
LOAD DATA LOCAL INFILE 'data/ola_rides_clean.csv'
INTO TABLE ola_rides
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(Date, Time, Booking_ID, Booking_Status, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location,
 @v_tat, @c_tat, @cc, @cd, @inc, @incr, Booking_Value, @pay, Ride_Distance, @dr, @cr,
 Ride_Datetime, Hour, Day_Of_Month, Day_Name, Week_Number, Is_Weekend, Time_Of_Day, Is_Success, Revenue, Distance_Bucket)
SET V_TAT = NULLIF(@v_tat,''), C_TAT = NULLIF(@c_tat,''),
    Canceled_Rides_by_Customer = NULLIF(@cc,''), Canceled_Rides_by_Driver = NULLIF(@cd,''),
    Incomplete_Rides = NULLIF(@inc,''), Incomplete_Rides_Reason = NULLIF(@incr,''),
    Payment_Method = NULLIF(@pay,''), Driver_Ratings = NULLIF(@dr,''), Customer_Rating = NULLIF(@cr,'');
-- If LOAD DATA is blocked: SET GLOBAL local_infile = 1; and connect with --local-infile=1,
-- or use MySQL Workbench > Table Data Import Wizard.

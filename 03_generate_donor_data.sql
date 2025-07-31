-- Higher Education Alumni Targeting Demo - Generate Alumni Donor Data
-- This script generates 10,000 realistic alumni donor records
-- 70% from target zip codes: 29680, 29650, 29607, 29681

USE DATABASE HIGHER_ED_DEMO;
USE SCHEMA ALUMNI_TARGETING;

-- Create actual tables for Greenville County addresses with focus on target zip codes
-- Using the specified address database: US_POINTS_OF_INTEREST__ADDRESSES.cybersyn.us_addresses

-- Create table for target zip code addresses (70% of our data)
CREATE OR REPLACE TABLE TARGET_ZIP_ADDRESSES AS
SELECT 
    ADDRESS_ID,
    CITY,
    STATE,
    ZIP,
    LATITUDE,
    LONGITUDE,
    COALESCE(STREET, '') || ' ' || COALESCE(NUMBER, '') AS STREET_ADDRESS,
    'TARGET' AS ADDRESS_TYPE
FROM US_POINTS_OF_INTEREST__ADDRESSES.cybersyn.us_addresses
WHERE STATE = 'SC' 
-- AND CITY = 'GREENVILLE'  -- Commented out - city filtering can be inconsistent
AND ZIP IN ('29680', '29650', '29607', '29681')
AND LATITUDE IS NOT NULL 
AND LONGITUDE IS NOT NULL
LIMIT 7000;  -- 70% of 10,000

-- Create table for other Greenville County addresses (30% of our data)
CREATE OR REPLACE TABLE OTHER_GREENVILLE_ADDRESSES AS
SELECT 
    ADDRESS_ID,
    CITY,
    STATE,
    ZIP,
    LATITUDE,
    LONGITUDE,
    COALESCE(STREET, '') || ' ' || COALESCE(NUMBER, '') AS STREET_ADDRESS,
    'OTHER' AS ADDRESS_TYPE
FROM US_POINTS_OF_INTEREST__ADDRESSES.cybersyn.us_addresses
WHERE STATE = 'SC' 
-- AND (CITY = 'GREENVILLE' OR CITY LIKE '%GREENVILLE%')  -- Commented out - using zip codes instead
AND ZIP IN ('29601', '29602', '29603', '29604', '29605', '29606', '29608', '29609', '29610', '29611', '29612', '29613', '29614', '29615', '29616', '29617', '29635', '29636', '29644', '29651', '29652', '29661', '29662', '29673', '29683', '29687', '29688', '29690')
AND LATITUDE IS NOT NULL 
AND LONGITUDE IS NOT NULL
LIMIT 3000;  -- 30% of 10,000

-- Create combined table for all Greenville addresses
CREATE OR REPLACE TABLE GREENVILLE_ADDRESSES AS
SELECT * FROM TARGET_ZIP_ADDRESSES
UNION ALL
SELECT * FROM OTHER_GREENVILLE_ADDRESSES;

-- Create arrays for generating realistic data
CREATE OR REPLACE VIEW DEMO_DATA_ARRAYS AS
SELECT
    ARRAY_CONSTRUCT(
        'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Christopher',
        'Charles', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua',
        'Kenneth', 'Kevin', 'Brian', 'George', 'Edward', 'Ronald', 'Timothy', 'Jason', 'Jeffrey', 'Ryan',
        'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
        'Nancy', 'Lisa', 'Betty', 'Helen', 'Sandra', 'Donna', 'Carol', 'Ruth', 'Sharon', 'Michelle',
        'Laura', 'Sarah', 'Kimberly', 'Deborah', 'Dorothy', 'Lisa', 'Nancy', 'Karen', 'Betty', 'Helen'
    ) AS FIRST_NAMES,
    
    ARRAY_CONSTRUCT(
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
        'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
        'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
        'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
        'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts'
    ) AS LAST_NAMES,
    
    ARRAY_CONSTRUCT(
        'Business Administration', 'Engineering', 'Liberal Arts', 'Education', 'Nursing', 'Computer Science',
        'Psychology', 'Biology', 'English', 'History', 'Political Science', 'Economics', 'Marketing',
        'Accounting', 'Finance', 'Communications', 'Sociology', 'Chemistry', 'Mathematics', 'Art'
    ) AS MAJORS,
    
    ARRAY_CONSTRUCT(
        'Bachelor of Arts', 'Bachelor of Science', 'Master of Arts', 'Master of Science', 
        'Master of Business Administration', 'Doctor of Philosophy', 'Juris Doctor', 'Master of Education'
    ) AS DEGREE_TYPES;

-- Generate the alumni donor data
INSERT INTO ALUMNI_DONORS (
    DONOR_ID,
    FIRST_NAME,
    LAST_NAME,
    FULL_NAME,
    EMAIL,
    ADDRESS_ID,
    STREET_ADDRESS,
    CITY,
    STATE,
    ZIP_CODE,
    LATITUDE,
    LONGITUDE,
    GRADUATION_YEAR,
    DEGREE_TYPE,
    MAJOR,
    AGE,
    ANNUAL_DONATION_AMOUNT,
    CUMULATIVE_DONATION_AMOUNT,
    LAST_DONATION_DATE,
    DONOR_SEGMENT,
    H3_LEVEL_7,
    H3_LEVEL_8,
    H3_LEVEL_9
)
WITH numbered_addresses AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
    FROM GREENVILLE_ADDRESSES
    LIMIT 10000
),
donor_base AS (
    SELECT
        rn,
        'DONOR_' || LPAD(rn, 5, '0') AS DONOR_ID,
        (SELECT FIRST_NAMES FROM DEMO_DATA_ARRAYS)[UNIFORM(1, 60, RANDOM())] AS FIRST_NAME,
        (SELECT LAST_NAMES FROM DEMO_DATA_ARRAYS)[UNIFORM(1, 50, RANDOM())] AS LAST_NAME,
        ADDRESS_ID,
        STREET_ADDRESS,
        CITY,
        STATE,
        ZIP,
        LATITUDE,
        LONGITUDE,
        -- Graduation year between 1990-2024, weighted toward more recent years
        CASE 
            WHEN UNIFORM(1, 100, RANDOM()) <= 20 THEN UNIFORM(1990, 2000, RANDOM())
            WHEN UNIFORM(1, 100, RANDOM()) <= 50 THEN UNIFORM(2000, 2010, RANDOM())
            WHEN UNIFORM(1, 100, RANDOM()) <= 80 THEN UNIFORM(2010, 2020, RANDOM())
            ELSE UNIFORM(2020, 2024, RANDOM())
        END AS GRADUATION_YEAR,
        (SELECT DEGREE_TYPES FROM DEMO_DATA_ARRAYS)[UNIFORM(1, 8, RANDOM())] AS DEGREE_TYPE,
        (SELECT MAJORS FROM DEMO_DATA_ARRAYS)[UNIFORM(1, 20, RANDOM())] AS MAJOR
    FROM numbered_addresses
),
donor_with_calculated_fields AS (
    SELECT
        *,
        FIRST_NAME || ' ' || LAST_NAME AS FULL_NAME,
        LOWER(FIRST_NAME || '.' || LAST_NAME || '@clemson.edu') AS EMAIL,
        2024 - GRADUATION_YEAR + 22 AS AGE,  -- Assuming graduated at 22
        
        -- Annual donation amount - older grads generally give more
        CASE 
            WHEN 2024 - GRADUATION_YEAR >= 25 THEN  -- 25+ years out
                ROUND(UNIFORM(500, 50000, RANDOM()) * 
                      (1 + (2024 - GRADUATION_YEAR - 25) * 0.02), 2)  -- 2% increase per year beyond 25
            WHEN 2024 - GRADUATION_YEAR >= 15 THEN  -- 15-24 years out
                ROUND(UNIFORM(250, 25000, RANDOM()) * 
                      (1 + (2024 - GRADUATION_YEAR - 15) * 0.03), 2)  -- 3% increase per year beyond 15
            WHEN 2024 - GRADUATION_YEAR >= 5 THEN   -- 5-14 years out
                ROUND(UNIFORM(100, 10000, RANDOM()) * 
                      (1 + (2024 - GRADUATION_YEAR - 5) * 0.05), 2)   -- 5% increase per year beyond 5
            ELSE  -- Recent grads (0-4 years out)
                ROUND(UNIFORM(25, 2500, RANDOM()), 2)
        END AS ANNUAL_DONATION_AMOUNT
    FROM donor_base
)
SELECT
    DONOR_ID,
    FIRST_NAME,
    LAST_NAME,
    FULL_NAME,
    EMAIL,
    ADDRESS_ID,
    STREET_ADDRESS,
    CITY,
    STATE,
    ZIP AS ZIP_CODE,
    LATITUDE,
    LONGITUDE,
    GRADUATION_YEAR,
    DEGREE_TYPE,
    MAJOR,
    AGE,
    ANNUAL_DONATION_AMOUNT,
    -- Cumulative donation amount (typically 8-15x annual amount based on giving years)
    ROUND(ANNUAL_DONATION_AMOUNT * GREATEST(1, 2024 - GRADUATION_YEAR) * 
          UNIFORM(0.8, 1.5, RANDOM()), 2) AS CUMULATIVE_DONATION_AMOUNT,
    
    -- Last donation date (within last 2 years)
    DATEADD(day, -UNIFORM(1, 730, RANDOM()), CURRENT_DATE()) AS LAST_DONATION_DATE,
    
    -- Donor segment based on annual giving
    CASE 
        WHEN ANNUAL_DONATION_AMOUNT >= 10000 THEN 'Major Donor'
        WHEN ANNUAL_DONATION_AMOUNT >= 1000 THEN 'Mid-Level Donor'
        ELSE 'Annual Donor'
    END AS DONOR_SEGMENT,
    
    -- H3 indices at different resolutions using working function
    H3_LATLNG_TO_CELL_STRING(LATITUDE, LONGITUDE, 7) AS H3_LEVEL_7,
    H3_LATLNG_TO_CELL_STRING(LATITUDE, LONGITUDE, 8) AS H3_LEVEL_8,
    H3_LATLNG_TO_CELL_STRING(LATITUDE, LONGITUDE, 9) AS H3_LEVEL_9
FROM donor_with_calculated_fields
ORDER BY DONOR_ID;

-- Clean up temporary tables and views
DROP TABLE IF EXISTS TARGET_ZIP_ADDRESSES;
DROP TABLE IF EXISTS OTHER_GREENVILLE_ADDRESSES;
DROP TABLE IF EXISTS GREENVILLE_ADDRESSES;
DROP VIEW IF EXISTS DEMO_DATA_ARRAYS; 
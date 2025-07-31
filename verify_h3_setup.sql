-- Higher Education Alumni Targeting Demo - H3 Setup Verification
-- This script checks if H3 columns exist and have data
-- Note: The demo uses zip code filtering for Greenville County (not city names)
-- For H3 function testing, also run: debug_h3_functions.sql

USE DATABASE HIGHER_ED_DEMO;
USE SCHEMA ALUMNI_TARGETING;

-- Check if tables exist
SELECT 'Checking table existence...' as STATUS;

SELECT 
    table_name,
    created
FROM information_schema.tables 
WHERE table_schema = 'ALUMNI_TARGETING'
AND table_name IN ('ALUMNI_DONORS', 'EVENT_VENUES', 'DONOR_ANALYTICS_SUMMARY')
ORDER BY table_name;

-- Check ALUMNI_DONORS table structure
SELECT 'Checking ALUMNI_DONORS columns...' as STATUS;

SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'ALUMNI_TARGETING'
AND table_name = 'ALUMNI_DONORS'
AND column_name LIKE '%H3%'
ORDER BY column_name;

-- Check if H3 columns have data
SELECT 'Checking H3 data in ALUMNI_DONORS...' as STATUS;

SELECT 
    COUNT(*) as TOTAL_RECORDS,
    COUNT(H3_LEVEL_7) as H3_LEVEL_7_COUNT,
    COUNT(H3_LEVEL_8) as H3_LEVEL_8_COUNT,
    COUNT(H3_LEVEL_9) as H3_LEVEL_9_COUNT,
    COUNT(CASE WHEN H3_LEVEL_7 IS NOT NULL THEN 1 END) as H3_LEVEL_7_NOT_NULL,
    COUNT(CASE WHEN H3_LEVEL_8 IS NOT NULL THEN 1 END) as H3_LEVEL_8_NOT_NULL,
    COUNT(CASE WHEN H3_LEVEL_9 IS NOT NULL THEN 1 END) as H3_LEVEL_9_NOT_NULL
FROM ALUMNI_DONORS;

-- Sample H3 values
SELECT 'Sample H3 values...' as STATUS;

SELECT 
    DONOR_ID,
    LATITUDE,
    LONGITUDE,
    H3_LEVEL_7,
    H3_LEVEL_8,
    H3_LEVEL_9
FROM ALUMNI_DONORS 
WHERE H3_LEVEL_7 IS NOT NULL
LIMIT 5;

-- Test H3 function availability
SELECT 'Testing H3 function...' as STATUS;

SELECT 
    H3_LATLNG_TO_CELL_STRING(34.8526, -82.3940, 7) as TEST_H3_LEVEL_7,
    H3_LATLNG_TO_CELL_STRING(34.8526, -82.3940, 8) as TEST_H3_LEVEL_8,
    H3_LATLNG_TO_CELL_STRING(34.8526, -82.3940, 9) as TEST_H3_LEVEL_9;

-- Check EVENT_VENUES H3 data
SELECT 'Checking EVENT_VENUES H3 data...' as STATUS;

SELECT 
    COUNT(*) as TOTAL_VENUES,
    COUNT(H3_LEVEL_7) as H3_LEVEL_7_COUNT,
    COUNT(H3_LEVEL_8) as H3_LEVEL_8_COUNT,
    COUNT(H3_LEVEL_9) as H3_LEVEL_9_COUNT
FROM EVENT_VENUES;

-- Final status
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM ALUMNI_DONORS WHERE H3_LEVEL_7 IS NOT NULL) > 0 
        THEN '✅ H3 setup appears to be working correctly'
        ELSE '❌ H3 columns exist but have no data - please re-run data generation scripts'
    END as FINAL_STATUS; 
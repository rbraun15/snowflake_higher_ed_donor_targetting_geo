-- Debug H3 Functions in Snowflake
-- Run this script to test if H3 functions are working in your environment

-- Test 1: Basic H3 cell generation
SELECT 'Test 1: Basic H3 cell generation' AS test_description;
SELECT 
    H3_LATLNG_TO_CELL_STRING(34.8526, -82.3940, 8) AS h3_cell_greenville
    LIMIT 1;

-- Test 2: H3 boundary WKT generation (may not be available in all environments)
SELECT 'Test 2: H3 boundary WKT generation' AS test_description;
-- Note: This function may not exist in your Snowflake environment
-- If you get "Unknown function" error, that's why you see circles instead of hexagons
SELECT 
    H3_CELL_TO_BOUNDARY_WKT('872830828ffffff') AS boundary_wkt
    LIMIT 1;

-- Test 3: Check if your donor data has H3 columns
SELECT 'Test 3: Check H3 columns in ALUMNI_DONORS' AS test_description;
SELECT 
    COUNT(*) AS total_donors,
    COUNT(H3_LEVEL_7) AS h3_level_7_count,
    COUNT(H3_LEVEL_8) AS h3_level_8_count,
    COUNT(H3_LEVEL_9) AS h3_level_9_count
FROM HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
LIMIT 1;

-- Test 4: Sample H3 data from your donors
SELECT 'Test 4: Sample H3 data from donors' AS test_description;
SELECT 
    DONOR_ID,
    LATITUDE,
    LONGITUDE,
    H3_LEVEL_8,
    H3_CELL_TO_BOUNDARY_WKT(H3_LEVEL_8) AS boundary_wkt_sample
FROM HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
WHERE H3_LEVEL_8 IS NOT NULL
LIMIT 3;

-- Test 5: H3 aggregation like the app does
SELECT 'Test 5: H3 aggregation test' AS test_description;
SELECT 
    H3_LEVEL_8,
    COUNT(*) AS donor_count,
    SUM(ANNUAL_DONATION_AMOUNT) AS total_annual,
    AVG(LATITUDE) AS center_lat,
    AVG(LONGITUDE) AS center_lon
FROM HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
WHERE H3_LEVEL_8 IS NOT NULL
GROUP BY H3_LEVEL_8
ORDER BY donor_count DESC
LIMIT 5;

-- Expected Results:
-- Test 1: Should return an H3 cell ID like '872830828ffffff'
-- Test 2: Should return WKT polygon like 'POLYGON((-82.123 34.456, ...))'
--         ⚠️  If you get "Unknown function H3_CELL_TO_BOUNDARY_WKT" error:
--         This explains why you see CIRCLES instead of HEXAGONS in the app
--         The app will use enhanced markers instead of true hexagon shapes
-- Test 3: Should show counts - if H3 counts are 0, you need to regenerate data
-- Test 4: Should show sample boundary WKT for actual donor H3 cells (will fail if Test 2 fails)
-- Test 5: Should show aggregated data by H3 cell (what creates the spatial clustering)

-- Summary:
-- ✅ Test 1 + Test 5 working = Spatial aggregation works (enhanced markers)
-- ✅ Test 1 + Test 2 + Test 5 working = True hexagons available
-- ❌ Test 1 failing = Need to regenerate data with H3 columns 
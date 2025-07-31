# 🐅 Streamlit in Snowflake Deployment Guide

This guide shows you how to deploy the Clemson Alumni Event Location Targeting demo as a **Streamlit in Snowflake (SiS)** application.

## 🎯 Overview

Streamlit in Snowflake allows you to run Streamlit applications natively within Snowflake, providing:
- **Seamless data access** without connection strings or secrets
- **Built-in security** using Snowflake's role-based access control
- **Easy sharing** within your Snowflake organization
- **Native integration** with Snowflake data and compute resources

## 📋 Prerequisites

1. **Snowflake Account** with Streamlit in Snowflake enabled
2. **Appropriate Privileges**:
   - `CREATE STREAMLIT` privilege
   - `USAGE` privilege on database and schema
   - Access to the US Addresses & POI marketplace data

## 🚀 Step-by-Step Deployment

### Step 1: Set Up the Database

1. **Run the SQL scripts** in order using Snowsight or your preferred SQL client:

```sql
-- 1. Setup database and warehouse
-- Execute: sql/01_setup_database.sql

-- 2. Create tables 
-- Execute: sql/02_create_tables.sql

-- 3. Generate donor data
-- Execute: sql/03_generate_donor_data.sql

-- 4. Generate venue data
-- Execute: sql/04_generate_venue_data.sql

-- 5. Create analytics summaries
-- Execute: sql/05_create_analytics_summary.sql

-- 6. Verify H3 setup (optional but recommended)
-- Execute: verify_h3_setup.sql
```

### Step 2: Create the Streamlit Application

1. **Open Snowsight** and navigate to "Streamlit"
2. **Click "Create Streamlit App"**
3. **Configure the application**:
   - **Name**: `clemson_alumni_targeting`
   - **Database**: `HIGHER_ED_DEMO`
   - **Schema**: `ALUMNI_TARGETING`
   - **Warehouse**: `HIGHER_ED_WH`

4. **Replace the default code** with the contents of `streamlit_in_snowflake_app.py`

### Step 3: Grant Necessary Privileges

```sql
-- Grant privileges to the Streamlit app
USE ROLE ACCOUNTADMIN; -- or appropriate role

-- Grant database and schema access
GRANT USAGE ON DATABASE HIGHER_ED_DEMO TO STREAMLIT CLEMSON_ALUMNI_TARGETING;
GRANT USAGE ON SCHEMA HIGHER_ED_DEMO.ALUMNI_TARGETING TO STREAMLIT CLEMSON_ALUMNI_TARGETING;

-- Grant table access
GRANT SELECT ON ALL TABLES IN SCHEMA HIGHER_ED_DEMO.ALUMNI_TARGETING TO STREAMLIT CLEMSON_ALUMNI_TARGETING;
GRANT SELECT ON FUTURE TABLES IN SCHEMA HIGHER_ED_DEMO.ALUMNI_TARGETING TO STREAMLIT CLEMSON_ALUMNI_TARGETING;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE HIGHER_ED_WH TO STREAMLIT CLEMSON_ALUMNI_TARGETING;
```

### Step 4: Verify Setup (Optional but Recommended)

Run the verification script to ensure H3 columns are properly set up:

```sql
-- Execute: verify_h3_setup.sql
```

This will check:
- ✅ Table existence and structure
- ✅ H3 column presence and data
- ✅ H3 function availability
- ✅ Sample H3 values

### Step 5: Deploy and Test

1. **Click "Run"** in the Streamlit interface
2. **Verify data loading** - you should see the donor and venue data
3. **Test all features**:
   - ✅ Geographic analysis with H3 hexagonal grids and individual points
   - ✅ Interactive filtering by zip, graduation year, donation amount, segments
   - ✅ Analytics dashboard with charts and visualizations
   - ✅ Venue exploration with filtering capabilities
   - ✅ Donor details table with summary statistics

**Note**: If you see warnings about missing H3 columns, the app will automatically calculate H3 indices on-the-fly.

## 🎮 Using the Application

### Key Features

1. **Geographic Analysis**:
   - **H3 Hexagonal Grid**: True H3 hexagons using Snowflake's H3 functions
   - **Individual Points**: Shows each donor as a colored point
   - **Venue Overlay**: Purple stars show potential event locations
   - **Interactive Maps**: Hover for detailed information with hexagon boundaries

2. **Dynamic Filtering**:
   - **Zip Codes**: Focus on high-concentration areas
   - **Graduation Years**: Target specific alumni cohorts
   - **Donation Amounts**: Filter by giving capacity
   - **Donor Segments**: Major, Mid-Level, Annual donors

3. **Analytics Dashboard**:
   - **Graduation trends**: Donation patterns by year
   - **Geographic analysis**: Top-performing zip codes
   - **Segment distribution**: Visual breakdown of donor types
   - **Academic analysis**: Top majors by total giving

4. **Event Planning**:
   - **20+ curated venues** across Greenville area
   - **Venue filtering** by type, capacity, price range
   - **Detailed venue information** with contact details
   - **Proximity consideration** to donor concentrations

## 🔧 Customization Options

### Adding More Zip Codes

The demo uses zip code filtering (not city names) for reliable geographic targeting. Current Greenville County zip codes:

**Target Zip Codes (70% of data)**: 29680, 29650, 29607, 29681

**Other Greenville County Zip Codes (30% of data)**: 29601, 29602, 29603, 29604, 29605, 29606, 29608, 29609, 29610, 29611, 29612, 29613, 29614, 29615, 29616, 29617, 29635, 29636, 29644, 29651, 29652, 29661, 29662, 29673, 29683, 29687, 29688, 29690

To expand to other counties:

```sql
-- Modify sql/03_generate_donor_data.sql to include other SC counties:

-- For example, add Charleston County zip codes:
AND ZIP IN ('29401', '29403', '29405', '29407', '29409', '29412', '29414', '29418', '29424', '29425')
```

### Adding More Venues

```sql
-- Insert additional venues into the EVENT_VENUES table
INSERT INTO HIGHER_ED_DEMO.ALUMNI_TARGETING.EVENT_VENUES 
(VENUE_ID, VENUE_NAME, VENUE_TYPE, ...) 
VALUES 
('VENUE_021', 'Your Custom Venue', 'Restaurant', ...);
```

### Modifying Spatial Resolution

The spatial binning resolution can be adjusted in the application:
- **Lower values (6-7)**: Fewer, larger spatial bins
- **Higher values (9-10)**: More, smaller spatial bins

## 🚨 Troubleshooting

### Common Issues

1. **"Table not found" errors**:
   - Verify all SQL scripts ran successfully
   - Check database and schema names match exactly
   - Ensure proper privileges are granted

2. **"Access denied" errors**:
   - Run the privilege grant statements
   - Verify the Streamlit app has access to the warehouse
   - Check role permissions

3. **"KeyError: H3_LEVEL_X" errors**:
   - H3 columns missing from database tables
   - **Solution**: Run `verify_h3_setup.sql` to check H3 column status
   - If H3 columns don't exist, re-run SQL scripts 02-05 in order
   - The app will automatically fall back to on-the-fly H3 calculation using Snowpark

4. **"Unsupported statement type 'temporary TABLE'" errors**:
   - Snowflake Streamlit environment restrictions
   - **Fixed**: App now uses Snowpark dataframe operations instead of temporary tables
   - On-the-fly H3 calculation works without temporary table creation

5. **Empty data or maps**:
   - Verify the US Addresses marketplace data is accessible
   - Check that donor generation completed successfully
   - Ensure latitude/longitude values are not null
   - Run `verify_h3_setup.sql` to confirm data integrity

6. **Performance issues**:
   - Increase warehouse size if needed
   - Add filters to reduce data volume for visualization
   - Consider data sampling for very large datasets

7. **H3 functions not available**:
   - Verify your Snowflake account has H3 functions enabled
   - Test with: `SELECT H3_LATLNG_TO_CELL_STRING(34.8526, -82.3940, 7);`
   - Contact Snowflake support if H3 functions are unavailable

8. **"Truth value of an array" errors**:
   - Pandas/numpy array boolean context issues
   - **Fixed**: Improved array handling with `.tolist()` and `.dropna()` methods
   - Better error handling for empty dataframes and missing data

9. **Map Issues - Common Problems**:

   **🔴 CIRCLES instead of TRUE HEXAGONS?**
   - **NEW SOLUTION**: App now uses PyDeck H3HexagonLayer for native hexagon visualization!
   - **Look for**: "Creating TRUE H3 hexagons using PyDeck" success message
   - **If you see enhanced markers**: PyDeck may not be available in your SiS environment
   - **Fallback**: App automatically falls back to enhanced circular markers
   - **Best visualization**: PyDeck provides true H3 hexagon polygons without needing Snowflake boundary functions

   **🔴 No map geography (streets, boundaries)?**
   - Streamlit in Snowflake blocks external map tiles
   - **Solutions**:
     1. Use `white-bg` map style (no external dependencies)
     2. Try `carto-positron` (more reliable than OpenStreetMap)
     3. Use standalone Streamlit app instead (no SiS restrictions)
   
   **🔴 Some map styles don't work?**
   - `stamen-terrain` commonly fails in corporate environments
   - Corporate firewalls block certain tile servers
   - **Best options**: `carto-positron` or `white-bg`

### Getting Help

- **Snowflake Documentation**: [Streamlit in Snowflake Guide](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- **Community Support**: Snowflake Community Forums
- **Professional Support**: Snowflake Support Portal

## 🎯 Demo Use Cases

This application is perfect for demonstrating:

1. **Modern Data Stack**: Cloud data warehouse + native applications
2. **Geospatial Analytics**: Location-based decision making
3. **Interactive Dashboards**: Self-service analytics for end users
4. **Data-Driven Fundraising**: Optimizing advancement strategies
5. **Snowflake Capabilities**: Native Streamlit, marketplace data, spatial functions

## 📈 Extending the Demo

Consider adding:

1. **Real-time updates**: Schedule data refreshes
2. **Advanced spatial analysis**: Distance calculations, catchment areas
3. **Predictive modeling**: Donor likelihood scoring
4. **Integration**: Connect with CRM systems
5. **Mobile optimization**: Responsive design improvements

## 🔐 Security Considerations

- **Role-based access**: Use Snowflake's native security model
- **Data masking**: Apply dynamic data masking for sensitive information  
- **Audit trails**: Leverage Snowflake's audit capabilities
- **Row-level security**: Implement if multiple organizations use the demo

---

**🎉 Your Streamlit in Snowflake application is now ready!**

This native deployment provides the best performance and integration with your Snowflake environment while showcasing advanced geospatial analytics capabilities. 
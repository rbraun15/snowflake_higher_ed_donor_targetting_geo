# 🐅 Alumni Event Location Targeting Demo

A comprehensive **Streamlit in Snowflake** application for analyzing alumni donor data and optimizing event location selection in the Greenville, SC area. This demo showcases advanced geospatial analytics with **PyDeck H3 hexagon visualization**, interactive filtering, and data visualization capabilities running natively within Snowflake.

## 🎯 Two Deployment Options

This demo provides two ways to deploy:

1. **🏆 Streamlit in Snowflake (RECOMMENDED)**: Native deployment within Snowflake
   - **File**: `streamlit_in_snowflake_app.py`
   - **Setup Guide**: `STREAMLIT_IN_SNOWFLAKE_SETUP.md`
   - **Benefits**: Seamless data access, built-in security, easy sharing

2. **🐍 Standalone Streamlit**: Traditional Python application
   - **File**: `streamlit_app.py`
   - **Setup Guide**: This README
   - **Benefits**: Full control, PDF export, external deployment

## 🎯 Demo Overview

This application helps university advancement teams make data-driven decisions about alumni event locations by:

- **Visualizing donor density** using H3 hexagonal grids and individual points
- **Analyzing donation patterns** by geography, graduation year, and donor segments
- **Identifying optimal event venues** based on donor concentration
- **Providing interactive filtering** for targeted analysis
- **Generating comprehensive reports** with PDF export capabilities

## 🏗️ Architecture

The demo consists of:

1. **Data Layer**: Snowflake data warehouse with US Addresses & POI marketplace data
2. **Analytics Layer**: SQL scripts for data generation and aggregation
3. **Visualization Layer**: Streamlit application with interactive maps and charts
4. **Export Layer**: PDF report generation with preserved visualizations

## 📊 Key Features

### Strategic Event Planning Workflow
The app is designed with a **two-map workflow** for optimal event planning:

1. **🔷 Start with H3 Hexagon View**: 
   - Identify geographic areas with high donor concentration
   - Look for dark red hexagons = highest total donations
   - Analyze donor density patterns across Greenville County

2. **🎯 Switch to Individual Points View**:
   - See exact donor locations within your target areas
   - Identify specific venue options (purple stars)
   - Match high-value donors with convenient venue locations

3. **📊 Strategic Decision Making**:
   - Large red dots near purple venues = premium event opportunities
   - Cluster analysis for optimal venue selection
   - Filter by segments to match event type with audience

### Geographic Analysis
- **True H3 Hexagons**: PyDeck H3HexagonLayer for native hexagon visualization
- **PyDeck Point Maps**: ScatterplotLayer for high-performance individual donor visualization
- **Dynamic Resolution**: Slider (levels 7-9) for spatial aggregation
- **Strategic Workflow**: H3 hexagons for area analysis → switch to points for venue selection
- **Rich Tooltips**: Formatted donation amounts and donor counts
- **Background Maps**: Properly displayed geography with both visualization types
- **Interactive Map Legends**: Expandable guides explaining colors, sizes, and strategic workflows for both visualization types

### Advanced Filtering
- **Smart Zip Code Controls**: "Select All" and "Clear All" buttons plus multiselect
- **Smart Donor Segment Controls**: Quick selection buttons for faster filtering
- **Graduation Year Range**: Target alumni cohorts with slider
- **Donation Amount Range**: Filter by giving capacity
- **Real-time Updates**: All filters update maps and tables instantly

### Analytics Dashboard
- **Donation Trends**: Visualizations by graduation year
- **Geographic Distribution**: Top performing zip codes
- **Donor Segmentation**: Pie charts and distribution analysis
- **Major Analysis**: Top-performing academic programs

### Event Venue Integration
- **20+ Curated Venues**: Hotels, restaurants, country clubs, and unique locations
- **Venue Filtering**: By type, capacity, price range, and rating
- **Detailed Information**: Contact details, descriptions, and amenities

### Data Management & Export
- **Individual Donor Table**: Searchable table below map showing detailed records
- **Quadruple Download Options**: Filtered data, complete dataset, comprehensive analysis report, and map images
- **Map Image Download**: Generate and download current map view as high-resolution PNG (1200x800, 2x scale) - *Standalone app only*
- **Enhanced Map + Table Report**: Includes map recreation instructions, PyDeck code examples, and geographic bounds
- **Map Visualization Recreation**: Complete instructions and code for recreating both H3 hexagon and point maps
- **Smart Table Display**: Choose to show 50, 100, 250, 500, or all records
- **Formatted Display**: Currency formatting and clean column names
- **Sidebar Debug Info**: H3 data debugging moved to sidebar for cleaner interface
- **Real-time Record Counts**: Shows filtered vs total records

## 🚀 Quick Start

### For Streamlit in Snowflake (Recommended)

👉 **Follow the [Streamlit in Snowflake Setup Guide](STREAMLIT_IN_SNOWFLAKE_SETUP.md)**

This is the fastest way to get started and provides the best integration with Snowflake.

### For Standalone Python Deployment

Continue with the instructions below for a traditional Python/Streamlit deployment.

## 📋 Standalone Installation & Setup

### Prerequisites

- Python 3.8+
- Snowflake account with appropriate permissions
- Access to Snowflake Marketplace (US Addresses & POI dataset)

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd HE_Alumni_Targetting_GIS

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test setup (optional but recommended)
python test_setup.py
```

### Step 2: Snowflake Setup

1. **Get US Addresses & POI Data**:
   - Go to Snowflake Marketplace
   - Search for "US Addresses & POI" dataset
   - Request and install the dataset to your account
   - Ensure the data is available at: `US_POINTS_OF_INTEREST__ADDRESSES.cybersyn.us_addresses`

2. **Configure Database Connection**:
   ```bash
   # Create Streamlit secrets directory
   mkdir .streamlit
   
   # Copy and configure secrets
   cp secrets.toml.template .streamlit/secrets.toml
   ```

3. **Edit `.streamlit/secrets.toml`**:
   ```toml
   [snowflake]
   account = "your_account_identifier"
   user = "your_username"
   password = "your_password"
   ```

### Step 3: Initialize Database

Run the SQL scripts in order to set up your database:

```sql
-- 1. Setup database and warehouse
-- Run: sql/01_setup_database.sql

-- 2. Create tables
-- Run: sql/02_create_tables.sql

-- 3. Generate donor data (leverages marketplace data)
-- Run: sql/03_generate_donor_data.sql

-- 4. Generate venue data
-- Run: sql/04_generate_venue_data.sql

-- 5. Create analytics summaries
-- Run: sql/05_create_analytics_summary.sql
```

### Step 4: Launch Application

```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## 📋 Usage Guide

### 1. Geographic Analysis Tab
- Use the **Map Type** selector to toggle between H3 hexagonal grid and individual points
- Adjust **H3 Resolution** slider for different levels of spatial aggregation:
  - Level 7: Large hexagons (~5km across)
  - Level 8: Medium hexagons (~1.2km across)  
  - Level 9: Small hexagons (~460m across)
- Toggle **Show Venues** to overlay potential event locations

### 2. Targeting Filters (Sidebar)
- **Zip Codes**: Select specific areas (default focuses on 70% target zips)
- **Graduation Year Range**: Target specific alumni cohorts
- **Donation Range**: Filter by annual giving capacity
- **Donor Segments**: Focus on Major, Mid-Level, or Annual donors

### 3. Analytics Dashboard
- View **donation trends** by graduation year
- Analyze **top-performing zip codes** and academic majors
- Understand **donor segment distribution**
- Identify **geographic patterns** in giving

### 4. Event Venues Tab
- Browse **20+ curated venues** in the Greenville area
- Filter by **venue type**, **capacity**, **price range**
- View detailed **contact information** and descriptions
- Consider **proximity to donor concentrations**

### 5. Export & Reporting
- **Generate PDF reports** with all visualizations
- **Download filtered data** as CSV for external analysis
- **View summary statistics** for quick insights

## 🎯 Demo Data

The demo includes:

- **10,000 simulated alumni donors** with realistic demographics
- **70% concentration** in target zip codes (29680, 29650, 29607, 29681)
- **Graduation years**: 1990-2024 with age-correlated donation patterns
- **Donation ranges**: $25-$50K annual, $100-$500K cumulative
- **20 event venues** across multiple categories
- **H3 spatial indexing** at resolutions 7, 8, and 9 (calculated in Python)

### Data Distribution

**Geographic Coverage**: Uses zip code filtering (not city names) for reliable targeting across Greenville County, SC.

| Geographic Area | Zip Codes | Target % | Donor Count | 
|----------------|-----------|----------|-------------|
| Primary Target | 29680, 29650, 29607, 29681 | 70% | ~7,000 |
| Greenville County | 29601-29690 (30+ zip codes) | 30% | ~3,000 |

**Why Zip Codes vs. City Names**: 
- More reliable geographic boundaries
- Consistent data formatting
- Avoids city name variations in address data

## 🔧 Technical Details

### H3 Indexing
- Uses Uber's H3 hierarchical hexagonal indexing system
- **Streamlit in Snowflake**: Native H3 functions (`H3_LATLNG_TO_CELL_STRING`, `H3_CELL_TO_BOUNDARY_WKT`)
- **Standalone Python**: H3 calculations performed in Python for portability
- Enables efficient spatial aggregation and analysis
- Supports multiple resolution levels (7-9) for different use cases

### Snowflake Integration
- Leverages Snowflake's native geospatial functions
- Uses marketplace data for realistic address geocoding
- Creates materialized tables (not views) for optimal performance
- Optimized queries for large-scale data processing

### Visualization Stack
- **Streamlit**: Interactive web application framework
- **PyDeck**: Native H3 hexagon visualization with H3HexagonLayer
- **Plotly**: Advanced charting and mapping capabilities
- **Folium**: Interactive maps with tooltips and overlays (standalone app)
- **Matplotlib/Seaborn**: PDF report generation (standalone app)

## 🚨 Troubleshooting

### Map Display Issues

**🔴 Enhanced Markers instead of True Hexagons?**
- **NEW SOLUTION**: App now uses PyDeck H3HexagonLayer for native hexagon visualization!
- **Look for**: "Creating TRUE H3 hexagons using PyDeck" success message in the app
- **If enhanced markers**: PyDeck may not be available in your environment
- **Automatic fallback**: App falls back to enhanced circular markers if PyDeck fails
- **Best option**: PyDeck provides true H3 polygons without Snowflake boundary functions

**🔴 No map geography showing?**
- Try `white-bg` map style (no external dependencies)
- Corporate firewalls often block map tile servers
- Consider using standalone app instead of SiS

**🔴 PyDeck Serialization Errors?**
- Error: "vars() argument must have __dict__ attribute"
- **Fixed**: App now converts all data to basic Python types before PyDeck
- If persists: Check for pandas/numpy objects in your data

**🔴 HTML Rendering Issues (Map Legends)?**
- **Problem**: Raw HTML code showing instead of formatted content
- **Fixed**: Now using Streamlit native components (expanders, columns) instead of complex HTML
- **Result**: Map legends display properly in all environments

**🔴 Map Image Download Not Working?**
- **Streamlit in Snowflake**: Image downloads typically don't work due to environment restrictions
- **Standalone App**: Requires `pip install kaleido` for image generation
- **Alternative**: Use browser screenshot or the comprehensive text report with recreation instructions
- **Error "h3_resolution not defined"**: Fixed - variable now properly scoped for both map types

### Common Issues

1. **Snowflake Connection Errors**:
   - Verify account identifier format (`account.region.provider`)
   - Check username/password in secrets.toml
   - Ensure user has necessary permissions

2. **Missing Marketplace Data**:
   - Install "US Addresses & POI" from Snowflake Marketplace
   - Verify data is available at `US_POINTS_OF_INTEREST__ADDRESSES.cybersyn.us_addresses`
   - Update database references in SQL scripts if your path differs

3. **Package Installation Issues**:
   - Use Python 3.8+ (some dependencies require recent versions)
   - Consider using conda for complex dependencies like h3

4. **Performance Issues**:
   - Adjust warehouse size in Snowflake for faster queries
   - Use filtering to reduce data volume for visualization

5. **H3 Visualization**:
   - **NEW**: Both versions now use PyDeck H3HexagonLayer for true hexagon visualization
   - **SiS Version**: H3 aggregation via Snowflake functions (`H3_LATLNG_TO_CELL_STRING`)
   - **Standalone Version**: Uses Python `h3>=3.7.0` library for H3 calculations
   - **Test PyDeck**: Run `python test_pydeck_h3.py` to verify PyDeck functionality
   - **Fallback**: Apps automatically fall back to enhanced markers if PyDeck fails
   - Run `debug_h3_functions.sql` to test Snowflake H3 availability
   - Use `verify_h3_setup.sql` to check if your data has H3 columns

6. **"Truth value of an array" Errors**:
   - Pandas/numpy arrays used in boolean contexts
   - **Fixed**: Improved array handling with proper `.tolist()` and `.dropna()` methods
   - Apps now gracefully handle empty dataframes and missing H3 data

### Getting Help

- Check Snowflake documentation for marketplace data setup
- Review Streamlit documentation for deployment options
- Verify H3 installation for spatial indexing features

## 🎓 Educational Value

This demo showcases:

- **Modern data stack** architecture with cloud data warehouse
- **Geospatial analytics** techniques for business intelligence
- **Interactive visualization** best practices
- **Data-driven decision making** for advancement operations
- **Scalable data processing** patterns for large datasets

## 📝 License

This demo is provided for educational and demonstration purposes. Please ensure compliance with your organization's data policies and Snowflake marketplace terms when using real data.

## 🤝 Contributing

To extend this demo:

1. Add new venue types or geographic areas
2. Implement additional H3 resolution levels
3. Create new analytical visualizations
4. Add real-time data refresh capabilities
5. Extend filtering and segmentation options

---

**Built with ❤️ for Higher Education Advancement Teams**

*Clemson University colors: Orange (#F56500) and Purple (#522D80)* 

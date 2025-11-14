import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pydeck as pdk
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Alumni Event Location Targeting - Greenville, SC",
    page_icon="🐅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #F56500;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #522D80;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F56500;
    }
    .venue-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 0.5rem;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Hide any stray elements that might be causing red parentheses */
    div[data-testid="metric-container"] > div > div:first-child::before {
        content: none !important;
    }
    /* Ensure metric labels display properly */
    div[data-testid="metric-container"] {
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Get Snowflake session (automatically available in SiS)
@st.cache_resource
def get_snowflake_session():
    """Get the active Snowflake session"""
    return get_active_session()

session = get_snowflake_session()

# Data loading functions using Snowpark
@st.cache_data(ttl=600)
def load_donor_data():
    """Load donor data using Snowpark"""
    df = session.table("HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS").to_pandas()
    return df

@st.cache_data(ttl=600)
def load_venue_data():
    """Load venue data using Snowpark"""
    df = session.table("HIGHER_ED_DEMO.ALUMNI_TARGETING.EVENT_VENUES").to_pandas()
    return df

@st.cache_data(ttl=600)
def load_analytics_summary():
    """Load analytics summary data using Snowpark"""
    df = session.table("HIGHER_ED_DEMO.ALUMNI_TARGETING.DONOR_ANALYTICS_SUMMARY").to_pandas()
    return df

@st.cache_data(ttl=600)
def load_overview_data():
    """Load overview metrics using Snowpark"""
    df = session.table("HIGHER_ED_DEMO.ALUMNI_TARGETING.DONOR_OVERVIEW").to_pandas()
    return df

def apply_filters(df, zip_codes, grad_years, donation_range, donor_segments):
    """Apply filters to the donor dataframe"""
    filtered_df = df.copy()
    
    if zip_codes:
        filtered_df = filtered_df[filtered_df['ZIP_CODE'].isin(zip_codes)]
    
    if grad_years:
        filtered_df = filtered_df[
            (filtered_df['GRADUATION_YEAR'] >= grad_years[0]) & 
            (filtered_df['GRADUATION_YEAR'] <= grad_years[1])
        ]
    
    if donation_range:
        filtered_df = filtered_df[
            (filtered_df['ANNUAL_DONATION_AMOUNT'] >= donation_range[0]) & 
            (filtered_df['ANNUAL_DONATION_AMOUNT'] <= donation_range[1])
        ]
    
    if donor_segments:
        filtered_df = filtered_df[filtered_df['DONOR_SEGMENT'].isin(donor_segments)]
    
    return filtered_df

def create_h3_on_the_fly(df, resolution, map_style="open-street-map"):
    """Create H3 hexagon map by calculating H3 indices on-the-fly"""
    try:
        # Check if dataframe is empty or has no valid coordinates
        valid_data = df[['LATITUDE', 'LONGITUDE', 'ANNUAL_DONATION_AMOUNT', 'CUMULATIVE_DONATION_AMOUNT']].dropna()
        
        if valid_data.empty:
            st.warning("No valid geographic data available for H3 analysis.")
            return create_simple_scatter_map(df, map_style)
        
        # Use direct Snowpark dataframe operations instead of temporary tables
        # Create Snowpark dataframe from pandas
        snowpark_df = session.create_dataframe(valid_data)
        
        # Calculate H3 and aggregate using Snowpark operations
        from snowflake.snowpark.functions import col, sum, count, avg, round
        
        # Add H3 column using SQL expression
        h3_df = snowpark_df.with_column(
            "H3_CELL", 
            snowpark_df.sql_expr(f"H3_LATLNG_TO_CELL_STRING(LATITUDE, LONGITUDE, {resolution})")
        )
        
        # Aggregate by H3 cell
        h3_agg_snowpark = h3_df.group_by("H3_CELL").agg([
            count("*").alias("DONOR_COUNT"),
            sum("ANNUAL_DONATION_AMOUNT").alias("TOTAL_ANNUAL"),
            round(avg("ANNUAL_DONATION_AMOUNT"), 2).alias("AVG_ANNUAL"),
            sum("CUMULATIVE_DONATION_AMOUNT").alias("TOTAL_CUMULATIVE"),
            avg("LATITUDE").alias("CENTER_LAT"),
            avg("LONGITUDE").alias("CENTER_LON")
        ]).order_by(col("TOTAL_ANNUAL").desc())
        
        # Convert to pandas
        h3_agg = h3_agg_snowpark.to_pandas()
        
        if h3_agg.empty:
            st.error("No H3 data could be generated from the current dataset.")
            return create_simple_scatter_map(df, map_style)
        
        # Get H3 cell boundaries
        h3_cells = h3_agg['H3_CELL'].dropna().unique()
        boundaries = get_h3_boundaries_from_snowflake(h3_cells)
        
        # Create the map
        fig = go.Figure()
        
        # Add H3 hexagon polygons if we have boundaries
        if boundaries:
            for boundary in boundaries:
                h3_cell = boundary['h3_cell']
                cell_data = h3_agg[h3_agg['H3_CELL'] == h3_cell]
                
                if not cell_data.empty:
                    row = cell_data.iloc[0]
                    
                    # Color based on total annual donations
                    max_donations = h3_agg['TOTAL_ANNUAL'].max()
                    opacity = min(0.8, max(0.3, row['TOTAL_ANNUAL'] / max_donations))
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=boundary['lats'] + [boundary['lats'][0]],
                        lon=boundary['lons'] + [boundary['lons'][0]],
                        mode='lines',
                        fill='toself',
                        fillcolor=f'rgba(255, 87, 0, {opacity})',
                        line=dict(color='white', width=1),
                        hovertemplate=f"""
                        <b>H3 Cell: {h3_cell}</b><br>
                        Donors: {row['DONOR_COUNT']}<br>
                        Total Annual: ${row['TOTAL_ANNUAL']:,.2f}<br>
                        Avg Annual: ${row['AVG_ANNUAL']:,.2f}<br>
                        Total Cumulative: ${row['TOTAL_CUMULATIVE']:,.2f}<br>
                        <extra></extra>
                        """,
                        showlegend=False
                    ))
        else:
            # Simple, reliable fallback visualization when boundaries not available
            title_suffix = "No External Maps" if map_style == "white-bg" else map_style
            
            st.info(f"📊 Showing {len(h3_agg)} H3 spatial clusters as enhanced markers")
            
            fig = px.scatter_mapbox(
                h3_agg,
                lat='CENTER_LAT',
                lon='CENTER_LON',
                size='DONOR_COUNT',
                color='TOTAL_ANNUAL',
                hover_data={
                    'H3_CELL': True,
                    'DONOR_COUNT': True,
                    'TOTAL_ANNUAL': ':.0f',
                    'AVG_ANNUAL': ':.0f',
                    'TOTAL_CUMULATIVE': ':.0f',
                    'CENTER_LAT': False,
                    'CENTER_LON': False
                },
                color_continuous_scale='Oranges',
                size_max=60,
                zoom=10,
                mapbox_style="white-bg" if map_style == "white-bg" else map_style,
                title=f'H3 Spatial Analysis (Resolution Level {resolution}) - {len(h3_agg)} Clusters - {title_suffix}',
                labels={
                    'TOTAL_ANNUAL': 'Total Annual Donations ($)',
                    'DONOR_COUNT': 'Number of Donors'
                }
            )
            
            # Simple, reliable marker styling
            fig.update_traces(
                marker=dict(
                    opacity=0.8,
                    line=dict(width=1, color='white')
                )
            )
        
        # Update layout
        fig.update_layout(
            mapbox=dict(
                style=map_style,
                center=dict(lat=df['LATITUDE'].mean(), lon=df['LONGITUDE'].mean()),
                zoom=10
            ),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0),
            title=f'H3 Hexagon Analysis (Resolution Level {resolution}) - On-the-fly ({map_style})'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating H3 map on-the-fly: {str(e)}")
        return create_simple_scatter_map(df, map_style)

def create_simple_scatter_map(df, map_style="open-street-map"):
    """Create a simple scatter map as fallback"""
    
    # Remove rows with null coordinates
    valid_df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    if valid_df.empty:
        st.error("❌ No valid coordinates available")
        return None
    
    st.info(f"📍 Showing {len(valid_df)} individual donor locations")
    
    fig = px.scatter_mapbox(
        valid_df,
        lat='LATITUDE',
        lon='LONGITUDE',
        color='DONOR_SEGMENT' if 'DONOR_SEGMENT' in valid_df.columns else None,
        size='ANNUAL_DONATION_AMOUNT' if 'ANNUAL_DONATION_AMOUNT' in valid_df.columns else None,
        hover_data=['FULL_NAME', 'ANNUAL_DONATION_AMOUNT', 'ZIP_CODE'] if all(col in valid_df.columns for col in ['FULL_NAME', 'ANNUAL_DONATION_AMOUNT', 'ZIP_CODE']) else None,
        color_discrete_map={
            'Major Donor': '#ff0000',
            'Mid-Level Donor': '#ff8c00', 
            'Annual Donor': '#00a651'
        } if 'DONOR_SEGMENT' in valid_df.columns else None,
        zoom=10,
        mapbox_style="white-bg" if map_style == "white-bg" else map_style,
        title=f'Individual Donor Locations - {len(valid_df)} Donors - {"No External Maps" if map_style == "white-bg" else map_style}',
        height=600
    )
    
    fig.update_layout(
        mapbox=dict(
            center=dict(lat=valid_df['LATITUDE'].mean(), lon=valid_df['LONGITUDE'].mean()),
            zoom=10
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def get_h3_boundaries_from_snowflake(h3_cells):
    """Get H3 cell boundaries from Snowflake using H3 functions"""
    boundaries_data = []
    
    # Handle pandas Series/array checking properly
    if h3_cells is None or len(h3_cells) == 0:
        return boundaries_data
    
    # Convert to list and handle pandas Series properly    
    if hasattr(h3_cells, 'tolist'):
        h3_cells_list = h3_cells.tolist()
    else:
        h3_cells_list = list(h3_cells)
        
    # Limit to first 50 cells to avoid query complexity
    h3_list = [str(cell) for cell in h3_cells_list[:50] if pd.notna(cell)]
    
    if not h3_list:
        return boundaries_data
    
    # Test if H3_CELL_TO_BOUNDARY_WKT function is available
    try:
        test_query = "SELECT H3_CELL_TO_BOUNDARY_WKT('872830828ffffff') as test_boundary"
        test_result = session.sql(test_query).collect()
        function_available = True
    except Exception as e:
        if "Unknown function" in str(e) or "does not exist" in str(e):
            st.warning("⚠️ H3_CELL_TO_BOUNDARY_WKT function not available in your Snowflake environment")
            st.info("🔄 Using enhanced scatter visualization instead of true hexagons")
            function_available = False
        else:
            st.error(f"H3 boundary test failed: {str(e)}")
            function_available = False
    
    if not function_available:
        return boundaries_data
    
    # Debug info
    with st.expander("🔍 H3 Boundary Fetching Debug", expanded=False):
        st.write(f"✅ H3_CELL_TO_BOUNDARY_WKT function available!")
        st.write(f"Attempting to fetch boundaries for {len(h3_list)} H3 cells...")
        st.write(f"Sample H3 cells: {h3_list[:3]}")
    
    try:
        # Process H3 cells one by one to avoid complex SQL
        for i, h3_cell in enumerate(h3_list[:10]):  # Limit to 10 for performance
            try:
                boundary_query = f"""
                SELECT 
                    '{h3_cell}' as h3_cell,
                    H3_CELL_TO_BOUNDARY_WKT('{h3_cell}') as boundary_wkt
                """
                
                result = session.sql(boundary_query).collect()
                
                if result and len(result) > 0:
                    boundary_wkt = result[0]['BOUNDARY_WKT']
                    
                    # Debug: Show WKT for first cell
                    if i == 0:
                        with st.expander("🔍 H3 Boundary Fetching Debug", expanded=False):
                            st.code(f"Sample WKT result: {str(boundary_wkt)[:200]}...")
                    
                    if boundary_wkt and 'POLYGON' in str(boundary_wkt):
                        # Parse WKT POLYGON to extract coordinates
                        coords_str = str(boundary_wkt).replace('POLYGON((', '').replace('))', '')
                        coord_pairs = coords_str.split(', ')
                        
                        lats = []
                        lons = []
                        for pair in coord_pairs:
                            if ' ' in pair:
                                try:
                                    lon, lat = pair.strip().split(' ')
                                    lats.append(float(lat))
                                    lons.append(float(lon))
                                except:
                                    continue
                        
                        if len(lats) >= 3:  # Valid polygon needs at least 3 points
                            boundaries_data.append({
                                'h3_cell': h3_cell,
                                'lats': lats,
                                'lons': lons
                            })
                            
                            # Debug: Show success for first hexagon
                            if i == 0:
                                with st.expander("🔍 H3 Boundary Fetching Debug", expanded=False):
                                    st.success(f"✅ Parsed {len(lats)} coordinates for hexagon {h3_cell}")
                                    st.write(f"Sample coordinates: lat={lats[0]:.6f}, lon={lons[0]:.6f}")
                    else:
                        # Debug: Show why WKT failed
                        if i == 0:
                            with st.expander("🔍 H3 Boundary Fetching Debug", expanded=False):
                                st.error(f"❌ Invalid WKT format or no POLYGON found: {str(boundary_wkt)[:100]}")
            except Exception as cell_error:
                # Skip this cell and continue
                continue
                    
    except Exception as e:
        st.info(f"H3 boundary visualization not available: {str(e)[:100]}...")
        # Continue without boundaries - will use center points
        pass
    
    return boundaries_data

def create_h3_hexagon_map_pydeck(df, resolution, map_style="open-street-map"):
    """Create true H3 hexagon map using PyDeck H3HexagonLayer"""
    h3_column = f'H3_LEVEL_{resolution}'
    
    # Check if H3 column exists in dataframe
    if h3_column not in df.columns:
        st.warning(f"H3 column {h3_column} not found in data. Creating H3 indices on-the-fly...")
        return create_h3_on_the_fly(df, resolution, map_style)
    
    # Aggregate data by H3 cell
    h3_agg = df.groupby(h3_column).agg({
        'ANNUAL_DONATION_AMOUNT': ['sum', 'mean', 'count'],
        'CUMULATIVE_DONATION_AMOUNT': 'sum',
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    }).round(2)
    
    h3_agg.columns = ['total_annual', 'avg_annual', 'donor_count', 'total_cumulative', 'center_lat', 'center_lon']
    h3_agg = h3_agg.reset_index()
    
    # Debug: Check if we have valid aggregated data
    if h3_agg.empty:
        st.error("❌ No H3 aggregated data available")
        return create_simple_scatter_map(df, map_style)
    
    # Debug info moved to sidebar
    
    st.success(f"✅ Creating TRUE H3 hexagons using PyDeck for {len(h3_agg)} spatial clusters!")
    
    # Define color function based on total annual donations (following user's example)
    def get_color_for_donations(donation_amount, max_donation):
        # Normalize to 0-1 range
        normalized = min(1.0, max(0.0, donation_amount / max_donation)) if max_donation > 0 else 0
        
        # Color scale from light orange to dark red
        red = int(255 * (0.8 + 0.2 * normalized))  # 204-255
        green = int(255 * (0.6 * (1 - normalized)))  # 153 down to 0
        blue = int(255 * (0.2 * (1 - normalized)))   # 51 down to 0
        
        return [red, green, blue]
    
    # Apply color function
    max_donation = h3_agg['total_annual'].max() if not h3_agg.empty else 1
    h3_agg['color'] = h3_agg['total_annual'].apply(lambda x: get_color_for_donations(x, max_donation))
    
    # Format currency columns for tooltip display
    h3_agg['total_annual_formatted'] = h3_agg['total_annual'].apply(lambda x: f"{x:,.0f}")
    h3_agg['avg_annual_formatted'] = h3_agg['avg_annual'].apply(lambda x: f"{x:,.0f}")
    h3_agg['total_cumulative_formatted'] = h3_agg['total_cumulative'].apply(lambda x: f"{x:,.0f}")
    
    # Calculate map center
    avg_latitude = h3_agg['center_lat'].mean()
    avg_longitude = h3_agg['center_lon'].mean()
    
    # Define tooltip - PyDeck format
    tooltip = {
        "html": 
            "<b>H3 Cell:</b> {" + h3_column + "}<br/>"
            "<b>Donors:</b> {donor_count}<br/>"
            "<b>Total Annual:</b> ${total_annual_formatted}<br/>"
            "<b>Avg Annual:</b> ${avg_annual_formatted}<br/>"
            "<b>Total Cumulative:</b> ${total_cumulative_formatted}<br/>",
        "style": {
            "backgroundColor": 'rgba(255, 87, 0, 0.9)',
            "color": "white",
            "fontSize": "14px",
            "padding": "10px",
            "borderRadius": "5px"
        }
    }
    
    # Create PyDeck H3 layer
    h3_layer = pdk.Layer(
        "H3HexagonLayer",
        h3_agg,
        pickable=True,
        stroked=True,
        filled=True,
        extruded=False,
        opacity=0.7,
        get_hexagon=h3_column,  # Use the H3 index column
        get_fill_color="color",  # Use the dynamically calculated color
        get_line_color=[255, 255, 255],  # White borders
        line_width_min_pixels=1,
    )
    
    # Create the deck
    deck = pdk.Deck(
        layers=[h3_layer],
        tooltip=tooltip,
        initial_view_state=pdk.ViewState(
            latitude=avg_latitude,
            longitude=avg_longitude,
            zoom=10,
            pitch=0
        ),
        map_style='mapbox://styles/mapbox/light-v9' if map_style != "white-bg" else None
    )
    
    return deck

# Keep the old function as fallback
def create_h3_hexagon_map(df, resolution, map_style="open-street-map"):
    """Wrapper that tries PyDeck first, falls back to Plotly if needed"""
    try:
        # Try PyDeck first for true H3 hexagons
        return create_h3_hexagon_map_pydeck(df, resolution, map_style)
    except Exception as e:
        st.warning(f"⚠️ PyDeck H3 visualization failed: {str(e)}")
        st.info("🔄 Falling back to enhanced marker visualization...")
        return create_h3_hexagon_map_plotly_fallback(df, resolution, map_style)

def create_h3_hexagon_map_plotly_fallback(df, resolution, map_style="open-street-map"):
    """Fallback H3 map using Plotly markers"""
    h3_column = f'H3_LEVEL_{resolution}'
    
    # Check if H3 column exists in dataframe
    if h3_column not in df.columns:
        st.warning(f"H3 column {h3_column} not found in data. Creating H3 indices on-the-fly...")
        return create_h3_on_the_fly(df, resolution, map_style)
    
    # Aggregate data by H3 cell
    h3_agg = df.groupby(h3_column).agg({
        'ANNUAL_DONATION_AMOUNT': ['sum', 'mean', 'count'],
        'CUMULATIVE_DONATION_AMOUNT': 'sum',
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    }).round(2)
    
    h3_agg.columns = ['total_annual', 'avg_annual', 'donor_count', 'total_cumulative', 'center_lat', 'center_lon']
    h3_agg = h3_agg.reset_index()
    
    # Debug: Check if we have valid aggregated data
    if h3_agg.empty:
        st.error("❌ No H3 aggregated data available")
        return create_simple_scatter_map(df, map_style)
    
    st.info(f"📊 Showing {len(h3_agg)} H3 spatial clusters as enhanced markers (Plotly fallback)")
    
    # Create reliable scatter plot
    fig = px.scatter_mapbox(
        h3_agg,
        lat='center_lat',
        lon='center_lon',
        size='donor_count',
        color='total_annual',
        hover_data={
            h3_column: True,
            'donor_count': True,
            'total_annual': ':.0f',
            'avg_annual': ':.0f',
            'total_cumulative': ':.0f',
            'center_lat': False,
            'center_lon': False
        },
        color_continuous_scale='Oranges',
        size_max=60,
        zoom=10,
        mapbox_style="white-bg" if map_style == "white-bg" else map_style,
        title=f'H3 Spatial Analysis (Resolution Level {resolution}) - {len(h3_agg)} Clusters - Enhanced Markers',
        labels={
            'total_annual': 'Total Annual Donations ($)',
            'donor_count': 'Number of Donors'
        }
    )
    
    # Simple, reliable marker styling
    fig.update_traces(
        marker=dict(
            opacity=0.8,
            line=dict(width=1, color='white')
        )
    )
    
    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="white-bg" if map_style == "white-bg" else map_style,
            center=dict(lat=df['LATITUDE'].mean(), lon=df['LONGITUDE'].mean()),
            zoom=10
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def create_point_map_pydeck(df, venues_df=None, map_style="open-street-map"):
    """Create a point map using PyDeck ScatterplotLayer for better performance and display"""
    import pandas as pd
    
    if df.empty:
        st.warning("No donor data available for point map")
        return None
    
    # Remove rows with null coordinates
    valid_df = df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
    if valid_df.empty:
        st.warning("No valid coordinates available for point map")
        return None
    
    st.success(f"✅ Creating PyDeck point map with {len(valid_df)} donor locations!")
    
    # Add color coding by donor segment (following user's example format)
    def get_color_for_segment(segment):
        color_map = {
            'Major Donor': [255, 0, 0, 180],      # Red
            'Mid-Level Donor': [255, 140, 0, 180],  # Orange  
            'Annual Donor': [0, 166, 81, 180]      # Green
        }
        return color_map.get(segment, [128, 128, 128, 180])  # Gray default
    
    # Apply color function and convert to basic Python types
    valid_df['color'] = valid_df['DONOR_SEGMENT'].apply(get_color_for_segment)
    
    # Convert to basic Python data types for PyDeck serialization
    pydeck_data = []
    for _, row in valid_df.iterrows():
        pydeck_data.append({
            'LONGITUDE': float(row['LONGITUDE']),
            'LATITUDE': float(row['LATITUDE']),
            'FULL_NAME': str(row['FULL_NAME']),
            'DONOR_SEGMENT': str(row['DONOR_SEGMENT']),
            'ANNUAL_DONATION_AMOUNT': float(row['ANNUAL_DONATION_AMOUNT']),
            'CUMULATIVE_DONATION_AMOUNT': float(row['CUMULATIVE_DONATION_AMOUNT']),
            'ZIP_CODE': str(row['ZIP_CODE']),
            'GRADUATION_YEAR': int(row['GRADUATION_YEAR']) if pd.notna(row['GRADUATION_YEAR']) else 2000,
            'color': list(row['color']),  # Convert to list
            # Pre-formatted strings for tooltip display
            'ANNUAL_FORMATTED': f"${float(row['ANNUAL_DONATION_AMOUNT']):,.0f}",
            'CUMULATIVE_FORMATTED': f"${float(row['CUMULATIVE_DONATION_AMOUNT']):,.0f}"
        })
    
    # Calculate map center
    avg_latitude = float(valid_df['LATITUDE'].mean())
    avg_longitude = float(valid_df['LONGITUDE'].mean())
    
    # Create donor points layer
    donor_layer = pdk.Layer(
        type='ScatterplotLayer',
        data=pydeck_data,
        pickable=True,
        get_position=['LONGITUDE', 'LATITUDE'],
        get_color='color',
        get_radius='ANNUAL_DONATION_AMOUNT',  # Size by donation amount
        radius_scale=0.05,  # Scale down the radius  
        radius_min_pixels=4,
        radius_max_pixels=20,
        opacity=0.6,
        auto_highlight=True,
        id='donor_points'
    )
    
    layers = [donor_layer]
    
    # Add venues layer if provided
    if venues_df is not None and not venues_df.empty:
        venues_valid = venues_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        if not venues_valid.empty:
            # Convert venues to basic Python data types
            venue_pydeck_data = []
            for _, row in venues_valid.iterrows():
                venue_pydeck_data.append({
                    'LONGITUDE': float(row['LONGITUDE']),
                    'LATITUDE': float(row['LATITUDE']),
                    'VENUE_NAME': str(row['VENUE_NAME']),
                    'VENUE_TYPE': str(row['VENUE_TYPE']),
                    'CAPACITY': int(row['CAPACITY']) if pd.notna(row['CAPACITY']) else 0,
                    'PRICE_RANGE': str(row['PRICE_RANGE']),
                    'RATING': float(row['RATING']) if pd.notna(row['RATING']) else 0.0,
                    'color': [128, 0, 128, 255],  # Purple
                    # Venue-specific fields for tooltip
                    'FULL_NAME': f"🏛️ {str(row['VENUE_NAME'])}",
                    'DONOR_SEGMENT': f"Event Venue - {str(row['VENUE_TYPE'])}",
                    'ANNUAL_FORMATTED': f"Capacity: {int(row['CAPACITY']) if pd.notna(row['CAPACITY']) else 'N/A'}",
                    'CUMULATIVE_FORMATTED': f"Rating: {float(row['RATING']) if pd.notna(row['RATING']) else 'N/A'}/5",
                    'ZIP_CODE': str(row['PRICE_RANGE']),
                    'GRADUATION_YEAR': 'Venue'
                })
            
            venue_layer = pdk.Layer(
                type='ScatterplotLayer',
                data=venue_pydeck_data,
                pickable=True,
                get_position=['LONGITUDE', 'LATITUDE'],
                get_color='color',
                get_radius=400,  # Fixed size for venues
                opacity=0.9,
                auto_highlight=True,
                id='venue_points'
            )
            layers.append(venue_layer)
    
    # Define adaptive tooltip (works for both donors and venues)
    tooltip = {
        "html": 
            "<b>Name:</b> {FULL_NAME}<br/>"
            "<b>Type:</b> {DONOR_SEGMENT}<br/>"
            "<b>Annual/Capacity:</b> {ANNUAL_FORMATTED}<br/>"
            "<b>Cumulative/Rating:</b> {CUMULATIVE_FORMATTED}<br/>"
            "<b>ZIP/Price:</b> {ZIP_CODE}<br/>"
            "<b>Year/Category:</b> {GRADUATION_YEAR}",
        "style": {
            "backgroundColor": 'rgba(0, 166, 81, 0.9)',
            "color": "white",
            "fontSize": "14px",
            "padding": "10px",
            "borderRadius": "5px"
        }
    }
    
    # Debug: Show sample tooltip data
    if len(pydeck_data) > 0:
        sample = pydeck_data[0]
        st.caption(f"📋 Sample donor: {sample.get('FULL_NAME', 'Missing')} | {sample.get('ANNUAL_FORMATTED', 'Missing')}")
    
    # Create the deck (following user's example pattern)
    deck = pdk.Deck(
        map_provider='mapbox',
        api_keys={"mapbox": ''},  # Empty like in user's example
        map_style='mapbox://styles/mapbox/light-v11' if map_style != "white-bg" else None,
        layers=layers,
        tooltip=tooltip,
        initial_view_state=pdk.ViewState(
            latitude=avg_latitude,
            longitude=avg_longitude,
            zoom=10,
            pitch=0
        )
    )
    
    return deck

def create_point_map(df, venues_df=None, map_style="open-street-map"):
    """Wrapper that tries PyDeck first, falls back to Plotly if needed"""
    try:
        # Try PyDeck first for better point visualization
        return create_point_map_pydeck(df, venues_df, map_style)
    except Exception as e:
        st.warning(f"⚠️ PyDeck point visualization failed: {str(e)}")
        st.info("🔄 Falling back to Plotly point visualization...")
        return create_point_map_plotly_fallback(df, venues_df, map_style)

def create_point_map_plotly_fallback(df, venues_df=None, map_style="open-street-map"):
    """Fallback point map using Plotly"""
    
    # Create donor points with color coding by segment
    color_map = {
        'Major Donor': '#ff0000',      # Red
        'Mid-Level Donor': '#ff8c00',  # Orange 
        'Annual Donor': '#00a651'      # Green
    }
    
    df = df.copy()
    df['color'] = df['DONOR_SEGMENT'].map(color_map)
    df['size'] = np.clip(df['ANNUAL_DONATION_AMOUNT'] / 500, 3, 20)  # Size based on donation
    
    fig = px.scatter_mapbox(
        df,
        lat='LATITUDE',
        lon='LONGITUDE',
        color='DONOR_SEGMENT',
        size='size',
        hover_data={
            'FULL_NAME': True,
            'ANNUAL_DONATION_AMOUNT': ':.0f',
            'CUMULATIVE_DONATION_AMOUNT': ':.0f',
            'GRADUATION_YEAR': True,
            'MAJOR': True,
            'ZIP_CODE': True,
            'size': False,
            'LATITUDE': False,
            'LONGITUDE': False
        },
        color_discrete_map=color_map,
        zoom=10,
        mapbox_style="white-bg" if map_style == "white-bg" else map_style,
        title=f'Individual Donor Locations - {"No External Maps" if map_style == "white-bg" else map_style}',
        labels={
            'ANNUAL_DONATION_AMOUNT': 'Annual Donation ($)',
            'CUMULATIVE_DONATION_AMOUNT': 'Cumulative Donation ($)'
        }
    )
    
    # Add venues if provided
    if venues_df is not None and not venues_df.empty:
        fig.add_trace(
            px.scatter_mapbox(
                venues_df,
                lat='LATITUDE',
                lon='LONGITUDE',
                hover_data={
                    'VENUE_NAME': True,
                    'VENUE_TYPE': True,
                    'CAPACITY': True,
                    'PRICE_RANGE': True,
                    'RATING': True,
                    'LATITUDE': False,
                    'LONGITUDE': False
                },
                color_discrete_sequence=['purple']
            ).data[0]
        )
        fig.data[-1].name = 'Event Venues'
        fig.data[-1].marker.symbol = 'star'
        fig.data[-1].marker.size = 15
    
    # Center the map on Greenville
    fig.update_layout(
        mapbox=dict(
            center=dict(lat=df['LATITUDE'].mean(), lon=df['LONGITUDE'].mean()),
            zoom=10
        ),
        height=600,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def create_static_map_image(df, venues_df=None, map_type="points", h3_resolution=8, map_style="open-street-map"):
    """Create a static map image for download"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import numpy as np
        import io
        
        if df.empty:
            return None
            
        if map_type == "points":
            # Create static point map
            color_map = {
                'Major Donor': '#ff0000',      # Red
                'Mid-Level Donor': '#ff8c00',  # Orange 
                'Annual Donor': '#00a651'      # Green
            }
            
            df_copy = df.copy()
            df_copy['size'] = np.clip(df_copy['ANNUAL_DONATION_AMOUNT'] / 500, 5, 25)
            
            fig = px.scatter_mapbox(
                df_copy,
                lat='LATITUDE',
                lon='LONGITUDE',
                color='DONOR_SEGMENT',
                size='size',
                hover_data={
                    'FULL_NAME': True,
                    'ANNUAL_DONATION_AMOUNT': ':.0f',
                    'ZIP_CODE': True,
                    'size': False,
                    'LATITUDE': False,
                    'LONGITUDE': False
                },
                color_discrete_map=color_map,
                mapbox_style="open-street-map" if map_style != "white-bg" else "white-bg",
                title=f'Alumni Donor Locations - {len(df)} Records',
                width=1200,
                height=800
            )
            
            # Add venues if provided
            if venues_df is not None and not venues_df.empty:
                fig.add_trace(go.Scattermapbox(
                    lat=venues_df['LATITUDE'],
                    lon=venues_df['LONGITUDE'],
                    mode='markers',
                    marker=dict(size=15, color='purple', symbol='star'),
                    text=venues_df['VENUE_NAME'],
                    name='Event Venues',
                    showlegend=True
                ))
                
        else:  # H3 hexagon map
            # Create static H3 visualization using plotly fallback
            h3_column = f'H3_LEVEL_{h3_resolution}'
            if h3_column in df.columns:
                h3_agg = df.groupby(h3_column).agg({
                    'LATITUDE': 'mean',
                    'LONGITUDE': 'mean',
                    'ANNUAL_DONATION_AMOUNT': 'sum',
                    'DONOR_ID': 'count'
                }).reset_index()
                
                h3_agg.columns = [h3_column, 'latitude', 'longitude', 'total_annual', 'donor_count']
                
                fig = px.scatter_mapbox(
                    h3_agg,
                    lat='latitude',
                    lon='longitude',
                    size='total_annual',
                    color='total_annual',
                    hover_data={'donor_count': True, 'total_annual': ':.0f'},
                    color_continuous_scale='Reds',
                    mapbox_style="open-street-map" if map_style != "white-bg" else "white-bg",
                    title=f'Alumni H3 Analysis (Level {h3_resolution}) - {len(h3_agg)} Cells',
                    width=1200,
                    height=800
                )
            else:
                return None
        
        # Center the map
        fig.update_layout(
            mapbox=dict(
                center=dict(lat=df['LATITUDE'].mean(), lon=df['LONGITUDE'].mean()),
                zoom=9
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            font=dict(size=12)
        )
        
        # Convert to image bytes
        img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
        return img_bytes
        
    except Exception as e:
        error_msg = str(e)
        if "Kaleido" in error_msg or "kaleido" in error_msg:
            st.error("🚫 **Map Image Download Not Available in Streamlit in Snowflake**")
            st.info("""
            **Alternative Options:**
            1. **Use Browser Screenshot**: Take a screenshot of the current map view
            2. **Download Data**: Use the CSV downloads to recreate maps elsewhere
            3. **Use Text Report**: The '📊 Map + Table Report' includes recreation instructions
            4. **Run Standalone**: The standalone Streamlit app supports image downloads
            """)
        else:
            st.warning(f"Could not generate static map image: {error_msg}")
        return None

def create_charts(df):
    """Create various charts for analysis"""
    
    # Donations by graduation year
    grad_year_data = df.groupby('GRADUATION_YEAR').agg({
        'ANNUAL_DONATION_AMOUNT': ['sum', 'mean', 'count']
    }).round(2)
    grad_year_data.columns = ['total_annual', 'avg_annual', 'donor_count']
    grad_year_data = grad_year_data.reset_index()
    
    fig1 = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total Annual Donations by Graduation Year', 'Average Donation by Graduation Year')
    )
    
    fig1.add_trace(
        go.Bar(x=grad_year_data['GRADUATION_YEAR'], y=grad_year_data['total_annual'],
               name='Total Annual Donations', marker_color='#F56500'),
        row=1, col=1
    )
    
    fig1.add_trace(
        go.Bar(x=grad_year_data['GRADUATION_YEAR'], y=grad_year_data['avg_annual'],
               name='Average Annual Donation', marker_color='#522D80'),
        row=1, col=2
    )
    
    fig1.update_layout(height=400, showlegend=False, title_text="Donation Analysis by Graduation Year")
    
    # Donations by zip code
    zip_data = df.groupby('ZIP_CODE').agg({
        'ANNUAL_DONATION_AMOUNT': ['sum', 'count']
    }).round(2)
    zip_data.columns = ['total_annual', 'donor_count']
    zip_data = zip_data.reset_index().sort_values('total_annual', ascending=False)
    
    fig2 = px.bar(
        zip_data.head(10), 
        x='ZIP_CODE', 
        y='total_annual',
        title='Top 10 Zip Codes by Total Annual Donations',
        color='total_annual',
        color_continuous_scale='oranges',
        labels={'total_annual': 'Total Annual Donations ($)'}
    )
    fig2.update_layout(height=400)
    
    # Donor segment distribution
    segment_data = df['DONOR_SEGMENT'].value_counts()
    fig3 = px.pie(
        values=segment_data.values,
        names=segment_data.index,
        title='Donor Segment Distribution',
        color_discrete_sequence=['#F56500', '#522D80', '#00A651']
    )
    fig3.update_layout(height=400)
    
    # Major distribution
    major_data = df.groupby('MAJOR').agg({
        'ANNUAL_DONATION_AMOUNT': 'sum'
    }).round(2).sort_values('ANNUAL_DONATION_AMOUNT', ascending=False).head(10)
    
    fig4 = px.bar(
        x=major_data.index,
        y=major_data['ANNUAL_DONATION_AMOUNT'],
        title='Top 10 Majors by Total Annual Donations',
        color=major_data['ANNUAL_DONATION_AMOUNT'],
        color_continuous_scale='purples',
        labels={'y': 'Total Annual Donations ($)', 'x': 'Major'}
    )
    fig4.update_layout(height=400, xaxis_tickangle=-45)
    
    return fig1, fig2, fig3, fig4

def main():
    # Header
    st.markdown('<h1 class="main-header">🐅 Alumni Event Location Targeting</h1>', 
                unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Greenville, SC Area Analysis - Streamlit in Snowflake</h2>', 
                unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data from Snowflake..."):
        try:
            donors_df = load_donor_data()
            venues_df = load_venue_data()
            overview_data = load_overview_data()
            
            # Check if we have the required columns
            required_columns = ['LATITUDE', 'LONGITUDE', 'ANNUAL_DONATION_AMOUNT', 'DONOR_SEGMENT']
            missing_columns = [col for col in required_columns if col not in donors_df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns in donor data: {missing_columns}")
                st.info("Please run the data generation scripts to create the proper table structure.")
                st.stop()
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("Please ensure the database tables have been created and populated.")
            st.info("Run the SQL scripts in order: 01_setup_database.sql → 02_create_tables.sql → 03_generate_donor_data.sql → 04_generate_venue_data.sql → 05_create_analytics_summary.sql")
            st.stop()
    
    if donors_df.empty:
        st.error("No donor data found. Please run the data generation scripts first.")
        st.stop()
    
    # Sidebar filters
    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.sidebar.markdown('<h3 class="sub-header">🎯 Targeting Filters</h3>', unsafe_allow_html=True)
    
    # Zip code filter with controls
    st.sidebar.markdown("**Select Zip Codes**")
    col_zip1, col_zip2 = st.sidebar.columns(2)
    with col_zip1:
        if st.button("Select All Zips", key="select_all_zips"):
            st.session_state.zip_codes = sorted(donors_df['ZIP_CODE'].unique())
    with col_zip2:
        if st.button("Clear All Zips", key="clear_all_zips"):
            st.session_state.zip_codes = []
    
    # Initialize session state if not exists
    if 'zip_codes' not in st.session_state:
        st.session_state.zip_codes = ['29680', '29650', '29607', '29681']
    
    zip_codes = st.sidebar.multiselect(
        "",
        options=sorted(donors_df['ZIP_CODE'].unique()),
        default=st.session_state.zip_codes,
        key="zip_multiselect",
        help="Focus on specific zip codes for event targeting"
    )
    st.session_state.zip_codes = zip_codes
    
    # Graduation year filter
    min_year = int(donors_df['GRADUATION_YEAR'].min())
    max_year = int(donors_df['GRADUATION_YEAR'].max())
    grad_years = st.sidebar.slider(
        "Graduation Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        help="Target specific graduation year ranges"
    )
    
    # Donation amount filter
    min_donation = float(donors_df['ANNUAL_DONATION_AMOUNT'].min())
    max_donation = float(donors_df['ANNUAL_DONATION_AMOUNT'].max())
    donation_range = st.sidebar.slider(
        "Annual Donation Range ($)",
        min_value=min_donation,
        max_value=max_donation,
        value=(min_donation, max_donation),
        format="$%.0f",
        help="Filter by donation capacity"
    )
    
    # Donor segment filter with controls
    st.sidebar.markdown("**Donor Segments**")
    col_seg1, col_seg2 = st.sidebar.columns(2)
    with col_seg1:
        if st.button("Select All Segments", key="select_all_segments"):
            st.session_state.donor_segments = list(donors_df['DONOR_SEGMENT'].unique())
    with col_seg2:
        if st.button("Clear All Segments", key="clear_all_segments"):
            st.session_state.donor_segments = []
    
    # Initialize session state if not exists
    if 'donor_segments' not in st.session_state:
        st.session_state.donor_segments = list(donors_df['DONOR_SEGMENT'].unique())
    
    donor_segments = st.sidebar.multiselect(
        "",
        options=donors_df['DONOR_SEGMENT'].unique(),
        default=st.session_state.donor_segments,
        key="segment_multiselect",
        help="Focus on specific donor segments"
    )
    st.session_state.donor_segments = donor_segments
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = apply_filters(donors_df, zip_codes, grad_years, donation_range, donor_segments)
    
    # Debug section in sidebar (after filters are applied)
    with st.sidebar.expander("🔍 H3 Data Debug", expanded=False):
        if not filtered_df.empty:
            # Show debug info for current filtered data
            st.write(f"**Filtered Data:** {len(filtered_df):,} records")
            st.write(f"**Zip Codes:** {sorted(filtered_df['ZIP_CODE'].unique())}")
            st.write(f"**Donor Segments:** {sorted(filtered_df['DONOR_SEGMENT'].unique())}")
            st.write(f"**Lat Range:** {filtered_df['LATITUDE'].min():.4f} to {filtered_df['LATITUDE'].max():.4f}")
            st.write(f"**Lon Range:** {filtered_df['LONGITUDE'].min():.4f} to {filtered_df['LONGITUDE'].max():.4f}")
            
            # H3 info if available
            for resolution in [7, 8, 9]:
                h3_col = f'H3_LEVEL_{resolution}'
                if h3_col in filtered_df.columns:
                    unique_h3 = filtered_df[h3_col].nunique()
                    st.write(f"**H3 Level {resolution}:** {unique_h3} unique cells")
        else:
            st.write("No data matches current filters")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Donors",
            value=f"{len(filtered_df):,}",
            delta=f"{len(filtered_df) - len(donors_df):,} from full dataset"
        )
    
    with col2:
        total_annual = filtered_df['ANNUAL_DONATION_AMOUNT'].sum()
        st.metric(
            label="💰 Total Annual Donations",
            value=f"${total_annual:,.0f}",
            delta=f"${filtered_df['ANNUAL_DONATION_AMOUNT'].mean():,.0f} average"
        )
    
    with col3:
        major_donors = len(filtered_df[filtered_df['DONOR_SEGMENT'] == 'Major Donor'])
        st.metric(
            label="🌟 Major Donors",
            value=f"{major_donors:,}",
            delta=f"{major_donors/len(filtered_df)*100:.1f}% of filtered donors"
        )
    
    with col4:
        if not filtered_df.empty:
            top_zip = filtered_df.groupby('ZIP_CODE')['ANNUAL_DONATION_AMOUNT'].sum().idxmax()
            donor_count = len(filtered_df[filtered_df['ZIP_CODE'] == top_zip])
        else:
            top_zip = "No data"
            donor_count = 0
            
        st.metric(
            label="🎯 Top Zip Code",
            value=top_zip,
            delta=f"{donor_count} donors"
        )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Geographic Analysis", 
        "📊 Analytics Dashboard", 
        "🏢 Event Venues", 
        "📋 Donor Details"
    ])
    
    with tab1:
        st.markdown('<h3 class="sub-header">Geographic Distribution Analysis</h3>', 
                   unsafe_allow_html=True)
        
        # Map troubleshooting info
        with st.expander("🗺️ Map Issues? Troubleshooting Guide"):
            st.markdown("""
            **🔴 ISSUE 1: Not seeing TRUE HEXAGONS?**
            - **NEW**: App now uses PyDeck H3HexagonLayer for true hexagon visualization!
            - If you see enhanced markers instead: PyDeck may not be available or failed to load
            - Check for "Creating TRUE H3 hexagons using PyDeck" success message
            - Falls back to enhanced markers if PyDeck fails
            - **Best solution**: PyDeck provides native H3 hexagon support
            
            **🔴 ISSUE 2: No underlying map geography (streets, boundaries)?**
            - Your Streamlit in Snowflake environment may block external map tiles
            - **Solutions:**
              1. Try `white-bg` style (no external dependencies)
              2. Try different map styles: `carto-positron`, `carto-darkmatter`
              3. Use the standalone Streamlit app instead (no SiS restrictions)
            
            **🔴 ISSUE 3: Some map styles don't work?**
            - `stamen-terrain` often fails in corporate environments
            - Stick to `carto-positron` or `white-bg` for reliability
            - Corporate firewalls commonly block certain tile servers
            """)
        
        st.markdown("---")
        
        # Map controls
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        
        with col1:
            map_type = st.selectbox(
                "Map Type",
                ["H3 Hexagonal Grid", "Individual Points"],
                help="Choose between H3 hexagonal aggregation or individual donor points"
            )
        
        with col2:
            # Initialize h3_resolution with default value
            h3_resolution = 8  # Default value
            if map_type == "H3 Hexagonal Grid":
                h3_resolution = st.slider(
                    "H3 Resolution",
                    min_value=7,
                    max_value=9,
                    value=8,
                    help="Higher resolution = smaller hexagons, more detail"
                )
        
        with col3:
            show_venues = st.checkbox("Show Venues", value=True)
            
        with col4:
            map_style = st.selectbox(
                "Map Style",
                ["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain", "white-bg"],
                index=0,
                help="Try different map styles if geography doesn't load. Use 'white-bg' if no external maps work."
            )
        
        # Display map
        if map_type == "H3 Hexagonal Grid":
            result = create_h3_hexagon_map(filtered_df, h3_resolution, map_style)
            if result is not None:
                # Check if it's a PyDeck deck or Plotly figure
                if hasattr(result, 'layers'):  # PyDeck deck
                    st.pydeck_chart(result)
                else:  # Plotly figure
                    st.plotly_chart(result, use_container_width=True)
                
                # H3 Hexagon Map Legend
                with st.expander("🔷 H3 Hexagon Map Guide", expanded=True):
                    st.write("**What you're seeing:** Geographic areas divided into hexagonal cells, with donor data aggregated by location.")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**🎨 Color Scale:**")
                        st.write("🟡 **Light Yellow/Orange:** Lower total donations")
                        st.write("🟠 **Orange:** Moderate donations") 
                        st.write("🔴 **Dark Red:** Highest total donations")
                    
                    with col2:
                        st.write("**📊 Each Hexagon Shows:**")
                        st.write("• Total annual donations in that area")
                        st.write("• Number of donors")
                        st.write("• Average donation amounts")
                        st.write("• Geographic concentration")
                    
                    with col3:
                        st.write("**🎯 Strategic Workflow:**")
                        st.write("1. **Identify high-value areas** (dark red hexagons)")
                        st.write("2. **Switch to Individual Points** map")
                        st.write("3. **Find nearby venues** (purple stars)")
                        st.info("💡 **Pro Tip:** Use hex view for area analysis, then switch to points to find venues!")
            else:
                st.error("❌ Unable to create H3 hexagon map - check data and debug info above")
        else:
            venues_to_show = venues_df if show_venues else None
            result = create_point_map(filtered_df, venues_to_show, map_style)
            if result is not None:
                # Check if it's a PyDeck deck or Plotly figure
                if hasattr(result, 'layers'):  # PyDeck deck
                    st.pydeck_chart(result)
                else:  # Plotly figure
                    st.plotly_chart(result, use_container_width=True)
                
                # Point Map Legend
                with st.expander("🎯 Individual Donor Map Guide", expanded=True):
                    st.write("**What you're seeing:** Each dot represents one individual donor at their specific location.")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**🎨 Dot Colors (Donor Segments):**")
                        st.write("🔴 **Red = Major Donors:** `$10,000+` annually")
                        st.write("🟠 **Orange = Mid-Level:** `$1,000 - $9,999` annually")
                        st.write("🟢 **Green = Annual Donors:** `$25 - $999` annually")
                    
                    with col2:
                        st.write("**📏 Dot Sizes (Annual Donation):**")
                        st.write("⚫ **Large dots:** Higher annual giving")
                        st.write("🔘 **Medium dots:** Moderate annual giving")
                        st.write("• **Small dots:** Lower annual giving")
                    
                    with col3:
                        st.write("**🏛️ Purple Stars:** Event Venues")
                        st.success("🔍 **Pro Tip:** Large red dots = premium event targets!")
            else:
                st.error("❌ Unable to create point map - check data and debug info above")
        
        # Data table section
        st.markdown("---")
        st.markdown('<h3 class="sub-header">📋 Individual Donor Records</h3>', 
                   unsafe_allow_html=True)
        
        # Download and data controls
        col_download1, col_download2, col_download3, col_download4, col_download5 = st.columns([2, 2, 2, 2, 2])
        
        with col_download1:
            # Download filtered data as CSV
            if not filtered_df.empty:
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Filtered Data",
                    data=csv_data,
                    file_name=f"alumni_filtered_{len(filtered_df)}_records.csv",
                    mime="text/csv",
                    help="Download current filtered dataset as CSV"
                )
        
        with col_download2:
            # Download all data as CSV
            if not donors_df.empty:
                csv_all_data = donors_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Complete Data",
                    data=csv_all_data,
                    file_name=f"alumni_complete_{len(donors_df)}_records.csv",
                    mime="text/csv",
                    help="Download complete dataset as CSV"
                )
        
        with col_download3:
            # Download combined map + table report
            if not filtered_df.empty:
                # Create comprehensive report
                import io
                from datetime import datetime
                
                report_buffer = io.StringIO()
                report_buffer.write("ALUMNI EVENT TARGETING REPORT\n")
                report_buffer.write("="*50 + "\n")
                report_buffer.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                report_buffer.write(f"Total Records Analyzed: {len(filtered_df):,}\n")
                report_buffer.write(f"Map Center: {filtered_df['LATITUDE'].mean():.6f}, {filtered_df['LONGITUDE'].mean():.6f}\n")
                report_buffer.write(f"Geographic Bounds: {filtered_df['LATITUDE'].min():.6f} to {filtered_df['LATITUDE'].max():.6f} (Lat)\n")
                report_buffer.write(f"                   {filtered_df['LONGITUDE'].min():.6f} to {filtered_df['LONGITUDE'].max():.6f} (Lon)\n\n")
                
                # Map visualization recreation instructions
                report_buffer.write("MAP VISUALIZATION RECREATION\n")
                report_buffer.write("-"*35 + "\n")
                report_buffer.write("This report includes data that can be used to recreate the interactive maps:\n\n")
                report_buffer.write("H3 HEXAGON MAP INSTRUCTIONS:\n")
                report_buffer.write("- Use PyDeck H3HexagonLayer with the H3 spatial analysis data below\n")
                report_buffer.write("- Color scale: Light orange to dark red based on total annual donations\n")
                report_buffer.write("- Opacity: 0.7 with white borders\n")
                report_buffer.write("- Map style: mapbox://styles/mapbox/light-v11\n\n")
                report_buffer.write("POINT MAP INSTRUCTIONS:\n")
                report_buffer.write("- Use PyDeck ScatterplotLayer with individual donor records below\n")
                report_buffer.write("- Color coding: Major Donors (Red), Mid-Level (Orange), Annual (Green)\n")
                report_buffer.write("- Size: Proportional to annual donation amount\n")
                report_buffer.write("- Opacity: 0.6 with auto-highlight enabled\n\n")
                
                # Summary statistics
                report_buffer.write("SUMMARY STATISTICS\n")
                report_buffer.write("-"*20 + "\n")
                report_buffer.write(f"Total Donors in Analysis: {len(filtered_df):,}\n")
                report_buffer.write(f"Total Annual Donations: ${filtered_df['ANNUAL_DONATION_AMOUNT'].sum():,.2f}\n")
                report_buffer.write(f"Average Annual Donation: ${filtered_df['ANNUAL_DONATION_AMOUNT'].mean():.2f}\n")
                report_buffer.write(f"Total Cumulative Donations: ${filtered_df['CUMULATIVE_DONATION_AMOUNT'].sum():,.2f}\n")
                report_buffer.write(f"Average Cumulative Donation: ${filtered_df['CUMULATIVE_DONATION_AMOUNT'].mean():.2f}\n")
                
                # Geographic distribution
                report_buffer.write(f"\nGEOGRAPHIC DISTRIBUTION\n")
                report_buffer.write("-"*25 + "\n")
                zip_summary = filtered_df.groupby('ZIP_CODE').agg({
                    'ANNUAL_DONATION_AMOUNT': ['count', 'sum', 'mean']
                }).round(2)
                zip_summary.columns = ['Donor_Count', 'Total_Annual', 'Avg_Annual']
                zip_summary = zip_summary.sort_values('Total_Annual', ascending=False)
                report_buffer.write(zip_summary.to_string())
                
                # Donor segments
                report_buffer.write(f"\n\nDONOR SEGMENTS\n")
                report_buffer.write("-"*15 + "\n")
                segment_summary = filtered_df.groupby('DONOR_SEGMENT').agg({
                    'ANNUAL_DONATION_AMOUNT': ['count', 'sum', 'mean']
                }).round(2)
                segment_summary.columns = ['Donor_Count', 'Total_Annual', 'Avg_Annual']
                report_buffer.write(segment_summary.to_string())
                
                # H3 spatial analysis (if available)
                h3_column = f'H3_LEVEL_8'  # Default resolution
                if h3_column in filtered_df.columns:
                    report_buffer.write(f"\n\nH3 SPATIAL ANALYSIS (Resolution 8)\n")
                    report_buffer.write("-"*35 + "\n")
                    h3_summary = filtered_df.groupby(h3_column).agg({
                        'ANNUAL_DONATION_AMOUNT': ['count', 'sum', 'mean'],
                        'LATITUDE': 'mean',
                        'LONGITUDE': 'mean'
                    }).round(4)
                    h3_summary.columns = ['Donor_Count', 'Total_Annual', 'Avg_Annual', 'Center_Lat', 'Center_Lon']
                    h3_summary = h3_summary.sort_values('Total_Annual', ascending=False).head(10)
                    report_buffer.write("Top 10 H3 Cells by Total Annual Donations:\n")
                    report_buffer.write(h3_summary.to_string())
                
                # PyDeck code examples for recreation
                report_buffer.write(f"\n\nPYDECK CODE EXAMPLES FOR MAP RECREATION\n")
                report_buffer.write("-"*45 + "\n")
                report_buffer.write("# H3 HEXAGON MAP CODE:\n")
                report_buffer.write("import pydeck as pdk\n")
                report_buffer.write("import pandas as pd\n\n")
                report_buffer.write("# Load H3 aggregated data from 'H3 SPATIAL ANALYSIS' section above\n")
                report_buffer.write("h3_layer = pdk.Layer(\n")
                report_buffer.write("    'H3HexagonLayer',\n")
                report_buffer.write("    data=h3_data,  # Use H3 spatial analysis data\n")
                report_buffer.write("    get_hexagon='H3_LEVEL_8',\n")
                report_buffer.write("    get_fill_color='[255, 87, 0, opacity_based_on_donations]',\n")
                report_buffer.write("    get_line_color=[255, 255, 255],\n")
                report_buffer.write("    opacity=0.7,\n")
                report_buffer.write("    pickable=True\n")
                report_buffer.write(")\n\n")
                report_buffer.write("# POINT MAP CODE:\n")
                report_buffer.write("point_layer = pdk.Layer(\n")
                report_buffer.write("    'ScatterplotLayer',\n")
                report_buffer.write("    data=donor_data,  # Use individual donor records below\n")
                report_buffer.write("    get_position='[LONGITUDE, LATITUDE]',\n")
                report_buffer.write("    get_color='color_by_segment',  # Red/Orange/Green by segment\n")
                report_buffer.write("    get_radius='ANNUAL_DONATION_AMOUNT',\n")
                report_buffer.write("    radius_scale=0.05,\n")
                report_buffer.write("    opacity=0.6,\n")
                report_buffer.write("    pickable=True\n")
                report_buffer.write(")\n\n")
                
                # Individual donor records
                report_buffer.write(f"INDIVIDUAL DONOR RECORDS\n")
                report_buffer.write("-"*25 + "\n")
                report_buffer.write("CSV Format (copy to recreate maps):\n")
                report_buffer.write(filtered_df.to_csv(index=False))
                
                report_content = report_buffer.getvalue().encode('utf-8')
                report_buffer.close()
                
                st.download_button(
                    label="📊 Map + Table Report",
                    data=report_content,
                    file_name=f"alumni_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    help="Download comprehensive analysis report with map data and table"
                )
        
        with col_download4:
            # Download current map as image
            if not filtered_df.empty:
                st.caption("⚠️ Image download may not work in SiS")
                from datetime import datetime
                
                # Determine map type from current view
                current_map_type = "hexagons" if map_type == "H3 Hexagonal Grid" else "points"
                venues_to_show = venues_df if show_venues else None
                
                # Generate map image
                if st.button("🗺️ Generate Map Image", help="Create downloadable PNG of current map view (may not work in SiS environment)"):
                    with st.spinner("Generating map image..."):
                        img_bytes = create_static_map_image(
                            filtered_df, 
                            venues_to_show, 
                            current_map_type, 
                            h3_resolution, 
                            map_style
                        )
                        
                        if img_bytes:
                            st.download_button(
                                label="📥 Download Map PNG",
                                data=img_bytes,
                                file_name=f"alumni_map_{current_map_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                                help="Download current map view as high-resolution PNG image"
                            )
                            st.success("✅ Map image ready for download!")
                        # Error handling is now in create_static_map_image function
        
        with col_download5:
            st.info(f"📊 {len(filtered_df):,} of {len(donors_df):,} records")
        
        # Display data table
        if not filtered_df.empty:
            # Display options
            col_table1, col_table2 = st.columns([1, 3])
            with col_table1:
                show_records = st.selectbox(
                    "Records to display:",
                    [50, 100, 250, 500, "All"],
                    index=0,
                    help="Choose how many records to display in the table"
                )
            
            # Apply display limit
            if show_records == "All":
                display_df = filtered_df
            else:
                display_df = filtered_df.head(show_records)
            
            # Format display columns for better readability
            display_columns = [
                'FULL_NAME', 'ZIP_CODE', 'GRADUATION_YEAR', 'DEGREE', 
                'ANNUAL_DONATION_AMOUNT', 'CUMULATIVE_DONATION_AMOUNT', 
                'DONOR_SEGMENT', 'AGE', 'CITY', 'STATE'
            ]
            
            # Only show columns that exist in the dataframe
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            table_df = display_df[available_columns].copy()
            
            # Format currency columns
            if 'ANNUAL_DONATION_AMOUNT' in table_df.columns:
                table_df['ANNUAL_DONATION_AMOUNT'] = table_df['ANNUAL_DONATION_AMOUNT'].apply(lambda x: f"${x:,.0f}")
            if 'CUMULATIVE_DONATION_AMOUNT' in table_df.columns:
                table_df['CUMULATIVE_DONATION_AMOUNT'] = table_df['CUMULATIVE_DONATION_AMOUNT'].apply(lambda x: f"${x:,.0f}")
            
            # Display the table
            st.dataframe(
                table_df,
                use_container_width=True,
                height=400,
                column_config={
                    "FULL_NAME": "Name",
                    "ZIP_CODE": "Zip",
                    "GRADUATION_YEAR": "Grad Year",
                    "DEGREE": "Degree",
                    "ANNUAL_DONATION_AMOUNT": "Annual Donation",
                    "CUMULATIVE_DONATION_AMOUNT": "Total Lifetime",
                    "DONOR_SEGMENT": "Segment",
                    "AGE": "Age",
                    "CITY": "City",
                    "STATE": "State"
                }
            )
            
            if show_records != "All" and len(filtered_df) > show_records:
                st.info(f"Showing first {show_records} records. Use download button above to get complete data.")
        else:
            st.warning("No donor records match the current filters. Try adjusting your filter criteria.")
    
    with tab2:
        st.markdown('<h3 class="sub-header">Analytics Dashboard</h3>', 
                   unsafe_allow_html=True)
        
        if not filtered_df.empty:
            # Create charts
            fig1, fig2, fig3, fig4 = create_charts(filtered_df)
            
            # Display charts in grid
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig3, use_container_width=True)
            
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("No data matches the current filters. Please adjust your selection.")
    
    with tab3:
        st.markdown('<h3 class="sub-header">Event Venues in Greenville Area</h3>', 
                   unsafe_allow_html=True)
        
        # Venue filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            venue_types = st.multiselect(
                "Venue Types",
                options=venues_df['VENUE_TYPE'].unique(),
                default=venues_df['VENUE_TYPE'].unique()
            )
        
        with col2:
            price_ranges = st.multiselect(
                "Price Ranges",
                options=venues_df['PRICE_RANGE'].unique(),
                default=venues_df['PRICE_RANGE'].unique()
            )
        
        with col3:
            min_capacity = st.number_input(
                "Minimum Capacity",
                min_value=0,
                max_value=int(venues_df['CAPACITY'].max()),
                value=0
            )
        
        # Filter venues
        filtered_venues = venues_df[
            (venues_df['VENUE_TYPE'].isin(venue_types)) &
            (venues_df['PRICE_RANGE'].isin(price_ranges)) &
            (venues_df['CAPACITY'] >= min_capacity)
        ]
        
        # Display venues in a more structured way
        for _, venue in filtered_venues.iterrows():
            with st.expander(f"{venue['VENUE_NAME']} - {venue['VENUE_TYPE']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Capacity", f"{venue['CAPACITY']}")
                    st.metric("Rating", f"{venue['RATING']}/5.0")
                
                with col2:
                    st.write(f"**Price Range:** {venue['PRICE_RANGE']}")
                    st.write(f"**Phone:** {venue['PHONE']}")
                
                with col3:
                    st.write(f"**Address:** {venue['STREET_ADDRESS']}")
                    st.write(f"{venue['CITY']}, {venue['STATE']} {venue['ZIP_CODE']}")
                
                st.write(f"**Description:** {venue['DESCRIPTION']}")
                if venue['WEBSITE']:
                    st.write(f"**Website:** {venue['WEBSITE']}")
    
    with tab4:
        st.markdown('<h3 class="sub-header">Donor Details</h3>', 
                   unsafe_allow_html=True)
        
        # Display filtered donor data
        display_columns = [
            'FULL_NAME', 'ZIP_CODE', 'GRADUATION_YEAR', 'MAJOR', 'DEGREE_TYPE',
            'ANNUAL_DONATION_AMOUNT', 'CUMULATIVE_DONATION_AMOUNT', 'DONOR_SEGMENT'
        ]
        
        st.dataframe(
            filtered_df[display_columns].round(2),
            use_container_width=True,
            hide_index=True
        )
        
        # Summary statistics
        st.markdown("### 📊 Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Geographic Distribution:**")
            zip_summary = filtered_df.groupby('ZIP_CODE').agg({
                'DONOR_ID': 'count',
                'ANNUAL_DONATION_AMOUNT': 'sum'
            }).sort_values('ANNUAL_DONATION_AMOUNT', ascending=False).head(5)
            zip_summary.columns = ['Donor Count', 'Total Annual Donations']
            st.dataframe(zip_summary, use_container_width=True)
        
        with col2:
            st.markdown("**Donor Segments:**")
            segment_summary = filtered_df['DONOR_SEGMENT'].value_counts()
            st.dataframe(segment_summary, use_container_width=True)

if __name__ == "__main__":
    main() 

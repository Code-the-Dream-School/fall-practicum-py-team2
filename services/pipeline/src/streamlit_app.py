import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
from supabase import create_client

# KAN-29 POLISH: Set wider responsive page layout config on script boot
st.set_page_config(page_title="Bay Area Bike Rental Analytics", layout="wide")

# Fetch Data
load_dotenv()

# KAN-29: Wrap raw queries inside an explicit
# try-except guard block to intercept missing keys or database drops safely.

try:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    response = (supabase
                .schema("gold")
                .table("enriched_bks")
                .select("*")
                .execute())
    
    # Check if the database table returned empty data arrays cleanly
    if not response.data:
        st.warning("The database table connected successfully, but contains no records.")
        st.stop()
    df = pd.DataFrame(response.data)

except Exception as e:
    st.error("Data Source Connection Failure")
    st.info(f"Could not connect to Supabase backend: {e}")
    st.stop()  # Safely halts app layout rendering to protect against layout crashes

# Create Header
st.title("Bay Area Bike Rental Data")
st.write("Our project looks at bike rental data in the Bay Area. " \
"By using Lyft's API we can see how many bikes are being rented/returned, including both manual and ebikes. " \
"The data also shows which stations are the most used, and at what times of day.")

# KAN-29 ADVANCED INTERACTIVE FILTERS: Inject structural sidebar filtering
# blocks to isolate live runtime evaluation metrics against new LLM properties.
# Availibility Map

st.sidebar.header("🔍 Enrichment Filtering Matrix")
zone_col = "station_zone_profile"
density_col = "commuter_density_impact"

# Verify if KAN-24 LLM properties are actively populated inside the target table relation
if zone_col in df.columns and density_col in df.columns:
    available_zones = ["All Zones"] + sorted([z for z in df[zone_col].unique() if z])
    available_densities = ["All Impact Levels"] + sorted([d for d in df[density_col].unique() if d])
    
    selected_zone = st.sidebar.selectbox("Filter by Station Zone:", available_zones)
    selected_density = st.sidebar.selectbox("Filter by Commuter Impact:", available_densities)
    
    # Filter the active dataframe slice dynamically down to user configuration bounds
    if selected_zone != "All Zones":
        df = df[df[zone_col] == selected_zone]
    if selected_density != "All Impact Levels":
        df = df[df[density_col] == selected_density]
else:
    st.sidebar.warning("💡 LLM enrichment fields not populated yet. Showing base charts.")

# Availability Map
st.subheader('Bike Map')
# KAN-29 TOOLTIP POLISH: Safely check for and append the enrichment summaries
# right where it makes sense inside the map hover configurations.

df["text"] = ("<br>Ebikes:" + df['num_ebikes_available'].astype(str) + 
              "<br>Manual Bikes:" + 
              df['num_manual_bikes_available'].astype(str))

if "enrichment_summary" in df.columns:
    df["text"] += "<br>LLM Summary: " + df["enrichment_summary"]

map_fig = px.scatter_mapbox(df,
                      lon = df["lon"],
                      lat = df["lat"],
                      hover_name="name",
                      text = df['text'],
                      color = df['num_bikes_available'],
                      color_continuous_scale="Viridis",
                      mapbox_style="carto-positron",
                      zoom=11
                      )

st.plotly_chart(map_fig)

# Rolling Averages Bar Chart
st.subheader("Rolling Averages")
rolling1 = px.bar(df,
              x = "name",
              y = "rolling_avg_score",
              labels = {"name": "Station Name", "rolling_avg_score": "Rolling Average Score"}
              )
st.plotly_chart(rolling1,use_container_width=True)

## Get top and bottom Rolling averages
col1,col2 = st.columns(2)
sorted_df = df.sort_values(by=['station_id', 'collected_at']).drop_duplicates(subset="station_id", keep="last")
top_roll = sorted_df.nlargest(10,'rolling_avg_score')
bottom_roll = sorted_df[sorted_df['rolling_avg_score'] > 0].nsmallest(10, 'rolling_avg_score')

with col1:
        st.subheader('Top Rolling Averages')
        # KAN-29 BUG PATCH: Removed buggy hardcoded hex sequences to resolve
        # syntax compilation crashes. Plotly default rendering handles native keys seamlessly.

        top_fig = px.bar(
            top_roll,
            x="name",
            y="rolling_avg_score",
            labels={"name": "Station Name", "rolling_avg_score": "Rolling Average Score"}
        )
        st.plotly_chart(top_fig, use_container_width=True)
        
with col2:
        st.subheader('Bottom Rolling Averages (Above 0)')
        bottom_fig = px.bar(
            bottom_roll,
            x="name",
            y="rolling_avg_score",
            labels={"name": "Station Name", "rolling_avg_score": "Rolling Average Score"}
        )
        st.plotly_chart(bottom_fig, use_container_width=True)


# --- Bike Health & Rental Rate Analysis Layout ---
col3, col4 = st.columns(2)

with col3:
    st.subheader("Health of Available Bikes")
    health_fig = px.histogram(
        df,
        x="availability_status",
        labels={"availability_status": "Availability Status"}
    )
    st.plotly_chart(health_fig, use_container_width=True)

with col4:
    st.subheader("Manual vs. EBike Rental Rate")
    # Aggregate trends safely
    bike_count = df.groupby('collected_at').agg({
        "num_ebikes_available": "sum", 
        "num_manual_bikes_available": "sum"
    }).reset_index()
    
    bike_fig = px.scatter(
        bike_count,
        x="collected_at",
        y=['num_ebikes_available', 'num_manual_bikes_available'],
        labels={"collected_at": "Collected At", "value": "Bikes Available", "variable": "Bike Type"}
    )
    st.plotly_chart(bike_fig, use_container_width=True)

# --- Raw Data Table View ---
st.subheader("Raw Data View")
st.dataframe(df, use_container_width=True)

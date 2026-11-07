import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
from supabase import create_client

# Fetch Data
load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
response = (supabase
            .schema("gold")
            .table("enriched_bks")
            .select("*")
            .execute())
df = pd.DataFrame(response.data)

# Create Header
st.title("Bay Area Bike Rental Data")
st.write("what our map is about")

# Availibility Map
st.subheader('Bike Map')
df["text"] = ("Bikes Availale:" + 
              df['num_bikes_available'].astype(str) + 
              "<br>Ebikes:" + df['num_ebikes_available'].astype(str) + 
              "<br>Manual Bikes:" + 
              df['num_manual_bikes_available'].astype(str))
map_fig = px.scatter_map(df,
                      lon = df["lon"],
                      lat = df["lat"],
                      hover_name="name",
                      text = df['text'],
                      color = df['num_bikes_available'],
                      color_continuous_scale="Viridis")
st.plotly_chart(map_fig)

# Rolling Averages Bar Chart
st.subheader("Rolling Averages")
rolling1 = px.bar(df,
              x = "name",
              y = "rolling_avg_score",
              labels = {"Station Name","Rolling Average Score"})
st.plotly_chart(rolling1)

## Get top and bottom Rolling averages
col1,col2 = st.columns(2)
sorted_df = df.sort_values(by=['station_id', 'collected_at']).drop_duplicates(subset="station_id", keep="last")
top_roll = sorted_df.nlargest(10,'rolling_avg_score')
bottom_roll = sorted_df[sorted_df['rolling_avg_score'] > 0].nsmallest(10, 'rolling_avg_score')

with col1:
    st.subheader('Top Rolling Averages')
    top_fig = px.bar(top_roll, 
                  x = "name",
                  y = "rolling_avg_score",
                  labels = {"name","rolling_avg_score"})
    st.plotly_chart(top_fig)
with col2:
    st.subheader('Bottom Rolling Averages')
    bottom_fig = px.bar(bottom_roll, 
                        x = "name",
                        y = "rolling_avg_score",
                        labels = {"name","rolling_avg_score"})
    st.plotly_chart(bottom_fig)


# Bike Health Status
health_fig = px.histogram(df,
                    x = "availability_status",
                    )
st.plotly_chart(health_fig)

#Data
st.dataframe(df)
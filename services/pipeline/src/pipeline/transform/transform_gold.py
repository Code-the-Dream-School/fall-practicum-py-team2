import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client

def transform_and_load_to_gold():
    # 1. Authenticates securely with live Supabase project.
    # 2. Pulls historical time-series snapshot rows from raw tables.
    # 3. Cleans entries, backfills inventory counts, and computes rolling averages.
    # 4. Handles full matrix safety filtering to prevent NaN/JSON compliance errors.
    # 5. Returns analytics DataFrame ready for Gold Layer metrics.
    
    # 1. Safely pull private connection keys from local hidden .env file
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(" Missing database connection credentials. Please check .env file.")
        
    # 2. Establish live authenticated connection client to the cloud database
    supabase = create_client(supabase_url, supabase_key)
    
    # 3. Download the raw tracking records Gaby is inserting
    print("Querying raw input logs straight from Supabase cloud database...")
    response = supabase.table("stations_raw").select("*").execute()
    df = pd.DataFrame(response.data)
    
    if df.empty:
        print("Warning: Target database raw input table is currently empty.")
        return df

    # 4. Handle Data Quality & Cleansing Rules (Drop missing tracking IDs or GPS coordinates)
    df = df.dropna(subset=['lat', 'lon', 'station_id'])
    
    # 5. Standardize Field Types & Fallback Map Counts safely from 'capacity' schema rows
    if 'num_bikes_available' not in df.columns and 'capacity' in df.columns:
        df['num_bikes_available'] = (df['capacity'] * 0.4).astype(int)
        df['num_docks_available'] = (df['capacity'] - df['num_bikes_available']).astype(int)
    else:
        df['num_bikes_available'] = pd.to_numeric(df.get('num_bikes_available', 0), errors='coerce').fillna(0).astype(int)
        df['num_docks_available'] = pd.to_numeric(df.get('num_docks_available', 0), errors='coerce').fillna(0).astype(int)

    if 'collected_at' in df.columns:
        df['collected_at'] = pd.to_datetime(df['collected_at'], errors='coerce')

    # 6. Derive Core Analytics Metric (The occupancy ratio score column)
    df['availability'] = np.where(df['capacity'] > 0, (df['num_bikes_available'] / df['capacity']) * 100, 0.0)
    df['availability'] = df['availability'].round(2)


    # 7. Process Dynamic Rolling Aggregate Window Trends (3-period group average trend)
    if 'collected_at' in df.columns:
        df = df.sort_values(by=['station_id', 'collected_at'])

    else:
        df = df.sort_values(by=['station_id'])
        
    df['rolling_avg_score'] = df.groupby('station_id')['availability'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean().round(2)
)

    # 8. Derive Product Category Label Bounds (Availability Status classifications)
    conditions = [
    (df['availability'] == 0.00),
    (df['availability'] > 0.00) & (df['availability'] <= 20.00),
    (df['availability'] > 20.00) & (df['availability'] < 90.00),
    (df['availability'] >= 90.00)
    ]
    categories = ['empty', 'low', 'healthy', 'full']
    df['availability_status'] = np.select(conditions, categories, default='healthy')

    # Convert last_reported timestamp rows to string formatting for clean JSON database storage serialization
    if 'collected_at' in df.columns:
        df['collected_at'] = df['collected_at'].astype(str)

    # 8.5 Derive Richer Gold Fields: Calculate manual bike counts and proportional preference rental rates
    # First, derive the number of manual bikes safely by subtracting ebikes from total available bikes
    df['num_ebikes_available'] = pd.to_numeric(df.get('num_ebikes_available', 0), errors='coerce').fillna(0).astype(int)
    df['num_manual_bikes_available'] = (df['num_bikes_available'] - df['num_ebikes_available']).clip(lower=0)

    # Now calculate the preference rental rates without any missing column keys
    df['bike_rent_rate'] = np.where(df['num_bikes_available'] > 0, (df['num_manual_bikes_available'] / df['num_bikes_available']) * 100, 0.0)
    df['ebike_rent_rate'] = np.where(df['num_bikes_available'] > 0, (df['num_ebikes_available'] / df['num_bikes_available']) * 100, 0.0)
    
    df['bike_rent_rate'] = df['bike_rent_rate'].round(2)
    df['ebike_rent_rate'] = df['ebike_rent_rate'].round(2)


    # 9. Clean up temporary operational utility columns before final processing
    if 'total_capacity' in df.columns:
        df = df.drop(columns=['total_capacity'])
        
    # Universal matrix filter: Replace any infinite or empty NaN values across columns with 0.0 or defaults
    df = df.replace([np.inf, -np.inf], np.nan)
    df['rolling_avg_score'] = df['rolling_avg_score'].fillna(0.0)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    text_cols = df.select_dtypes(exclude=[np.number]).columns

    df[numeric_cols] = df[numeric_cols].fillna(0.0)
    df[text_cols] = df[text_cols].fillna("")

    # 10. Temporarily return the dataframe locally until KAN-13 (Alevtina's schema cache) is deployed live
    print("Data transformation complete! Summary of Gold Layer analytics:")
    return df

if __name__ == "__main__":
    print("Initiating live KAN-15 database analytics pipeline runtime execution...")
    try:
        gold_layer_df = transform_and_load_to_gold()
        if gold_layer_df is not None and not gold_layer_df.empty:
            print("\n Success! Previewing clean Gold analytics data rows:")
            print(gold_layer_df[['station_id', 'name', 'availability', 'rolling_avg_score', 'availability_status', 'bike_rent_rate', 'ebike_rent_rate']].head(10))

    except Exception as e:
        print(f"\nPipeline execution failure details: {e}")

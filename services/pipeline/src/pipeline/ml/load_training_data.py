import os
from duckdb import df
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
import json
from pathlib import Path

# Downloading historical bike station records from Supabase
# Using pagination to retrieve all records for ML training

def load_raw_history():
    """
    Downloading historical bike station data from Supabase
    for preparing the KAN-28 machine learning training dataset.

    Returning the downloaded records as a pandas DataFrame.
    """

    # Loading database credentials securely from the local .env file
    load_dotenv()

    # Connecting to Supabase without changing any database records
    db = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    # Creating an empty list for storing downloaded records
    all_rows = []

    # Setting the page size to avoid Supabase's 1,000-row limit
    page_size = 1000
    start = 0

    # Downloading historical records in batches until reaching the last page
    while True:

        # Requesting one batch using a consistent sorting order
        response = (
            db.schema("raw")
            .table("stations_raw")
            .select("*")
            .order("station_id")
            .order("last_reported")
            .range(start, start + page_size - 1)
            .execute()
        )

        # Getting the records from the current batch
        rows = response.data

        # Adding the downloaded records to the complete list
        all_rows.extend(rows)

        # Stopping when reaching the final batch
        if len(rows) < page_size:
            break

        # Moving to the next batch
        start += page_size

    # Converting all downloaded records into a pandas DataFrame
    df = pd.DataFrame(all_rows)

    # Displaying the total number of downloaded records
    print(f"Total records downloaded: {len(df)}")

    # Returning the DataFrame for preparing ML training features
    return df


# Combining historical Supabase records with multiple local snapshots
# Standardizing timestamps and preparing one dataset for ML processing
def combine_history_and_snapshot(snapshot_paths):
    """
    Combining historical station records with local snapshots.
    Returning a DataFrame with standardized UTC timestamps.
    """

    # Loading historical station records from Supabase
    history = load_raw_history()

    # Converting historical reporting timestamps into UTC
    history["last_reported"] = pd.to_datetime(
        history["last_reported"],
        utc=True,
        errors="coerce",
        format="mixed"
    )

    # Creating a list for storing all datasets
    datasets = [history]

    # Reading each local snapshot
    for snapshot_path in snapshot_paths:

        # Opening the snapshot JSON file
        with open(snapshot_path, "r", encoding="utf-8") as file:
            snapshot = json.load(file)

        # Converting station records into a DataFrame
        new_data = pd.DataFrame(snapshot["stations"])

        # Adding the snapshot collection timestamp
        new_data["collected_at"] = snapshot["collected_at"]

        # Converting Unix reporting timestamps into UTC
        new_data["last_reported"] = pd.to_datetime(
            new_data["last_reported"],
            unit="s",
            utc=True,
            errors="coerce"
        )

        # Adding the snapshot to our datasets
        datasets.append(new_data)

    # Combining historical records and all snapshots
    combined = pd.concat(datasets, ignore_index=True)

    # Converting collection timestamps into UTC
    combined["collected_at"] = pd.to_datetime(
        combined["collected_at"],
        utc=True,
        errors="coerce",
        format="mixed"
    )

    # Sorting observations by station and reporting time
    combined = combined.sort_values(
        ["station_id", "last_reported", "collected_at"]
    )

    # Displaying the combined record count
    print(f"Combined records: {len(combined)}")

    # Returning the combined dataset
    return combined

# Removing repeated station reports from the combined training dataset
# Keeping the latest collected record for each station and reporting time
def remove_duplicate_reports(df):
    """
    Removing repeated station reports based on station ID
    and reporting timestamp.
    """

    # Counting records before removing duplicates
    original_count = len(df)

    # Sorting records by collection time
    df = df.sort_values("collected_at")

    # Keeping the latest record for each station and reporting timestamp
    df = df.drop_duplicates(
        subset=["station_id", "last_reported"],
        keep="last"
    )

    # Sorting cleaned records by station and reporting time
    df = df.sort_values(
        ["station_id", "last_reported"]
    ).reset_index(drop=True)

    # Displaying the number of removed duplicates
    print(f"Duplicate reports removed: {original_count - len(df)}")
    print(f"Remaining unique reports: {len(df)}")

    # Returning the cleaned dataset
    return df

# Preparing short-term bike availability examples for ML training
# Creating prediction labels from future station observations
def prepare_training_data(df):
    """
    Preparing labeled station observations for predicting
    whether available bikes will increase, decrease, or remain unchanged.
    """

    # Sorting observations by station and reporting time
    df = df.sort_values(
        ["station_id", "last_reported"]
    ).copy()

    # Finding the next bike count for each station
    df["next_bikes"] = (
        df.groupby("station_id")["num_bikes_available"].shift(-1)
    )

    # Finding the next reporting time for each station
    df["next_report"] = (
        df.groupby("station_id")["last_reported"].shift(-1)
    )

    # Calculating minutes between consecutive reports
    df["gap_minutes"] = (
        (df["next_report"] - df["last_reported"])
        .dt.total_seconds() / 60
    )

    # Keeping observation pairs within 10 minutes
    df = df[
        df["gap_minutes"].between(0, 10, inclusive="right")
    ].copy()

    # Calculating changes in available bike counts
    df["bike_change"] = (
        df["next_bikes"] - df["num_bikes_available"]
    )

    # Creating the three prediction labels
    df["target"] = "Unchanged"
    df.loc[df["bike_change"] > 0, "target"] = "Increase"
    df.loc[df["bike_change"] < 0, "target"] = "Decrease"

    # Displaying the number of prepared examples
    print(f"Training examples prepared: {len(df)}")

    # Returning the labeled dataset
    return df

# Preparing current station information as ML input features
# Extracting time features without using future observations
def prepare_ml_features(df):
    """
    Preparing numerical features for predicting
    the next change in bike availability.
    """

    # Creating a copy to preserve the original dataset
    df = df.copy()

    # Extracting the reporting hour in UTC
    df["hour"] = df["last_reported"].dt.hour

    # Extracting the reporting day of the week
    df["day_of_week"] = df["last_reported"].dt.dayofweek

    
    
    # Selecting current station information and historical trend features
    # Excluding future observations to prevent data leakage
    feature_columns = [
    "num_bikes_available",
    "capacity",
    "num_docks_available",
    "num_ebikes_available",
    "lat",
    "lon",
    "hour",
    "day_of_week",
    "previous_bike_change",
    "has_recent_history"
    ]

    # Creating the model input dataset
    X = df[feature_columns].copy()

    # Selecting the prediction labels
    #y = df["target"].copy()
    # Selecting labels when available for model training
    # Allowing new station observations without known labels
    y = df["target"].copy() if "target" in df.columns else None

    # Displaying the number of features
    print(f"ML features selected: {len(feature_columns)}")
    print(f"Training examples: {len(X)}")

    # Returning model inputs and prediction labels
    return X, y

# Splitting ML examples into training and testing datasets
# Using different reporting dates to reduce data leakage
def split_training_testing(df):
    
    """
    Splitting station observations by reporting date.
    Training on November 10 and 11.
    Testing on November 12.

    """

    # Selecting November 10 and 11 observations for training
    train_df = df[
    df["last_reported"].dt.date.astype(str).isin(
        ["2026-11-10", "2026-11-11"]
    )
    ].copy()

    # Selecting November 12 observations for testing
    test_df = df[
    df["last_reported"].dt.date.astype(str) == "2026-11-12"
    ].copy()

    # Preparing training features and labels
    X_train, y_train = prepare_ml_features(train_df)

    # Preparing testing features and labels
    X_test, y_test = prepare_ml_features(test_df)

    # Displaying dataset sizes
    print(f"Training examples: {len(X_train)}")
    print(f"Testing examples: {len(X_test)}")

    # Returning training and testing datasets
    return X_train, X_test, y_train, y_test

# Creating historical bike availability features
# Using previous station observations without looking into the future
def add_historical_features(df):
    """
    Creating features from previous station reports
    for improving short-term bike availability predictions.
    """

    # Sorting observations by station and reporting time
    df = df.sort_values(
        ["station_id", "last_reported"]
    ).copy()

    # Finding the previous bike count for each station
    previous_bikes = (
        df.groupby("station_id")["num_bikes_available"].shift(1)
    )

    # Finding the previous reporting timestamp
    previous_time = (
        df.groupby("station_id")["last_reported"].shift(1)
    )

    # Calculating minutes since the previous report
    previous_gap = (
        (df["last_reported"] - previous_time)
        .dt.total_seconds() / 60
    )

    # Checking whether the previous report is within 10 minutes
    recent_history = previous_gap.between(
        0, 10, inclusive="right"
    )

    # Creating an indicator for recent history
    df["has_recent_history"] = recent_history.astype(int)

    # Calculating the previous bike availability change
    df["previous_bike_change"] = (
        df["num_bikes_available"] - previous_bikes
    ).where(recent_history, 0)

    # Returning the dataset with historical features
    return df
from pathlib import Path
import pandas as pd
from pipeline.ml.load_training_data import load_raw_history
from pipeline.transform.transform_gold import transform_and_load_to_gold
from pipeline.ml.load_training_data import (
    add_historical_features,
    prepare_ml_features,
)
from pipeline.ml.train_model import load_model, predict_availability

# Transforming prepared station observations into ML predictions
def transform_ml(df, model_path, require_fresh=True):
    """
    Predicting the next change in bike availability
    using a previously trained classifier.
    """

    # Creating a copy to preserve the original station data
    result = df.copy()

    # Converting station reporting timestamps to UTC datetime
    result["last_reported"] = pd.to_datetime(
        result["last_reported"],
        utc=True,
        errors="coerce"
    )

    # Removing observations with missing reporting timestamps
    result = result.dropna(subset=["last_reported"]).copy()

    # Checking whether any valid station observations remain
    if result.empty:
        raise ValueError(
            "No station observations with valid timestamps available."
        )

    # Finding the newest station report
    reference_time = result["last_reported"].max()

    # Getting the current UTC time
    current_time = pd.Timestamp.now(tz="UTC")

    # Calculating the age of the newest report in minutes
    newest_report_age = (
        current_time - reference_time
    ).total_seconds() / 60

    # Rejecting outdated or future-dated station reports
    if require_fresh and not (0 <= newest_report_age <= 10):
        raise ValueError(
            "Station data must be between 0 and 10 minutes old "
            "for live predictions."
        )

    # Preparing historical bike changes from previous station reports
    result = add_historical_features(result)

    # Preparing the ten model input features
    X, _ = prepare_ml_features(result)

    # Loading the previously trained Random Forest classifier
    model = load_model(Path(model_path))

    # Predicting the next bike availability change
    result["predicted_change"] = predict_availability(model, X)

    # Selecting the latest observation for each station
    result = (
    result.sort_values("last_reported")
    .drop_duplicates("station_id", keep="last")
    .copy()
    )

    # Calculating how old each station report is
    report_age = (
    reference_time - result["last_reported"]
    ).dt.total_seconds() / 60

    # Keeping stations reported within the last 10 dataset minutes
    result = result[report_age <= 10].copy()

    # Returning the latest station predictions
    return result

# Connecting the Gold transformation to the ML classifier
def run_gold_to_ml(model_path, require_fresh=True):
    """
    Running the Gold transformation first,
    then generating ML predictions.
    """

    # Loading transformed station data from the Gold layer
    gold_df = transform_and_load_to_gold()

    # Checking whether Gold returned any station records
    if gold_df.empty:
        print("No Gold data available for ML predictions.")
        return gold_df

    # Converting reporting timestamps to UTC datetime
    gold_df["last_reported"] = pd.to_datetime(
        gold_df["last_reported"],
        utc=True,
        errors="coerce"
    )

    # Removing records without valid reporting timestamps
    gold_df = gold_df.dropna(subset=["last_reported"])

    # Attempting to generate ML predictions after Gold processing
    try:
        predictions_df = transform_ml(
            gold_df,
            model_path,
            require_fresh=require_fresh
        )

    # Handling unavailable ML predictions without losing Gold data
    except ValueError as error:
        print(f"ML predictions skipped: {error}")
        return gold_df
    # Returning Gold analytics with ML predictions
    return predictions_df

# Loading complete station history for ML processing
def load_complete_station_history():
    """
    Loading all available Raw station observations
    instead of the first 1,000 records.
    """

    # Downloading historical station observations
    df = load_raw_history()

    # Converting report timestamps to UTC
    df["last_reported"] = pd.to_datetime(
        df["last_reported"],
        utc=True,
        errors="coerce"
    )

    # Removing records with invalid timestamps
    df = df.dropna(subset=["last_reported"])

    # Reporting the number of available observations
    print("Complete station history:", len(df))
    print("Unique stations:", df["station_id"].nunique())

    # Returning the historical station observations
    return df

# Calculating Gold availability for complete station history
def add_gold_availability(df):
    """
    Calculating the percentage of available bikes
    using the same formula as the Gold transformation.
    """

    # Creating a copy to preserve the original data
    result = df.copy()

    # Converting bike counts and capacity to numeric values
    bikes = pd.to_numeric(
        result["num_bikes_available"], errors="coerce"
    ).fillna(0)

    capacity = pd.to_numeric(
        result["capacity"], errors="coerce"
    ).fillna(0)

    # Calculating the availability percentage
    result["availability"] = (
        bikes.div(capacity.where(capacity > 0))
        .mul(100)
        .fillna(0)
        .round(2)
    )

    # Returning station history with Gold availability
        # Assigning Gold availability categories
    result["availability_status"] = pd.cut(
        result["availability"],
        bins=[-float("inf"), 0, 20, 90, float("inf")],
        labels=["empty", "low", "healthy", "full"],
        right=True
    ).astype(str)

    # Correcting the boundary at 90 percent
    result.loc[
        result["availability"] >= 90,
        "availability_status"
    ] = "full"
        # Sorting station observations by collection time
    result["collected_at"] = pd.to_datetime(
        result["collected_at"],
        utc=True,
        errors="coerce"
    )

    result = result.sort_values(
        ["station_id", "collected_at"]
    )

    # Calculating the rolling average of the last three observations
    result["rolling_avg_score"] = (
        result.groupby("station_id")["availability"]
        .transform(
            lambda values: values.rolling(
                window=3,
                min_periods=1
            ).mean().round(2)
        )
    )
        # Calculating bike availability changes between observations
    result["bike_availability_change"] = (
        result.groupby("station_id")["num_bikes_available"]
        .diff()
        .fillna(0)
        .astype(int)
    )
    return result

# Combining complete Gold analytics with ML predictions
def run_complete_gold_to_ml(model_path, require_fresh=True):
    """
    Generating Gold analytics and ML predictions
    from the complete station history.
    """

    # Loading all available historical station observations
    raw_df = load_complete_station_history()

    # Checking whether any station records were downloaded
    if raw_df.empty:
        print("No station data available.")
        return raw_df

    # Calculating Gold analytics for the complete history
    gold_df = add_gold_availability(raw_df)

    # Attempting to generate ML predictions after Gold processing
    try:
        predictions_df = transform_ml(
            gold_df,
            model_path,
            require_fresh=require_fresh
        )

    # Handling unavailable ML predictions without losing Gold data
    except ValueError as error:
        print(f"ML predictions skipped: {error}")
        return gold_df

    # Reporting the number of station predictions
    print("Gold-to-ML predictions:", len(predictions_df))

    # Returning Gold analytics with ML predictions
    return predictions_df
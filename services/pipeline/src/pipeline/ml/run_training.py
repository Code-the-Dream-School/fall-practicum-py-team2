from pathlib import Path

from pipeline.ml.load_training_data import (
    combine_history_and_snapshot,
    remove_duplicate_reports,
    add_historical_features,
    prepare_training_data,
    split_training_testing,
)

from pipeline.ml.train_model import (
    train_model,
    evaluate_model,
    save_model,
)

# Running the complete ML training workflow
def run_training():
    """
    Loading historical station data,
    preparing it for model training,
    and evaluating the classifier.
    """

   
    # Finding locally collected station snapshots
    snapshot_paths = sorted(
        str(path)
        for path in Path("data/kan28_snapshots").glob("stations_*.json")
    )

    # Reporting the number of snapshot files
    print("Snapshot files found:", len(snapshot_paths))

    # Combining Supabase history with local snapshots
    combined_df = combine_history_and_snapshot(snapshot_paths)

    # Reporting the combined record count
    print("Combined training records:", len(combined_df))

        # Removing duplicate station observations
    clean_df = remove_duplicate_reports(combined_df)

    # Reporting the number of unique observations
    print("Unique training records:", len(clean_df))
        # Calculating historical features before creating prediction labels
    featured_df = add_historical_features(clean_df)

    # Reporting the number of records with historical features
    print("Records with historical features:", len(featured_df))
        # Creating training labels from the next station observation
    labeled_df = prepare_training_data(featured_df)

    # Reporting the number of labeled training examples
    print("Labeled training examples:", len(labeled_df))

    # Displaying the distribution of prediction labels
    print("Label distribution:")
    print(labeled_df["target"].value_counts())

        # Splitting historical observations into training and testing sets
    X_train, X_test, y_train, y_test = split_training_testing(
        labeled_df
    )

    # Reporting the number of training and testing examples
    print("Training examples:", len(X_train))
    print("Testing examples:", len(X_test))

        # Training the Random Forest classifier
    model = train_model(X_train, y_train)

    # Reporting successful model training
    print("Random Forest training completed.")

    # Evaluating the classifier using testing data and training labels
    evaluate_model(model, X_test, y_test, y_train)
    # Reporting successful model evaluation
    print("Model evaluation completed.")

    
    # Setting the output path for the trained ML classifier
    model_path = Path(
        "services/pipeline/models/bike_availability_model.joblib"
    )

    # Creating the models directory if it does not exist
    model_path.parent.mkdir(parents=True, exist_ok=True)

    # Saving the trained Random Forest classifier
    save_model(model, model_path)

    # Reporting the saved model location
    print("Training workflow completed.")
    print("Model saved to:", model_path)

# Starting the ML training workflow when running this file directly
if __name__ == "__main__":
    run_training()
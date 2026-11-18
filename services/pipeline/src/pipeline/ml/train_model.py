from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
import joblib


# Training a Random Forest classifier to predict bike availability changes
# Learning patterns from current station information
def train_model(X_train, y_train):
    """
    Training a Random Forest classifier using
    historical station observations.
    """


    # Creating a Random Forest classifier with balanced class weights
    model = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42
    )

    # Training the classifier using historical examples
    model.fit(X_train, y_train)

    # Displaying a confirmation after training
    print("Random Forest model trained successfully!")

    # Returning the trained classifier
    return model

# Evaluating classifier predictions against actual bike availability changes
# Comparing model performance with a simple majority-class baseline
def evaluate_model(model, X_test, y_test, y_train):
    """
    Evaluating Random Forest performance using
    accuracy, macro-F1, and a baseline comparison.
    """

    # Predicting bike availability changes for testing examples
    predictions = model.predict(X_test)

    # Calculating model accuracy
    accuracy = accuracy_score(y_test, predictions)

    # Calculating macro-F1 across all three categories
    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    # Finding the most common prediction category in training data
    majority_class = y_train.value_counts().idxmax()

    # Creating baseline predictions using the majority training class
    baseline_predictions = [majority_class] * len(y_test)

    # Displaying the majority class used by the baseline
    print("Baseline majority class:", majority_class)

    # Calculating baseline accuracy
    baseline_accuracy = accuracy_score(
        y_test,
        baseline_predictions
    )

    # Calculating baseline macro-F1
    baseline_f1 = f1_score(
        y_test,
        baseline_predictions,
        average="macro",
        zero_division=0
    )

    # Displaying model performance
    print(f"Model accuracy: {accuracy:.3f}")
    print(f"Model macro-F1: {macro_f1:.3f}")

    # Displaying baseline performance
    print(f"Baseline accuracy: {baseline_accuracy:.3f}")
    print(f"Baseline macro-F1: {baseline_f1:.3f}")

    # Displaying performance for each prediction category
    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        zero_division=0
    ))

# Saving the trained classifier to a local file
# Allowing future predictions without retraining the model
def save_model(model, file_path):
    """
    Saving a trained Random Forest model
    for future predictions.
    """

    # Saving the trained model using joblib
    joblib.dump(model, file_path)

    # Displaying a confirmation after saving
    print(f"Model saved successfully: {file_path}")

# Loading a previously trained classifier from a local file
# Allowing predictions without repeating the training process
def load_model(file_path):
    """
    Loading a saved Random Forest classifier
    for future bike availability predictions.
    """

    # Loading the saved classifier using joblib
    model = joblib.load(file_path)

    # Displaying a confirmation after loading
    print(f"Model loaded successfully: {file_path}")

    # Returning the loaded classifier
    return model

# Predicting future bike availability changes using a trained model
def predict_availability(model, X):
    """
    Predicting whether available bikes will
    Increase, Decrease, or remain Unchanged.
    """

    # Generating predictions using the trained classifier
    predictions = model.predict(X)

    # Returning the predicted categories
    return predictions
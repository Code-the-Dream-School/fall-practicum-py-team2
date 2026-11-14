# KAN-28 — Bike Availability ML Classifier

## Project Overview

For this task, I built a machine learning model to predict changes in bike availability at each station.

The model predicts what will happen at the next station update, within 10 minutes:

- **Increase:** More bikes are available.
- **Decrease:** Fewer bikes are available.
- **Unchanged:** The number of bikes stays the same.

I used Python, pandas, and a Random Forest classifier from scikit-learn.

## How It Works

I used historical bike station data from Supabase and some snapshots I collected.

The model uses 10 features, including:

- Available bikes, electric bikes, docks, and station capacity
- Station location (latitude and longitude)
- Hour and day of the week
- Previous bike changes and recent station history

I used future bike counts only to create the correct answers for training, not as model inputs. This helps prevent data leakage.

## Training and Results

After cleaning the data and removing duplicates, I had **6,279 unique records** and **2,921 training and testing examples**.

I split the data by date:

- **Training:** November 10–11, 2026 (1,544 examples)
- **Testing:** November 12, 2026 (1,377 examples)

Here are my results:

| Metric | My Model | Baseline |
|---|---:|---:|
| Accuracy | 52.7% | 49.7% |
| Macro-F1 | 43.2% | 22.1% |

The baseline always predicts "Unchanged."

My model performed better than the baseline, especially on macro-F1. However, it still had difficulty predicting when bikes would increase or decrease.

## How to Run

**1. Install the required packages:**

```bash
pip install -r requirements.txt
```

**2. Add your Supabase credentials to `.env`:**

- `SUPABASE_URL`
- `SUPABASE_KEY`

**3. Run the training script from the project root:**

```bash
PYTHONPATH=services/pipeline/src python -m pipeline.ml.run_training
```

The trained model is saved to:

`services/pipeline/models/bike_availability_model.joblib`

The training script uses local snapshots from `data/kan28_snapshots/`. These files are not included in Git, so the same data is needed to reproduce my exact results. Running training again will overwrite the saved model.

## ML Predictions

I created two functions:

- `run_gold_to_ml()` — Uses the team's existing Gold transformation.
- `run_complete_gold_to_ml()` — Loads more historical records and calculates some Gold-style fields before making predictions.

For live predictions, the newest station report must be no more than 10 minutes old.

If the data is outdated, the ML wrappers can skip predictions and return the Gold data instead.

The ML code is separate from the main ETL workflow for now. Predictions are not saved to Supabase.

## Limitations and Next Steps

The model was trained using only a few days of data, so its predictions are not reliable enough for production yet.

In the future, I would like to:

- Collect more historical data.
- Improve predictions for Increase and Decrease.
- Add weather and holiday information.
- Test other machine learning models.
- Connect the ML classifier to the team's main pipeline.

## Conclusion

For KAN-28, I built and tested a Random Forest classifier using real bike station data.

The model performed better than a simple baseline, and I learned how to prepare time-based data, avoid data leakage, evaluate a classifier, and connect machine learning with an existing data pipeline.
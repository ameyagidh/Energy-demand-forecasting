"""
Forecasts Spain's hourly electricity load and honestly benchmarks the
result against two real baselines already present in the data:

1. Naive persistence  - "load will be what it was 24h ago"
2. The grid operator's own day-ahead forecast (`total load forecast` column,
   Spain's real transmission-system-operator forecast, not something we made up)

A time-ordered (never shuffled) 80/20 split - the last 20% of the timeline
is held out, since shuffling hourly data would leak future information into
training via adjacent lag features.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from features import FEATURE_COLS, TARGET_COL, build_features, load_frame

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "energy_spain_hourly.csv")
MODEL_DIR = os.path.join(BASE, "model")
os.makedirs(MODEL_DIR, exist_ok=True)


def mape(y_true, y_pred):
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def score(y_true, y_pred):
    return {
        "mae": round(float(np.mean(np.abs(y_true - y_pred))), 2),
        "rmse": round(float(np.sqrt(np.mean((y_true - y_pred) ** 2))), 2),
        "mape_pct": round(mape(y_true, y_pred), 3),
    }


def main():
    df = load_frame(DATA)
    df = build_features(df)
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL, "total load forecast"]).reset_index(drop=True)

    split_idx = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

    X_train, y_train = train_df[FEATURE_COLS], train_df[TARGET_COL]
    X_test, y_test = test_df[FEATURE_COLS], test_df[TARGET_COL]

    model = GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.9, random_state=42
    )
    model.fit(X_train, y_train)
    gbr_preds = model.predict(X_test)

    naive_preds = test_df["load_lag_24h"].values
    operator_preds = test_df["total load forecast"].values

    results = {
        "gradient_boosting": score(y_test.values, gbr_preds),
        "naive_persistence_24h": score(y_test.values, naive_preds),
        "grid_operator_forecast": score(y_test.values, operator_preds),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "test_period": {
            "start": str(test_df["time"].iloc[0]),
            "end": str(test_df["time"].iloc[-1]),
        },
    }

    print(json.dumps(results, indent=2))

    joblib.dump({"model": model, "features": FEATURE_COLS}, os.path.join(MODEL_DIR, "load_forecast_model.joblib"))
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2)

    # Save a sample of test predictions for the dashboard's actual-vs-predicted chart.
    sample = test_df[["time", TARGET_COL, "total load forecast"]].copy()
    sample["gbr_prediction"] = gbr_preds
    sample.to_csv(os.path.join(MODEL_DIR, "test_predictions.csv"), index=False)

    print("\nSaved model/load_forecast_model.joblib, metrics.json, test_predictions.csv")


if __name__ == "__main__":
    main()

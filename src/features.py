"""Feature engineering for the Spain hourly electricity load forecast."""
import pandas as pd

LAGS = [24, 48, 168]  # 1 day, 2 days, 1 week (hours)
ROLLING_WINDOWS = [24, 168]

FEATURE_COLS = (
    ["hour", "dayofweek", "month", "is_weekend"]
    + [f"load_lag_{h}h" for h in LAGS]
    + [f"load_rollmean_{h}h" for h in ROLLING_WINDOWS]
)
TARGET_COL = "total load actual"


def load_frame(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    df[TARGET_COL] = df[TARGET_COL].interpolate(limit_direction="both")
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["time"].dt.hour
    df["dayofweek"] = df["time"].dt.dayofweek
    df["month"] = df["time"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    for h in LAGS:
        df[f"load_lag_{h}h"] = df[TARGET_COL].shift(h)
    for w in ROLLING_WINDOWS:
        df[f"load_rollmean_{w}h"] = df[TARGET_COL].shift(1).rolling(w).mean()

    return df

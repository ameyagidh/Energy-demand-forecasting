"""Generates the dashboard's static charts from real predictions."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "model")
CHARTS = os.path.join(BASE, "static", "charts")
os.makedirs(CHARTS, exist_ok=True)

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#151922", "figure.facecolor": "#0b0d12",
                                     "axes.edgecolor": "#232936", "grid.color": "#232936",
                                     "text.color": "#f3f4f6", "axes.labelcolor": "#f3f4f6",
                                     "xtick.color": "#9ca3af", "ytick.color": "#9ca3af"})


def main():
    df = pd.read_csv(os.path.join(MODEL_DIR, "test_predictions.csv"))
    df["time"] = pd.to_datetime(df["time"], utc=True)

    # One representative week for readability.
    week = df[(df["time"] >= "2018-11-05") & (df["time"] < "2018-11-12")]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(week["time"], week["total load actual"], label="Actual load", color="#f3f4f6", linewidth=1.8)
    ax.plot(week["time"], week["gbr_prediction"], label="Our model (GBR)", color="#8b5cf6", linewidth=1.4)
    ax.plot(week["time"], week["total load forecast"], label="Grid operator forecast", color="#10b981",
            linewidth=1.2, linestyle="--")
    ax.set_title("One week: actual vs. our model vs. Spain's grid operator forecast")
    ax.set_ylabel("Load (MW)")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "forecast_week.png"), dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    df["error_gbr"] = df["total load actual"] - df["gbr_prediction"]
    df["error_operator"] = df["total load actual"] - df["total load forecast"]
    sns.histplot(df["error_gbr"], bins=50, color="#8b5cf6", label="Our model error", alpha=0.6, ax=ax)
    sns.histplot(df["error_operator"], bins=50, color="#10b981", label="Grid operator error", alpha=0.6, ax=ax)
    ax.set_title("Forecast error distribution (test set)")
    ax.set_xlabel("Actual - Predicted (MW)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "error_distribution.png"), dpi=130)
    plt.close(fig)

    print("Saved forecast_week.png and error_distribution.png")


if __name__ == "__main__":
    main()

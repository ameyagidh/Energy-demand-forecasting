"""
Regenerates data/energy_spain_hourly.csv from the original Hugging Face
dataset. Not required to run the app - the CSV is already committed - but
kept for reproducibility. Requires requirements-datasets.txt.
"""
import os

import pandas as pd
from datasets import load_dataset

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

COLS = ["time", "total load actual", "total load forecast", "price actual", "price day ahead"]


def main():
    d = load_dataset("vitaliy-sharandin/energy-consumption-hourly-spain", split="train")
    pd.DataFrame(d)[COLS].to_csv(os.path.join(DATA, "energy_spain_hourly.csv"), index=False)
    print("Refreshed data/energy_spain_hourly.csv")


if __name__ == "__main__":
    main()

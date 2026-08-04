import json
import os

import pandas as pd
from flask import Flask, jsonify, render_template

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE, "model")

app = Flask(__name__)

with open(os.path.join(MODEL_DIR, "metrics.json")) as f:
    _metrics = json.load(f)

_predictions = pd.read_csv(os.path.join(MODEL_DIR, "test_predictions.csv"))
_predictions["time"] = pd.to_datetime(_predictions["time"], utc=True)


@app.route("/")
def index():
    return render_template("index.html", m=_metrics)


@app.route("/api/sample-day")
def sample_day():
    """Returns one real day of actual/predicted/operator-forecast values for the demo chart."""
    day = _predictions[_predictions["time"].dt.date.astype(str) == "2018-11-07"]
    return jsonify(
        {
            "labels": day["time"].dt.strftime("%H:%M").tolist(),
            "actual": day["total load actual"].round(0).tolist(),
            "our_model": day["gbr_prediction"].round(0).tolist(),
            "operator": day["total load forecast"].round(0).tolist(),
        }
    )


if __name__ == "__main__":
    app.run(port=5300, debug=True)

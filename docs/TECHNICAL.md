# Technical documentation

## Dataset

[Spain hourly energy generation/load/price, 2015–2018](https://huggingface.co/datasets/vitaliy-sharandin/energy-consumption-hourly-spain)
via ENTSO-E, downloaded once via Hugging Face and committed as a CSV under
`data/`. Only the columns needed for this project are kept:

| Column | Meaning |
|---|---|
| `time` | hourly timestamp (UTC-offset aware) |
| `total load actual` | real measured grid load (target) |
| `total load forecast` | Spain's actual REE day-ahead forecast for that hour |
| `price actual` / `price day ahead` | kept for reference, not used in this model |

35,064 hourly rows (2015-01-01 to 2018-12-31), with 36 missing values in
`total load actual` — filled via linear interpolation (`.interpolate()`),
since a gap of a few missing hours in a smooth load signal is safely
approximated by its neighbors.

## Why the operator-forecast benchmark matters

`total load forecast` is not a column this project invented — it's REE's
(Spain's transmission system operator) own real day-ahead forecast, bundled
in the original dataset as a point of comparison. Benchmarking against it
is the difference between "here's an accuracy number" and "here's how that
number compares to what a professional grid operator actually achieves with
far more input data (weather, generation schedules, historical patterns
across the whole peninsula)." Reporting only the naive-baseline comparison
would have made the model look better than it really is.

## Feature engineering (`src/features.py`)

- **Calendar features:** hour, day-of-week, month, is-weekend — captures
  daily and weekly demand cycles (people use less power at 3am, more on
  weekday evenings).
- **Lag features:** load 24h, 48h, and 168h (1 week) ago — the model's main
  signal, since electricity demand is highly autocorrelated at daily/weekly
  periods.
- **Rolling means:** 24h and 168h trailing average load — smooths out
  single-hour noise in the lag features.

No weather data, no holiday calendar, no generation-mix features — this is
a deliberately lean feature set, and the gap to the grid operator's
forecast (which surely uses richer inputs) is the direct, honest cost of
that choice.

## Train/test split

**Time-ordered, never shuffled**: the first 80% of the timeline is train,
the last 20% (6,980 hours, 2018-03-16 to 2018-12-31) is test. This matters
specifically because of the lag/rolling features — a random shuffle would
put, e.g., hour *t* in training and hour *t-24* (which directly informs its
prediction) in test, leaking future information backward. A forecasting
model must be validated the way it will actually be used: predicting
forward in time from only past data.

## Model (`src/train.py`)

`GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.9)`
on the 10 engineered features above (no scaling needed — tree-based model).

### Results (held-out test set)

| Forecast source | MAE (MW) | RMSE (MW) | MAPE |
|---|---|---|---|
| Naive persistence (load 24h ago) | 2,464.62 | 3,508.52 | 8.573% |
| Gradient Boosting (this project) | 1,126.45 | 1,585.34 | 3.969% |
| REE grid operator day-ahead forecast | 259.62 | 378.30 | 0.898% |

The naive-persistence baseline is itself a legitimate, commonly-used
forecasting baseline (not a strawman) — beating it by more than 2x on MAPE
means the model has learned real structure beyond "tomorrow looks like
yesterday." Losing to REE's forecast by ~4x is expected and explained by
the missing weather/generation inputs, not treated as a mystery.

## Charts (`src/charts.py`)

- **`forecast_week.png`** — one representative week (Nov 5–12, 2018) of
  actual vs. predicted vs. operator-forecast, chosen because it includes
  both a sharp demand spike (Nov 7) and calmer days, giving a visually
  honest sense of where the model does and doesn't track well.
- **`error_distribution.png`** — overlaid histograms of `actual - predicted`
  for both this model and the operator forecast, over the full test set (not
  just the one displayed week) — shows the operator's error is both smaller
  and more tightly centered around zero.

## Serving (`app.py`)

Two routes: the main dashboard (all charts/tables precomputed, served as
static content) and `GET /api/sample-day`, which returns real saved
predictions for November 7, 2018 (from `model/test_predictions.csv`, itself
written during `train.py`) rendered client-side with a small vanilla-Canvas
line chart — no charting library dependency, and no data invented for the
demo.

## What was deliberately not built

- **No weather features.** This is the single biggest lever for closing the
  gap to the operator forecast, and adding a weather API integration was
  considered and deferred — noted here as the clear next step rather than
  silently working around it.
- **No hyperparameter search (grid/random search, Optuna).** The current
  parameters were chosen from reasonable defaults and one round of manual
  tuning; a proper search would likely improve the Gradient Boosting number
  somewhat, but wouldn't change the core honest finding (still well short
  of the operator's weather-informed forecast).
- **No multi-step-ahead forecasting.** This project predicts one hour at a
  time using lag features; a true day-ahead system (matching what REE
  actually produces) would need to forecast the full next 24 hours without
  access to intervening actuals — a materially harder problem, and worth
  stating plainly rather than implying this project solves the same task
  REE does.

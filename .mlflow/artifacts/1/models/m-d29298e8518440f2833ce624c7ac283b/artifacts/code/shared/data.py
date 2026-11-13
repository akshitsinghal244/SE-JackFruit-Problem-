"""Offline data pipeline: CSV -> labelled training samples.

Expected CSV schema (Kaggle "Store Item Demand Forecasting Challenge", train.csv):
    date,store,item,sales
    2013-01-01,1,1,13

Pipeline
--------
1. load_sales        read + sort + sanity-check that every store-item has one row per day
2. split_dates       decide train / validation / test cut-off dates (by time, never shuffled)
3. fit_thresholds    per store-item tertiles, computed on TRAINING rows only
4. build_samples     for every (store, item, target day): 7 lags, calendar parts, label
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import HOLDOUT_MONTHS, LAG_NAMES, VALIDATION_MONTHS, WINDOW


# --------------------------------------------------------------------------- 1
def load_sales(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, usecols=["date", "store", "item", "sales"])
    df["date"] = pd.to_datetime(df["date"])
    df["store"] = df["store"].astype(int)
    df["item"] = df["item"].astype(int)
    df["sales"] = df["sales"].astype(float)
    if df["sales"].lt(0).any():
        raise ValueError("Negative sales values found in the CSV.")
    df = df.sort_values(["store", "item", "date"]).reset_index(drop=True)
    if df.duplicated(["store", "item", "date"]).any():
        raise ValueError("Duplicate (store, item, date) rows found in the CSV.")
    return df


# --------------------------------------------------------------------------- 2
@dataclass(frozen=True)
class Split:
    val_start: pd.Timestamp   # first day of validation period
    test_start: pd.Timestamp  # first day of held-out test period (last 3 months)
    end: pd.Timestamp         # last day in data

    def as_dict(self) -> dict:
        return {k: str(v.date()) for k, v in self.__dict__.items()}


def split_dates(df: pd.DataFrame) -> Split:
    end = df["date"].max()
    test_start = (end - pd.DateOffset(months=HOLDOUT_MONTHS)) + pd.Timedelta(days=1)
    val_start = test_start - pd.DateOffset(months=VALIDATION_MONTHS)
    return Split(val_start=val_start, test_start=test_start, end=end)


# --------------------------------------------------------------------------- 3
def fit_thresholds(df: pd.DataFrame, before: pd.Timestamp) -> pd.DataFrame:
    """Tertile cut points per store-item, using only rows strictly before `before`.

    Returns a frame indexed by (store, item) with columns q1, q2:
        sales <= q1        -> Low
        q1 < sales <= q2   -> Medium
        sales > q2         -> High
    Using only past rows prevents the test period from leaking into the labels.
    """
    past = df[df["date"] < before]
    q = past.groupby(["store", "item"])["sales"].quantile([1 / 3, 2 / 3]).unstack()
    q.columns = ["q1", "q2"]
    return q


def label_from_thresholds(sales: np.ndarray, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    return np.where(sales <= q1, 0, np.where(sales <= q2, 1, 2)).astype(np.int64)


# --------------------------------------------------------------------------- 4
def build_samples(df: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    """One row per (store, item, target day) that has 7 full days of history.

    Columns: store, item, date, dow, month, lag_1..lag_7, roll_mean, sales, label
    lag_k = sales k days BEFORE the target day.
    """
    out = df.copy()
    g = out.groupby(["store", "item"], sort=False)
    for k in range(1, WINDOW + 1):
        out[f"lag_{k}"] = g["sales"].shift(k)
        # A shift of k rows must equal exactly k calendar days, otherwise there is a gap.
        gap = (out["date"] - g["date"].shift(k)).dt.days != k
        out.loc[gap, f"lag_{k}"] = np.nan
    out = out.dropna(subset=LAG_NAMES)

    out["dow"] = out["date"].dt.dayofweek          # Monday = 0 ... Sunday = 6
    out["month"] = out["date"].dt.month            # 1 ... 12
    out["roll_mean"] = out[LAG_NAMES].mean(axis=1)

    out = out.join(thresholds, on=["store", "item"], how="inner")
    out["label"] = label_from_thresholds(out["sales"].to_numpy(), out["q1"].to_numpy(), out["q2"].to_numpy())
    return out.drop(columns=["q1", "q2"]).reset_index(drop=True)


PAIR_FEATURES = ["pair_q1", "pair_q2"]


def add_pair_level(samples: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    """Optional ML features: the store-item's own tertile cut-offs (from training data only)."""
    t = thresholds.rename(columns={"q1": "pair_q1", "q2": "pair_q2"})
    return samples.join(t, on=["store", "item"])


def naive_baseline(samples: pd.DataFrame, thresholds: pd.DataFrame) -> np.ndarray:
    """Predict that the target day has the same class as YESTERDAY's sales (lag_1).

    Any model worth deploying must beat this. Report both numbers.
    """
    q = samples[["store", "item"]].join(thresholds, on=["store", "item"])
    return label_from_thresholds(samples["lag_1"].to_numpy(), q["q1"].to_numpy(), q["q2"].to_numpy())


def prepare(csv_path: str):
    """Convenience wrapper used by every train.py.

    Returns (train, val, test, split, thresholds, meta) where train/val/test are
    sample frames split by TARGET date.
    """
    df = load_sales(csv_path)
    split = split_dates(df)
    thresholds = fit_thresholds(df, before=split.test_start)
    samples = build_samples(df, thresholds)
    train = samples[samples["date"] < split.val_start]
    val = samples[(samples["date"] >= split.val_start) & (samples["date"] < split.test_start)]
    test = samples[samples["date"] >= split.test_start]
    meta = {
        "dataset": csv_path.replace("\\", "/").split("/")[-1],
        "data_range": [str(df["date"].min().date()), str(split.end.date())],
        "split": split.as_dict(),
        "known_stores": sorted(int(s) for s in df["store"].unique()),
        "known_items": sorted(int(i) for i in df["item"].unique()),
        "label_rule": "Low/Medium/High = tertiles of daily sales per store-item, fitted on data before test_start",
        "prev_sales_order": "oldest_to_newest (prev_sales[6] is the day before `date`)",
    }
    return train, val, test, split, thresholds, meta

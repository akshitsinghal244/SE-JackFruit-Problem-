"""Online feature building: one API request -> model inputs.

These functions MUST produce exactly what shared/data.py produced at training
time. tests/test_shared.py checks that the two paths agree.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

from .config import TABULAR_FEATURES, WINDOW


def lags_from_prev_sales(prev_sales: list[float]) -> np.ndarray:
    """prev_sales is oldest -> newest, so lag_1 is the LAST element."""
    if len(prev_sales) != WINDOW:
        raise ValueError(f"prev_sales must contain exactly {WINDOW} values")
    return np.asarray(prev_sales, dtype=float)[::-1]  # [lag_1, lag_2, ..., lag_7]


def tabular_row(store_id: int, item_id: int, date: dt.date, prev_sales: list[float]) -> np.ndarray:
    """The ML-row feature vector: store, item, dow, month, lag_1..lag_7, roll_mean (12 numbers)."""
    lags = lags_from_prev_sales(prev_sales)
    row = np.concatenate(([store_id, item_id, date.weekday(), date.month], lags, [lags.mean()]))
    assert row.shape[0] == len(TABULAR_FEATURES)
    return row.reshape(1, -1)


def sequence_from_prev_sales(prev_sales: list[float]) -> np.ndarray:
    """The DL-row input before scaling: oldest -> newest, i.e. the order an LSTM should read."""
    if len(prev_sales) != WINDOW:
        raise ValueError(f"prev_sales must contain exactly {WINDOW} values")
    return np.asarray(prev_sales, dtype=float)


def sequence_columns_oldest_first() -> list[str]:
    """Training-frame columns in LSTM reading order: lag_7 (oldest) ... lag_1 (newest)."""
    return [f"lag_{k}" for k in range(WINDOW, 0, -1)]

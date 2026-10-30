"""Checks that do not need torch / pennylane / fastapi."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from shared.config import TABULAR_FEATURES
from shared.data import build_samples, fit_thresholds, load_sales, prepare
from shared.features import sequence_columns_oldest_first, sequence_from_prev_sales, tabular_row
from shared.predictor import build_result


def tiny_frame():
    dates = pd.date_range("2017-01-01", periods=20, freq="D")
    return pd.DataFrame({"date": dates, "store": 1, "item": 1, "sales": np.arange(1, 21, dtype=float)})


def test_lags_are_the_previous_days():
    df = tiny_frame()
    s = build_samples(df, fit_thresholds(df, before=pd.Timestamp("2018-01-01")))
    row = s[s["date"] == pd.Timestamp("2017-01-10")].iloc[0]   # sales on that day = 10
    assert row["sales"] == 10
    assert row["lag_1"] == 9 and row["lag_7"] == 3            # yesterday = 9, a week ago = 3
    assert row["roll_mean"] == pytest.approx(np.mean([3, 4, 5, 6, 7, 8, 9]))
    assert row["dow"] == dt.date(2017, 1, 10).weekday()


def test_first_seven_days_have_no_sample():
    df = tiny_frame()
    s = build_samples(df, fit_thresholds(df, before=pd.Timestamp("2018-01-01")))
    assert s["date"].min() == pd.Timestamp("2017-01-08")


def test_gap_in_dates_drops_the_window():
    df = tiny_frame().drop(index=9)  # remove 2017-01-10
    s = build_samples(df, fit_thresholds(df, before=pd.Timestamp("2018-01-01")))
    # 2017-01-11's lag_1 would be 2017-01-10 (missing) -> no sample for it
    assert pd.Timestamp("2017-01-11") not in set(s["date"])


def test_tertile_labels_are_balanced_on_training_data():
    df = tiny_frame()
    df["sales"] = np.tile([5.0, 10.0, 20.0], 7)[:20]   # repeating pattern -> all 3 classes appear
    th = fit_thresholds(df, before=pd.Timestamp("2018-01-01"))
    s = build_samples(df, th)
    assert set(s["label"]) == {0, 1, 2}
    assert s.loc[s["sales"] == 20, "label"].eq(2).all()
    assert s.loc[s["sales"] == 5, "label"].eq(0).all()


def test_online_features_match_offline_features(synthetic_csv):
    """The most important test: serving must compute EXACTLY what training computed."""
    train, *_ = prepare(synthetic_csv)
    df = load_sales(synthetic_csv)
    for _, r in train.sample(25, random_state=0).iterrows():
        d = r["date"]
        hist = df[(df["store"] == r["store"]) & (df["item"] == r["item"]) & (df["date"] < d) & (df["date"] >= d - pd.Timedelta(days=7))]
        prev_sales = hist.sort_values("date")["sales"].tolist()  # oldest -> newest, like the API
        online = tabular_row(int(r["store"]), int(r["item"]), d.date(), prev_sales)[0]
        offline = r[TABULAR_FEATURES].to_numpy(dtype=float)
        np.testing.assert_allclose(online, offline)
        np.testing.assert_allclose(sequence_from_prev_sales(prev_sales),
                                   r[sequence_columns_oldest_first()].to_numpy(dtype=float))


def test_no_test_period_leaks_into_thresholds(synthetic_csv):
    df = load_sales(synthetic_csv)
    _, _, test, split, th, _ = prepare(synthetic_csv)
    df2 = df.copy()
    df2.loc[df2["date"] >= split.test_start, "sales"] *= 100   # wildly change the future
    th2 = fit_thresholds(df2, before=split.test_start)
    pd.testing.assert_frame_equal(th, th2)


def test_build_result_shape():
    r = build_result("ml", np.array([0.1, 0.784, 0.116]), 81.2, 3.21)
    assert r["category"] == "Medium" and r["confidence"] == 78.4
    assert set(r["probabilities"]) == {"low", "medium", "high"}
    assert abs(sum(r["probabilities"].values()) - 1) < 1e-3


def test_build_result_rejects_garbage():
    with pytest.raises(ValueError):
        build_result("ml", np.array([np.nan, 0.5, 0.5]), 80.0, 1.0)

"""Train each model on tiny synthetic data, then predict through its predictor class.

DL and QML tests are skipped automatically if torch / pennylane are not installed.
"""
import datetime as dt

import numpy as np
import pytest

from tests.conftest import train

REQ = dict(store_id=1, item_id=2, date=dt.date(2017, 9, 15), prev_sales=[41.0, 38, 45, 50, 47, 39, 44])


def check_probs(p):
    assert p.shape == (3,)
    assert np.all(p >= 0) and abs(p.sum() - 1) < 1e-5


def test_ml_train_and_predict(synthetic_csv, tmp_path):
    out = str(tmp_path / "ml")
    train("ml_service.train", synthetic_csv, out, "--algo", "rf")
    from ml_service.predictor import MLPredictor
    p = MLPredictor(out)
    check_probs(p.predict_proba(**REQ))
    info = p.model_info()
    assert info["algorithm"] == "RandomForestClassifier" and 0 <= info["accuracy"] <= 100


def test_ml_pair_level_option(synthetic_csv, tmp_path):
    out = str(tmp_path / "ml_pair")
    train("ml_service.train", synthetic_csv, out, "--algo", "rf", "--pair-level")
    from ml_service.predictor import MLPredictor
    p = MLPredictor(out)
    assert p.pair_level is not None and p.model.n_features_in_ == 14
    check_probs(p.predict_proba(**REQ))


def test_dl_preprocess_without_torch(synthetic_csv):
    from dl_service.preprocess import IdIndexer, SequenceScaler, frame_to_arrays
    from shared.data import prepare
    from shared.features import sequence_columns_oldest_first
    tr, *_ , meta = prepare(synthetic_csv)
    sc = SequenceScaler().fit(tr[sequence_columns_oldest_first()].to_numpy(dtype=float))
    seq, s, i, y = frame_to_arrays(tr, sc, IdIndexer(meta["known_stores"]), IdIndexer(meta["known_items"]))
    assert seq.shape == (len(tr), 7, 1) and seq.dtype == np.float32
    assert abs(seq.mean()) < 0.05 and abs(seq.std() - 1) < 0.05      # standardised on train
    assert s.min() >= 1 and i.min() >= 1                              # 0 is reserved for unknown
    assert IdIndexer([1, 2]).transform(99)[0] == 0


def test_qml_angle_pipeline_without_pennylane(synthetic_csv):
    from qml_service.preprocess import make_angle_pipeline
    from shared.config import TABULAR_FEATURES
    from shared.data import prepare
    tr, *_ = prepare(synthetic_csv)
    pipe = make_angle_pipeline(4).fit(tr[TABULAR_FEATURES].to_numpy(dtype=float))
    a = pipe.transform(tr[TABULAR_FEATURES].to_numpy(dtype=float))
    assert a.shape[1] == 4 and a.min() >= 0 and a.max() <= np.pi + 1e-9
    extreme = pipe.transform(np.full((1, len(TABULAR_FEATURES)), 1e6))
    assert extreme.min() >= 0 and extreme.max() <= np.pi + 1e-9      # clipped, never wraps around


def test_dl_train_and_predict(synthetic_csv, tmp_path):
    pytest.importorskip("torch")
    out = str(tmp_path / "dl")
    train("dl_service.train", synthetic_csv, out, "--epochs", "2")
    from dl_service.predictor import DLPredictor
    check_probs(DLPredictor(out).predict_proba(**REQ))


def test_qml_train_and_predict(synthetic_csv, tmp_path):
    pytest.importorskip("torch")
    pytest.importorskip("pennylane")
    out = str(tmp_path / "qml")
    train("qml_service.train", synthetic_csv, out,
          "--epochs", "1", "--n-train", "64", "--n-val", "32", "--n-test", "64")
    from qml_service.predictor import QMLPredictor
    check_probs(QMLPredictor(out).predict_proba(**REQ))

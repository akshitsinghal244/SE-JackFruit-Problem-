"""Train the ML service model: Random Forest / XGBoost on 12 tabular features.

Table row:  ML | Random Forest / XGBoost | store, item, day-of-week, month, 7 lags, rolling mean

Procedure
  1. build samples (shared/data.py)
  2. fit RF and (if installed) XGBoost on TRAIN, compare macro-F1 on VALIDATION
  3. refit the winner on TRAIN + VALIDATION
  4. report accuracy / macro-F1 on the held-out TEST (last 3 months) -> metadata.json

Usage:
    python -m ml_service.train --data data/train.csv --out artifacts/ml [--algo auto|rf|xgb] [--pair-level]
"""
from __future__ import annotations

import argparse
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

from shared.config import CLASSES, TABULAR_FEATURES
from shared.data import PAIR_FEATURES, add_pair_level, naive_baseline, prepare
from shared.metrics import evaluate, make_version, print_report, write_metadata


def make_model(algo: str, seed: int):
    if algo == "rf":
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=18,            # caps model size; full-depth trees on ~900k rows get huge
            min_samples_leaf=20,
            max_samples=0.5,         # each tree sees half the rows -> faster, more diverse
            n_jobs=-1,
            random_state=seed,
        )
    if algo == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=400,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.9,
            tree_method="hist",
            n_jobs=-1,
            random_state=seed,
        )
    raise ValueError(algo)


def xgb_available() -> bool:
    try:
        import xgboost  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="artifacts/ml")
    ap.add_argument("--algo", choices=["auto", "rf", "xgb"], default="auto")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--pair-level", action="store_true",
                    help="OPTIONAL (not in SADS v1.0): add each store-item's tertile cut-offs q1, q2 as 2 extra "
                         "features so the trees know what 'normal' means for that pair. Update the SADS if used.")
    a = ap.parse_args()

    train, val, test, split, thresholds, meta = prepare(a.data)
    features = TABULAR_FEATURES + (PAIR_FEATURES if a.pair_level else [])
    if a.pair_level:
        train, val, test = (add_pair_level(d, thresholds) for d in (train, val, test))
    print(f"samples: train={len(train):,} val={len(val):,} test={len(test):,}  split={split.as_dict()}")
    X = lambda d: d[features].to_numpy(dtype=float)  # noqa: E731
    y = lambda d: d["label"].to_numpy()                       # noqa: E731

    # ---- 2. model selection on validation
    candidates = ["rf", "xgb"] if a.algo == "auto" else [a.algo]
    if "xgb" in candidates and not xgb_available():
        print("xgboost not installed -> skipping XGBoost")
        candidates = [c for c in candidates if c != "xgb"]
    scores = {}
    for algo in candidates:
        m = make_model(algo, a.seed).fit(X(train), y(train))
        scores[algo] = f1_score(y(val), m.predict(X(val)), average="macro")
        print(f"validation macro-F1 {algo}: {scores[algo]:.4f}")
    best = max(scores, key=scores.get)
    print(f"selected: {best}")

    # ---- 3. refit on train + val
    full = pd.concat([train, val])
    model = make_model(best, a.seed).fit(X(full), y(full))

    # ---- 4. held-out test
    pred = model.predict(X(test))
    print_report(f"TEST (held-out last 3 months) - {best}", y(test), pred)
    test_metrics = evaluate(y(test), pred)
    baseline = evaluate(y(test), naive_baseline(test, thresholds))
    print(f"naive baseline (yesterday's class) accuracy: {baseline['accuracy']}%  "
          f"model: {test_metrics['accuracy']}%")

    os.makedirs(a.out, exist_ok=True)
    joblib.dump(model, os.path.join(a.out, "model.joblib"), compress=3)
    if a.pair_level:
        thresholds.reset_index().to_csv(os.path.join(a.out, "pair_thresholds.csv"), index=False)
    algorithm = {"rf": "RandomForestClassifier", "xgb": "XGBClassifier"}[best]
    importances = dict(zip(features, np.round(model.feature_importances_, 4).tolist()))
    path = write_metadata(a.out, {
        **meta,
        "service": "ml",
        "algorithm": algorithm,
        "version": make_version(best),
        "features": features,
        "classes": CLASSES,
        "validation_macro_f1": {k: round(v, 4) for k, v in scores.items()},
        "test_metrics": test_metrics,
        "baseline_test_metrics": baseline,
        "n_train": len(full),
        "n_test": len(test),
        "feature_importances": importances,
    })
    print(f"saved model + {path}")


if __name__ == "__main__":
    main()

"""Evaluation + metadata helpers shared by the three train.py scripts."""
from __future__ import annotations

import datetime as dt
import json
import os

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from .config import CLASSES


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "accuracy": round(100 * accuracy_score(y_true, y_pred), 2),       # percent, as in the API
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
    }


def print_report(title: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    print(f"\n=== {title} ===")
    print(classification_report(y_true, y_pred, labels=[0, 1, 2], target_names=CLASSES, digits=3))


def make_version(algorithm: str) -> str:
    return f"{algorithm}-{dt.date.today():%Y%m%d}"


def write_metadata(out_dir: str, metadata: dict) -> str:
    os.makedirs(out_dir, exist_ok=True)
    metadata = {**metadata, "trained_on": metadata.get("trained_on") or str(dt.date.today())}
    path = os.path.join(out_dir, "metadata.json")
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path


def read_metadata(model_dir: str) -> dict:
    with open(os.path.join(model_dir, "metadata.json")) as f:
        return json.load(f)

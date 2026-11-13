"""The contract every model service implements (no web framework imports here).

A predictor turns one validated request into 3 probabilities [P(Low), P(Medium), P(High)].
Everything else (category, confidence, response shape) is derived identically for
all three services in `build_result`, so ML, DL and QML can never disagree on format.
"""
from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod

import numpy as np

from .config import CLASSES
from .metrics import read_metadata


class BasePredictor(ABC):
    service_name: str = "base"  # "ml" | "dl" | "qml"

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.metadata = read_metadata(model_dir)
        self.known_stores = set(self.metadata["known_stores"])
        self.known_items = set(self.metadata["known_items"])
        self.load()

    @abstractmethod
    def load(self) -> None:
        """Load model artifacts from self.model_dir (called once at start-up)."""

    @abstractmethod
    def predict_proba(self, store_id: int, item_id: int, date: dt.date, prev_sales: list[float]) -> np.ndarray:
        """Return array of shape (3,) = [P(Low), P(Medium), P(High)]."""

    def model_info(self) -> dict:
        m = self.metadata
        return {
            "algorithm": m["algorithm"],
            "version": m["version"],
            "accuracy": m["test_metrics"]["accuracy"],
            "macro_f1": m["test_metrics"]["macro_f1"],
            "trained_on": m["trained_on"],
        }


def build_result(service_name: str, probs: np.ndarray, accuracy: float, latency_ms: float) -> dict:
    probs = np.asarray(probs, dtype=float).reshape(-1)
    if probs.shape[0] != 3 or not np.all(np.isfinite(probs)):
        raise ValueError("Model returned an invalid probability vector")
    probs = np.clip(probs, 0.0, None)
    probs = probs / probs.sum()                     # guarantee they sum to 1
    k = int(np.argmax(probs))
    return {
        "model": service_name,
        "category": CLASSES[k],
        "confidence": round(100 * float(probs[k]), 1),  # e.g. 78.4
        "probabilities": {
            "low": round(float(probs[0]), 4),
            "medium": round(float(probs[1]), 4),
            "high": round(float(probs[2]), 4),
        },
        "accuracy": accuracy,
        "latency_ms": round(latency_ms, 1),
    }

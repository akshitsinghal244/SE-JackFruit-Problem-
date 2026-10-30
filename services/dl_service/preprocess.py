"""DL preprocessing (no torch import, so it is unit-testable anywhere).

Table row:  DL | LSTM (7 steps) / MLP | scaled 7-day sequence + store/item embedding

* Scaling:   z = (log1p(sales) - mean) / std      mean/std from TRAINING rows only
             log1p squashes big-selling items so one scale works for all items.
* Embedding: store_id / item_id are labels, not quantities, so each id is mapped
             to a row index of an nn.Embedding table. Index 0 is reserved for
             "unknown" (the API already rejects unknown ids; this is defence in depth).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from shared.features import sequence_columns_oldest_first


class SequenceScaler:
    def __init__(self, mean: float = 0.0, std: float = 1.0):
        self.mean, self.std = float(mean), float(std)

    def fit(self, seqs: np.ndarray) -> "SequenceScaler":
        z = np.log1p(seqs)
        self.mean, self.std = float(z.mean()), float(z.std() or 1.0)
        return self

    def transform(self, seqs: np.ndarray) -> np.ndarray:
        return ((np.log1p(seqs) - self.mean) / self.std).astype(np.float32)

    def to_dict(self) -> dict:
        return {"mean": self.mean, "std": self.std}


class IdIndexer:
    """Maps raw ids (e.g. store 3) to embedding rows 1..N; 0 = unknown."""

    def __init__(self, ids: list[int]):
        self.ids = [int(i) for i in ids]
        self.index = {v: k + 1 for k, v in enumerate(self.ids)}

    def __len__(self) -> int:
        return len(self.ids) + 1  # +1 for the unknown slot

    def transform(self, values) -> np.ndarray:
        return np.array([self.index.get(int(v), 0) for v in np.atleast_1d(values)], dtype=np.int64)


def frame_to_arrays(df: pd.DataFrame, scaler: SequenceScaler, stores: IdIndexer, items: IdIndexer):
    """Training frame -> (seq[N,7,1] float32, store_idx[N], item_idx[N], label[N])."""
    seq = scaler.transform(df[sequence_columns_oldest_first()].to_numpy(dtype=float))
    return (
        seq[:, :, None],
        stores.transform(df["store"].to_numpy()),
        items.transform(df["item"].to_numpy()),
        df["label"].to_numpy(dtype=np.int64),
    )

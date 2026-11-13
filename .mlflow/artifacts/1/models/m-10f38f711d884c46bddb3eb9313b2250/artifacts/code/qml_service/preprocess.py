"""QML preprocessing (sklearn only, unit-testable without PennyLane).

Table row:  QML | VQC / QNN, 4-6 qubits | PCA-reduced features angle-encoded

Why each step exists
  1. StandardScaler  PCA looks for directions of largest variance; without scaling,
                     the large-valued lag columns would dominate store/dow/month.
  2. PCA(n_qubits)   angle encoding puts ONE number on ONE qubit, and we only have
                     4-6 qubits, so 12 features must be compressed to 4-6.
  3. MinMax->[0, pi] a rotation RY(theta) only makes sense for an angle; mapping to
                     [0, pi] uses the full range from |0> (theta=0) to |1> (theta=pi)
                     without wrapping around (0 and 2*pi would be the same state).
                     clip=True keeps unseen extreme inputs inside [0, pi].
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def make_angle_pipeline(n_qubits: int, seed: int = 42) -> Pipeline:
    if not 3 <= n_qubits <= 12:
        raise ValueError("n_qubits must be >= 3 (3 class read-outs) and small enough to simulate")
    return Pipeline([
        ("standardise", StandardScaler()),
        ("pca", PCA(n_components=n_qubits, random_state=seed)),
        ("to_angle", MinMaxScaler(feature_range=(0.0, np.pi), clip=True)),
    ])


def explained_variance(pipe: Pipeline) -> float:
    """Fraction of the (standardised) feature variance the kept components retain."""
    return float(pipe.named_steps["pca"].explained_variance_ratio_.sum())

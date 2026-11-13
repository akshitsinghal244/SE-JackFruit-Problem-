"""Train the QML service model (VQC on PCA-reduced, angle-encoded features).

Simulating a quantum circuit is slow, so the circuit is trained on a random
SUBSAMPLE of the training rows (default 1500) and evaluated on a subsample of the
held-out test period (default 3000). Both sizes are recorded in metadata.json;
mention this when you present the QML accuracy.

The angle pipeline (scaler + PCA + [0, pi] mapping) is fitted on ALL training rows,
since that part is classical and cheap.

Usage:
    python -m qml_service.train --data data/train.csv --out artifacts/qml [--qubits 4] [--layers 3]
"""
from __future__ import annotations

import argparse
import copy
import os

import joblib
import numpy as np
import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from qml_service.circuit import HybridVQC
from qml_service.preprocess import explained_variance, make_angle_pipeline
from shared.config import CLASSES, TABULAR_FEATURES
from shared.data import naive_baseline, prepare
from shared.metrics import evaluate, make_version, print_report, write_metadata


def subsample(df, n: int, seed: int):
    return df if n <= 0 or n >= len(df) else df.sample(n=n, random_state=seed)


@torch.no_grad()
def predict(model: nn.Module, angles: np.ndarray, batch: int = 256) -> np.ndarray:
    model.eval()
    x = torch.from_numpy(angles.astype(np.float32))
    return torch.cat([model(x[k:k + batch]).argmax(1) for k in range(0, len(x), batch)]).numpy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="artifacts/qml")
    ap.add_argument("--qubits", type=int, default=4)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--n-train", type=int, default=1500)
    ap.add_argument("--n-val", type=int, default=600)
    ap.add_argument("--n-test", type=int, default=3000, help="0 = whole test period (slow)")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=0.03)
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)

    train, val, test, split, thresholds, meta = prepare(a.data)

    # Classical part: fitted on all training rows.
    pipe = make_angle_pipeline(a.qubits, a.seed).fit(train[TABULAR_FEATURES].to_numpy(dtype=float))
    ev = explained_variance(pipe)
    print(f"PCA {len(TABULAR_FEATURES)} -> {a.qubits} components keeps {100 * ev:.1f}% of the variance")

    tr = subsample(train, a.n_train, a.seed)
    va = subsample(val, a.n_val, a.seed)
    te = subsample(test, a.n_test, a.seed)
    enc = lambda d: pipe.transform(d[TABULAR_FEATURES].to_numpy(dtype=float))  # noqa: E731
    x_tr, x_va, x_te = enc(tr), enc(va), enc(te)
    y_tr, y_va, y_te = (d["label"].to_numpy() for d in (tr, va, te))
    print(f"circuit training rows={len(tr)} val={len(va)} test={len(te)}")

    model = HybridVQC(a.qubits, a.layers)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    loss_fn = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(torch.from_numpy(x_tr.astype(np.float32)), torch.from_numpy(y_tr)),
                        batch_size=a.batch_size, shuffle=True)

    best_f1, best_state, bad = -1.0, None, 0
    for epoch in range(1, a.epochs + 1):
        model.train()
        total = 0.0
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total += loss.item() * len(yb)
        f1 = f1_score(y_va, predict(model, x_va), average="macro")
        print(f"epoch {epoch:2d}  loss {total / len(tr):.4f}  val macro-F1 {f1:.4f}")
        if f1 > best_f1:
            best_f1, best_state, bad = f1, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= a.patience:
                print("early stopping")
                break
    model.load_state_dict(best_state)

    pred = predict(model, x_te)
    print_report(f"TEST subsample (held-out last 3 months) - VQC {a.qubits} qubits", y_te, pred)
    test_metrics = evaluate(y_te, pred)
    baseline = evaluate(y_te, naive_baseline(te, thresholds))
    print(f"naive baseline accuracy: {baseline['accuracy']}%  model: {test_metrics['accuracy']}%")

    os.makedirs(a.out, exist_ok=True)
    joblib.dump(pipe, os.path.join(a.out, "angle_pipeline.joblib"))
    torch.save({"n_qubits": a.qubits, "n_layers": a.layers, "state_dict": model.state_dict()},
               os.path.join(a.out, "model.pt"))
    path = write_metadata(a.out, {
        **meta,
        "service": "qml",
        "algorithm": f"VQC ({a.qubits} qubits, {a.layers} StronglyEntangling layers, default.qubit simulator)",
        "version": make_version(f"vqc{a.qubits}q"),
        "classes": CLASSES,
        "inputs": f"12 tabular features -> standardise -> PCA({a.qubits}) -> [0, pi] -> RY angle encoding",
        "pca_explained_variance": round(ev, 4),
        "readout": "softmax(scale * <Z_q> + bias) for qubits 0,1,2 = Low, Medium, High",
        "best_validation_macro_f1": round(best_f1, 4),
        "test_metrics": test_metrics,
        "baseline_test_metrics": baseline,
        "n_train": len(tr),
        "n_test": len(te),
        "hyperparameters": {"epochs_max": a.epochs, "batch_size": a.batch_size, "lr": a.lr},
    })
    print(f"saved model + {path}")


if __name__ == "__main__":
    main()

"""Train the DL service model (LSTM over 7 days + store/item embeddings, or MLP).

Procedure
  1. build samples (shared/data.py), fit scaler on TRAIN only
  2. train with Adam + cross-entropy; after each epoch measure VALIDATION macro-F1
  3. keep the best epoch (early stopping, patience 3)
  4. report accuracy / macro-F1 on held-out TEST -> metadata.json

Usage:
    python -m dl_service.train --data data/train.csv --out artifacts/dl [--arch lstm|mlp] [--epochs 15]
"""
from __future__ import annotations

import argparse
import copy
import os

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from dl_service.model import build_model
from dl_service.preprocess import IdIndexer, SequenceScaler, frame_to_arrays
from shared.config import CLASSES
from shared.data import naive_baseline, prepare
from shared.features import sequence_columns_oldest_first
from shared.metrics import evaluate, make_version, print_report, write_metadata


def to_loader(arrays, batch_size: int, shuffle: bool) -> DataLoader:
    seq, s, i, y = arrays
    ds = TensorDataset(torch.from_numpy(seq), torch.from_numpy(s), torch.from_numpy(i), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


@torch.no_grad()
def predict(model: nn.Module, loader: DataLoader) -> np.ndarray:
    model.eval()
    out = [model(seq, s, i).argmax(dim=1) for seq, s, i, _ in loader]
    return torch.cat(out).numpy()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="artifacts/dl")
    ap.add_argument("--arch", choices=["lstm", "mlp"], default="lstm")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)

    train, val, test, split, thresholds, meta = prepare(a.data)
    print(f"samples: train={len(train):,} val={len(val):,} test={len(test):,}")

    scaler = SequenceScaler().fit(train[sequence_columns_oldest_first()].to_numpy(dtype=float))
    stores, items = IdIndexer(meta["known_stores"]), IdIndexer(meta["known_items"])
    tr = to_loader(frame_to_arrays(train, scaler, stores, items), a.batch_size, shuffle=True)
    va = to_loader(frame_to_arrays(val, scaler, stores, items), 4096, shuffle=False)
    te = to_loader(frame_to_arrays(test, scaler, stores, items), 4096, shuffle=False)

    model = build_model(a.arch, len(stores), len(items))
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    loss_fn = nn.CrossEntropyLoss()

    best_f1, best_state, bad_epochs = -1.0, None, 0
    for epoch in range(1, a.epochs + 1):
        model.train()
        total = 0.0
        for seq, s, i, y in tr:
            opt.zero_grad()
            loss = loss_fn(model(seq, s, i), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(y)
        val_f1 = f1_score(val["label"].to_numpy(), predict(model, va), average="macro")
        print(f"epoch {epoch:2d}  train loss {total / len(tr.dataset):.4f}  val macro-F1 {val_f1:.4f}")
        if val_f1 > best_f1:
            best_f1, best_state, bad_epochs = val_f1, copy.deepcopy(model.state_dict()), 0
        else:
            bad_epochs += 1
            if bad_epochs >= a.patience:
                print("early stopping")
                break
    model.load_state_dict(best_state)

    y_test = test["label"].to_numpy()
    pred = predict(model, te)
    print_report(f"TEST (held-out last 3 months) - {a.arch}", y_test, pred)
    test_metrics = evaluate(y_test, pred)
    baseline = evaluate(y_test, naive_baseline(test, thresholds))
    print(f"naive baseline accuracy: {baseline['accuracy']}%  model: {test_metrics['accuracy']}%")

    os.makedirs(a.out, exist_ok=True)
    # Only tensors + plain python types -> loads with torch.load(weights_only=True).
    torch.save({
        "arch": a.arch,
        "state_dict": model.state_dict(),
        "scaler": scaler.to_dict(),
        "store_ids": stores.ids,
        "item_ids": items.ids,
    }, os.path.join(a.out, "model.pt"))
    path = write_metadata(a.out, {
        **meta,
        "service": "dl",
        "algorithm": {"lstm": "LSTM (7 steps) + store/item embeddings", "mlp": "MLP + store/item embeddings"}[a.arch],
        "version": make_version(a.arch),
        "classes": CLASSES,
        "inputs": "log1p + standardised 7-day sequence (oldest->newest), store embedding (4), item embedding (8)",
        "best_validation_macro_f1": round(best_f1, 4),
        "test_metrics": test_metrics,
        "baseline_test_metrics": baseline,
        "n_train": len(train),
        "n_test": len(test),
        "hyperparameters": {"epochs_max": a.epochs, "batch_size": a.batch_size, "lr": a.lr, "patience": a.patience},
    })
    print(f"saved model + {path}")


if __name__ == "__main__":
    main()

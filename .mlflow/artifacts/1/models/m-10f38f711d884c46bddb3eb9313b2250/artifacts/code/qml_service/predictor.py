from __future__ import annotations

import datetime as dt
import os

import joblib
import numpy as np
import torch

from qml_service.circuit import HybridVQC
from shared.features import tabular_row
from shared.predictor import BasePredictor


class QMLPredictor(BasePredictor):
    service_name = "qml"

    def load(self) -> None:
        torch.set_num_threads(1)
        self.pipe = joblib.load(os.path.join(self.model_dir, "angle_pipeline.joblib"))
        ckpt = torch.load(os.path.join(self.model_dir, "model.pt"), map_location="cpu", weights_only=True)
        self.model = HybridVQC(ckpt["n_qubits"], ckpt["n_layers"])
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()

    @torch.no_grad()
    def predict_proba(self, store_id: int, item_id: int, date: dt.date, prev_sales: list[float]) -> np.ndarray:
        angles = self.pipe.transform(tabular_row(store_id, item_id, date, prev_sales)).astype(np.float32)
        logits = self.model(torch.from_numpy(angles))
        return torch.softmax(logits, dim=1)[0].numpy()

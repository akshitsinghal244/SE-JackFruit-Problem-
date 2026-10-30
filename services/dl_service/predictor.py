from __future__ import annotations

import datetime as dt
import os

import numpy as np
import torch

from dl_service.model import build_model
from dl_service.preprocess import IdIndexer, SequenceScaler
from shared.features import sequence_from_prev_sales
from shared.predictor import BasePredictor


class DLPredictor(BasePredictor):
    service_name = "dl"

    def load(self) -> None:
        torch.set_num_threads(1)
        ckpt = torch.load(os.path.join(self.model_dir, "model.pt"), map_location="cpu", weights_only=True)
        self.scaler = SequenceScaler(**ckpt["scaler"])
        self.stores = IdIndexer(ckpt["store_ids"])
        self.items = IdIndexer(ckpt["item_ids"])
        self.model = build_model(ckpt["arch"], len(self.stores), len(self.items))
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()

    @torch.no_grad()
    def predict_proba(self, store_id: int, item_id: int, date: dt.date, prev_sales: list[float]) -> np.ndarray:
        seq = self.scaler.transform(sequence_from_prev_sales(prev_sales)[None, :])   # [1,7]
        seq_t = torch.from_numpy(seq).unsqueeze(-1)                                   # [1,7,1]
        s = torch.from_numpy(self.stores.transform(store_id))
        i = torch.from_numpy(self.items.transform(item_id))
        logits = self.model(seq_t, s, i)
        return torch.softmax(logits, dim=1)[0].numpy()

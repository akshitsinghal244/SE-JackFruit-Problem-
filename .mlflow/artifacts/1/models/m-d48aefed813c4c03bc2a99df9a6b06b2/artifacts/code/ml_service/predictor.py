from __future__ import annotations

import datetime as dt
import os

import joblib
import numpy as np
import pandas as pd

from shared.features import tabular_row
from shared.predictor import BasePredictor


class MLPredictor(BasePredictor):
    service_name = "ml"

    def load(self) -> None:
        self.model = joblib.load(os.path.join(self.model_dir, "model.joblib"))
        if hasattr(self.model, "n_jobs"):
            self.model.n_jobs = 1  # one request = one row; thread start-up would only add latency
        # Optional --pair-level model: also needs each store-item's tertile cut-offs.
        self.pair_level = None
        if "pair_q1" in self.metadata.get("features", []):
            t = pd.read_csv(os.path.join(self.model_dir, "pair_thresholds.csv"))
            self.pair_level = {(int(r.store), int(r.item)): (r.q1, r.q2) for r in t.itertuples()}

    def predict_proba(self, store_id: int, item_id: int, date: dt.date, prev_sales: list[float]) -> np.ndarray:
        x = tabular_row(store_id, item_id, date, prev_sales)
        if self.pair_level is not None:
            q1, q2 = self.pair_level.get((store_id, item_id), (np.nan, np.nan))
            if np.isnan(q1):
                raise ValueError("No training history for this store-item pair")
            x = np.hstack([x, [[q1, q2]]])
        return self.model.predict_proba(x)[0]

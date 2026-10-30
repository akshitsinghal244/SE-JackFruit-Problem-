"""Neural networks for the DL service.

LSTM version (default):
    seq [B,7,1] --LSTM--> last hidden state h [B,H]
    store id ---Embedding--> e_s [B,4]
    item id  ---Embedding--> e_i [B,8]
    concat(h, e_s, e_i) --> Linear -> ReLU -> Dropout -> Linear --> 3 logits

MLP version (fallback named in the SADS):
    flatten(seq) [B,7] + embeddings --> Linear -> ReLU -> Linear -> ReLU -> Linear --> 3 logits
    Same inputs, but it has no built-in notion of "day 1 comes before day 2".

The network outputs LOGITS; softmax turns them into the 3 probabilities.
CrossEntropyLoss applies softmax internally during training.
"""
from __future__ import annotations

import torch
from torch import nn

STORE_DIM, ITEM_DIM = 4, 8


class DemandLSTM(nn.Module):
    def __init__(self, n_stores: int, n_items: int, hidden: int = 32, dropout: float = 0.2):
        super().__init__()
        self.store_emb = nn.Embedding(n_stores, STORE_DIM)
        self.item_emb = nn.Embedding(n_items, ITEM_DIM)
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(hidden + STORE_DIM + ITEM_DIM, 32), nn.ReLU(), nn.Dropout(dropout), nn.Linear(32, 3)
        )

    def forward(self, seq, store_idx, item_idx):
        _, (h_n, _) = self.lstm(seq)          # h_n: [num_layers=1, B, H]
        h = h_n[-1]                            # summary of the whole 7-day sequence
        z = torch.cat([h, self.store_emb(store_idx), self.item_emb(item_idx)], dim=1)
        return self.head(z)


class DemandMLP(nn.Module):
    def __init__(self, n_stores: int, n_items: int, window: int = 7, dropout: float = 0.2):
        super().__init__()
        self.store_emb = nn.Embedding(n_stores, STORE_DIM)
        self.item_emb = nn.Embedding(n_items, ITEM_DIM)
        self.net = nn.Sequential(
            nn.Linear(window + STORE_DIM + ITEM_DIM, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 3),
        )

    def forward(self, seq, store_idx, item_idx):
        z = torch.cat([seq.flatten(1), self.store_emb(store_idx), self.item_emb(item_idx)], dim=1)
        return self.net(z)


def build_model(arch: str, n_stores: int, n_items: int) -> nn.Module:
    if arch == "lstm":
        return DemandLSTM(n_stores, n_items)
    if arch == "mlp":
        return DemandMLP(n_stores, n_items)
    raise ValueError(arch)

"""Generate a fake train.csv with the same schema as the Kaggle dataset.

Use it ONLY to smoke-test the pipeline. Real results must come from the real data:
https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data  (train.csv)

Usage:
    python scripts/make_synthetic_data.py --out data/synthetic.csv --stores 3 --items 5
"""
import argparse

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/synthetic.csv")
    ap.add_argument("--stores", type=int, default=3)
    ap.add_argument("--items", type=int, default=5)
    ap.add_argument("--start", default="2013-01-01")
    ap.add_argument("--end", default="2017-12-31")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    dates = pd.date_range(a.start, a.end, freq="D")
    t = np.arange(len(dates)) / 365.0
    weekly = np.array([0.80, 0.93, 0.93, 1.00, 1.07, 1.15, 1.22])[dates.dayofweek]  # weekend peak
    yearly = 1 + 0.25 * np.sin(2 * np.pi * (dates.dayofyear.to_numpy() - 80) / 365.25)  # summer peak
    trend = 1 + 0.08 * t

    rows = []
    for s in range(1, a.stores + 1):
        store_base = rng.uniform(0.7, 1.4)
        for i in range(1, a.items + 1):
            item_base = rng.uniform(10, 60)
            lam = store_base * item_base * weekly * yearly * trend
            sales = rng.poisson(lam)
            rows.append(pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "store": s, "item": i, "sales": sales}))
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(a.out, index=False)
    print(f"wrote {len(df):,} rows to {a.out}")


if __name__ == "__main__":
    main()

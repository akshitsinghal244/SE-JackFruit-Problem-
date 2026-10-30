# RDCP model microservices (ML / DL / QML)

Tier 3 of the Retail Demand Category Predictor (SADS v1.0, sections 2.4, 2.6, 3.3.2).
Three independent FastAPI services. Each one takes the same request and returns
the same response shape:

| Service | Model | Input to model (built inside the service) | Output |
|---|---|---|---|
| `ml_service`  | Random Forest / XGBoost (best on validation wins) | store, item, day-of-week, month, 7 lags, rolling mean (12 features) | class + 3 probabilities |
| `dl_service`  | LSTM over 7 steps (or `--arch mlp`) | log1p + standardised 7-day sequence, store embedding (4), item embedding (8) | class + 3 probabilities |
| `qml_service` | VQC, 4 qubits default (4-6 allowed), PennyLane simulator | 12 features -> standardise -> PCA(n_qubits) -> [0, π] -> RY angle encoding | class + 3 probabilities |

## What the prediction means (read this before the demo)

The label is a **tertile of that store-item's own daily sales history**:
- **High** means "this item at this store will sell more than it usually does".
- It does **not** mean "this item sells more than other items".

Business use: a restocking signal per item (order more than usual, normal, or less than usual).
It is not a ranking of best-sellers.

---

## 1. Setup

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements/dev.txt
```

## 2. Data

Download `train.csv` from the Kaggle **Store Item Demand Forecasting Challenge**
(https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data) and save it as `data/train.csv`.
It has the columns `date,store,item,sales`, with 10 stores, 50 items, and daily rows for 2013-2017.

To smoke-test without it:
```bash
python scripts/make_synthetic_data.py --out data/synthetic.csv --stores 3 --items 5
```

Split, by time and never shuffled:
- **train:** everything before the validation period.
- **validation:** the 3 months before the test period. Used for model selection and early stopping.
- **test:** the last 3 months (SADS 2.6). All reported accuracies come from this period.

Tertile cut-offs are fitted only on data **before** the test period, so no future data leaks into the labels.

## 3. Train (run from the repo root)

```bash
python -m ml_service.train  --data data/train.csv --out artifacts/ml            # ~3 min on 2 cores, ~100 MB model
python -m dl_service.train  --data data/train.csv --out artifacts/dl            # LSTM; add --arch mlp for the MLP
python -m qml_service.train --data data/train.csv --out artifacts/qml --qubits 4
```

Each run prints a per-class report, the held-out accuracy and macro-F1, and a **naive baseline**:
"tomorrow has the same class as yesterday". Your model must beat it. Present both numbers.

Everything goes into `artifacts/<service>/metadata.json`:
- accuracy, macro-F1 and the confusion matrix
- the split dates and the label rule
- the baseline result

`/model-info` serves this metadata, and the accuracy also appears in every `/predict` response.

QML trains on a random subsample (`--n-train 1500` by default) because circuit simulation is slow.
It is evaluated on `--n-test 3000` rows of the test period. Both sizes are recorded in the metadata,
so state them when you present QML accuracy.

## 4. Run

```bash
export SERVICE_API_KEY=dev-key
MODEL_DIR=artifacts/ml  uvicorn ml_service.app:app  --port 8001
MODEL_DIR=artifacts/dl  uvicorn dl_service.app:app  --port 8002
MODEL_DIR=artifacts/qml uvicorn qml_service.app:app --port 8003

curl -s localhost:8001/predict -H "X-API-Key: dev-key" -H "Content-Type: application/json" \
  -d '{"store_id":3,"item_id":12,"date":"2017-09-15","prev_sales":[41,38,45,50,47,39,44]}'
```

Example response:
```json
{"model":"ml","category":"Medium","confidence":78.4,
 "probabilities":{"low":0.12,"medium":0.784,"high":0.096},"accuracy":81.2,"latency_ms":3.1}
```

Docker (internal network only, with artifacts mounted read-only):
```bash
echo "SERVICE_API_KEY=$(python -c 'import secrets;print(secrets.token_hex(32))')" > .env
docker compose -f docker-compose.models.yml up --build
```

## 5. Contract for the web-server teammate (Prediction Orchestrator)

| Endpoint | Success | Failure |
|---|---|---|
| `POST /predict` | 200, body as above | 401 `AUTH_INVALID`, 422 `VALIDATION_ERROR` (details[] has field + reason), 503 `SVC_UNAVAILABLE` (model not loaded), 500 `INTERNAL_ERROR` |
| `GET /health` | 200 `{"status":"UP","model_loaded":true}` | 503 `{"status":"DOWN","model_loaded":false}` |
| `GET /model-info` | 200 `{algorithm, version, accuracy, macro_f1, trained_on}` | 503 |

Rules for calling the services:
- Every call needs the header `X-API-Key`.
- Send `X-Request-ID` to correlate logs; the service echoes it back.
- All errors use the SADS 3.4 body: `{"error":{"code","message","details","request_id"}}`.
- Unknown `store_id` or `item_id` (not in the training data) returns a 422.

## 6. Decisions the SADS does not specify yet (fix these in the document)

1. **Order of `prev_sales`.** Here it is **oldest to newest**, so `prev_sales[6]` is the day before `date`.
   The web client must send it in that order.
2. **QML class read-out.** With only qubits there is no built-in "3 probabilities", so the design is
   `softmax(scale * <Z_q> + bias)` for qubits 0/1/2 = Low/Medium/High.
3. **Optional ML improvement (`--pair-level`).**
   - Adds the store-item's own tertile cut-offs as 2 extra features.
   - On full-size synthetic data it raised accuracy from 49% to 56% and macro-F1 from 0.36 to 0.49.
   - Reason: the trees otherwise have to rediscover 500 different "normal" levels from IDs alone.
   - If you adopt it, update the ML row of the SADS table.
4. **The DL row has no calendar input.** The LSTM never learns the target day's weekday. Adding a
   day-of-week embedding is a likely accuracy gain; it would also be a SADS change.
5. **Imbalanced test period.** Tertiles are fitted on all seasons, but the test period is Oct-Dec,
   so the classes there are not 1/3 each. Report **macro-F1** alongside accuracy.

## 7. Tests

```bash
pytest -q
```

The tests cover:
- Lags, gaps and tertile labels.
- That online (serving) features equal offline (training) features. This is the most important test.
- That the test period cannot leak into the thresholds.
- Each model: train, then predict.
- The full HTTP contract: auth, the 422 cases (including injection-style input), and health DOWN when no model is loaded.

The DL, QML and API tests skip automatically if torch, pennylane or fastapi are missing.

## Layout

```
shared/        config, data pipeline, feature builders, metrics, predictor base, FastAPI factory
ml_service/    train.py  predictor.py  app.py  Dockerfile
dl_service/    preprocess.py  model.py  train.py  predictor.py  app.py  Dockerfile
qml_service/   preprocess.py  circuit.py  train.py  predictor.py  app.py  Dockerfile
scripts/       make_synthetic_data.py
tests/
artifacts/     trained models (git-ignored, mounted read-only into containers)
```

Train and serve with the **same scikit-learn version**, because joblib models are not portable across versions.
The simplest way is to run training inside the service image.

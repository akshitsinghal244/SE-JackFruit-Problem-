import logging
import os

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from .. import services
from ..deps import audit, current_user
from ..errors import ApiError, rid
from ..models import Prediction, User
from ..schemas import PredictIn

router = APIRouter(tags=["predict"])
log = logging.getLogger("rdcp.predict")


def _compact(r: dict) -> dict:
    keep = ("status", "category", "confidence", "probabilities", "accuracy", "latency_ms", "code")
    return {k: r[k] for k in keep if k in r}


def _save(user_id: int, body: PredictIn, results: dict, cons: str) -> int | None:
    from .. import db
    s = db.SessionLocal()
    try:
        row = Prediction(user_id=user_id, store_id=body.store_id, item_id=body.item_id, pred_date=body.date,
                         prev_sales=body.prev_sales, results={k: _compact(v) for k, v in results.items()}, consensus=cons)
        s.add(row)
        s.commit()
        return row.id
    except Exception:                                    # SADS 3.4.1: DB failure must not hide the prediction
        log.exception("could not save prediction")
        return None
    finally:
        s.close()


@router.post("/predict")
async def predict(body: PredictIn, request: Request, user: User = Depends(current_user)):
    payload = {"store_id": body.store_id, "item_id": body.item_id, "date": body.date.isoformat(), "prev_sales": body.prev_sales}
    request_id = rid(request)
    results = await services.predict(payload, request_id)
    oks = [r for r in results.values() if r["status"] == "ok"]
    if not oks:
        errs = list(results.values())
        if all(e["code"] == "VALIDATION_ERROR" for e in errs):          # e.g. unknown store/item in training data
            raise ApiError(422, "VALIDATION_ERROR", "Invalid input", errs[0]["details"])
        timeouts = all(e["code"] == "SVC_TIMEOUT" for e in errs)
        raise ApiError(504 if timeouts else 502, "ALL_SERVICES_DOWN", "Prediction unavailable, try again later")
    cons = services.consensus(results)
    pid = await run_in_threadpool(_save, user.id, body, results, cons)
    from .. import db
    s = db.SessionLocal()
    try:
        audit(s, request, "PREDICT", "success" if len(oks) == 3 else "partial", user.id)
    finally:
        s.close()
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=200 if len(oks) == 3 else 207, content={
        "id": pid, "consensus": cons, "results": results, "history_saved": pid is not None, "request_id": request_id,
        "served_by": os.environ.get("HOSTNAME", "local")})   # pod name in Kubernetes: shows load-balancing across replicas


@router.get("/models/info")
async def models_info(request: Request, user: User = Depends(current_user)):
    return await services.model_info(rid(request))

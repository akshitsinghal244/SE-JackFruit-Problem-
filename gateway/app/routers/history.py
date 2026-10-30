import csv
import io

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select

from ..deps import audit, current_user, get_db
from ..errors import ApiError
from ..models import Prediction, User

router = APIRouter(tags=["history"])
MODELS = ["ml", "dl", "qml"]


def _rows(s, user: User, limit: int):
    return s.scalars(select(Prediction).where(Prediction.user_id == user.id).order_by(Prediction.id.desc()).limit(limit)).all()


def _dict(p: Prediction) -> dict:
    return {"id": p.id, "store_id": p.store_id, "item_id": p.item_id, "date": p.pred_date.isoformat(), "prev_sales": p.prev_sales,
            "results": p.results, "consensus": p.consensus, "created_at": p.created_at.isoformat(timespec="seconds") + "Z"}


@router.get("/history")
def history(limit: int = Query(50, ge=1, le=50), user: User = Depends(current_user), s=Depends(get_db)):
    return [_dict(p) for p in _rows(s, user, limit)]                       # FR-10: own records only (SEC-06)


@router.get("/history/{prediction_id:int}")
def one(prediction_id: int, user: User = Depends(current_user), s=Depends(get_db)):
    p = s.get(Prediction, prediction_id)
    if p is None or p.user_id != user.id:                    # SEC-06: someone else's record looks the same as a missing one
        raise ApiError(404, "NOT_FOUND", "Not found")
    return _dict(p)


@router.get("/history/export")
def export(request: Request, user: User = Depends(current_user), s=Depends(get_db)):
    buf = io.StringIO()
    w = csv.writer(buf)
    head = ["id", "created_at", "store_id", "item_id", "date", "prev_sales", "consensus"]
    for m in MODELS:
        head += [f"{m}_category", f"{m}_confidence", f"{m}_accuracy"]
    w.writerow(head)
    for p in _rows(s, user, 50):
        row = [p.id, p.created_at.isoformat(timespec="seconds"), p.store_id, p.item_id, p.pred_date.isoformat(), " ".join(map(str, p.prev_sales)), p.consensus]
        for m in MODELS:
            r = p.results.get(m, {})
            row += [r.get("category", ""), r.get("confidence", ""), r.get("accuracy", "")]
        w.writerow(row)
    audit(s, request, "EXPORT", "success", user.id)
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="rdcp_history.csv"'})

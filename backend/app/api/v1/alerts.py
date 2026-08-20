import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.enums import AlertFrequency
from app.models.users import Alert, User
from app.services.alert_evaluation import evaluate_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreateRequest(BaseModel):
    alert_type: str  # topic | act | department | ministry | court | document_type
    target: dict
    frequency: AlertFrequency = AlertFrequency.DAILY


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(payload: AlertCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    alert = Alert(user_id=user.id, alert_type=payload.alert_type, target=payload.target, frequency=payload.frequency)
    db.add(alert)
    await db.flush()
    return {"id": alert.id, "alert_type": alert.alert_type, "target": alert.target, "frequency": alert.frequency.value}


@router.get("")
async def list_alerts(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "target": a.target,
                "frequency": a.frequency.value,
                "is_active": a.is_active,
                "last_checked_at": a.last_checked_at,
            }
            for a in rows
        ]
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    alert = await db.get(Alert, alert_id)
    if alert is None or alert.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Alert not found"}})
    await db.delete(alert)
    await db.flush()
    return None


@router.post("/{alert_id}/check-now")
async def check_alert_now(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    alert = await db.get(Alert, alert_id)
    if alert is None or alert.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "not_found", "message": "Alert not found"}})
    matches = await evaluate_alert(db, alert)
    return {"matched_documents": [{"id": d.id, "title": d.title} for d in matches]}

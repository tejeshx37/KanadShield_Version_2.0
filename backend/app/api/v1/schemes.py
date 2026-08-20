from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.scheme_matching import match_schemes

router = APIRouter(prefix="/schemes", tags=["schemes"])


class SchemeMatchRequest(BaseModel):
    """Manual profile input — free-form derived attributes, never raw
    identity documents. Keys should match the `field` names used in
    scheme eligibility_rules JSONB (e.g. age, income_annual, state,
    occupation_category)."""

    profile: dict


@router.post("/match")
async def match(payload: SchemeMatchRequest, db: AsyncSession = Depends(get_db)):
    results = await match_schemes(db, payload.profile)
    return {"results": [r.__dict__ for r in results]}

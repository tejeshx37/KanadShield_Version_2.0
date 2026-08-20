import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.graph_service import get_entity_graph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/entities/{entity_id}")
async def entity_graph(entity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_entity_graph(db, entity_id)

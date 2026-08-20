import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.entity_repositories import CourtRepository, DepartmentRepository, MinistryRepository

router = APIRouter(tags=["organizations"])


@router.get("/departments")
async def list_departments(db: AsyncSession = Depends(get_db)):
    return await DepartmentRepository(db).list(limit=500)


@router.get("/ministries")
async def list_ministries(db: AsyncSession = Depends(get_db)):
    return await MinistryRepository(db).list(limit=500)


@router.get("/courts")
async def list_courts(db: AsyncSession = Depends(get_db)):
    return await CourtRepository(db).list(limit=500)

from sqlalchemy import select

from app.models.document import Act, GR, Gazette, Judgment, Scheme
from app.models.organizations import Court, Department, Ministry
from app.models.relationships import LegalRelationship
from app.models.users import User
from app.repositories.base import BaseRepository


class ActRepository(BaseRepository[Act]):
    model = Act

    async def get_by_document_id(self, document_id):
        result = await self.session.execute(select(Act).where(Act.document_id == document_id))
        return result.scalar_one_or_none()


class JudgmentRepository(BaseRepository[Judgment]):
    model = Judgment

    async def get_by_document_id(self, document_id):
        result = await self.session.execute(select(Judgment).where(Judgment.document_id == document_id))
        return result.scalar_one_or_none()


class GRRepository(BaseRepository[GR]):
    model = GR


class GazetteRepository(BaseRepository[Gazette]):
    model = Gazette


class SchemeRepository(BaseRepository[Scheme]):
    model = Scheme

    async def list_active(self, *, limit: int = 200):
        result = await self.session.execute(select(Scheme).where(Scheme.is_active.is_(True)).limit(limit))
        return list(result.scalars().all())


class DepartmentRepository(BaseRepository[Department]):
    model = Department


class MinistryRepository(BaseRepository[Ministry]):
    model = Ministry


class CourtRepository(BaseRepository[Court]):
    model = Court


class RelationshipRepository(BaseRepository[LegalRelationship]):
    model = LegalRelationship

    async def list_for_entity(self, entity_id, *, limit: int = 100):
        result = await self.session.execute(
            select(LegalRelationship)
            .where(
                (LegalRelationship.source_entity_id == entity_id)
                | (LegalRelationship.target_entity_id == entity_id)
            )
            .limit(limit)
        )
        return list(result.scalars().all())


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

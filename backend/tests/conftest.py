import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base

TEST_DB_URL = get_settings().DATABASE_URL.rsplit("/", 1)[0] + "/kanadshield_test"


@pytest.fixture(scope="session", autouse=True)
def _create_test_database():
    """Synchronous, one-time setup: create the test database and schema.
    Runs outside any asyncio event loop so it can't collide with per-test
    loops created by pytest-asyncio."""
    import asyncio

    async def _setup():
        admin_url = get_settings().DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
        admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        async with admin_engine.connect() as conn:
            await conn.execute(sa.text("DROP DATABASE IF EXISTS kanadshield_test"))
            await conn.execute(sa.text("CREATE DATABASE kanadshield_test"))
        await admin_engine.dispose()

        engine = create_async_engine(TEST_DB_URL)
        async with engine.begin() as conn:
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.new_event_loop().run_until_complete(_setup())


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, poolclass=sa.pool.NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_engine):
    from app.api import deps as deps_module
    from app.main import app

    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[deps_module.get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

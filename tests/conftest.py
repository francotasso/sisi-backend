from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import respx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import verify_admin_token, verify_editor_access
from app.main import app

TEST_DSN = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture(scope="session")
async def engine():
    async_engine = create_async_engine(TEST_DSN, echo=False)

    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield async_engine
    await async_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(engine, tables) -> AsyncGenerator[AsyncSession, Any]:
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def override_get_db(db_session: AsyncSession):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
def admin_payload() -> dict:
    return {
        "sub": "test-admin-id",
        "email": "admin@test.com",
        "user_metadata": {"role": "admin"},
    }


@pytest_asyncio.fixture
def editor_payload() -> dict:
    return {
        "sub": "test-editor-id",
        "email": "editor@test.com",
        "user_metadata": {"role": "editor"},
    }


@pytest_asyncio.fixture
async def override_admin_auth(admin_payload: dict):
    async def _override():
        return admin_payload

    app.dependency_overrides[verify_admin_token] = _override
    yield
    app.dependency_overrides.pop(verify_admin_token, None)


@pytest_asyncio.fixture
async def override_editor_auth(editor_payload: dict):
    async def _override():
        return editor_payload

    app.dependency_overrides[verify_editor_access] = _override
    yield
    app.dependency_overrides.pop(verify_editor_access, None)


@pytest_asyncio.fixture
async def override_admin_and_editor_auth(admin_payload: dict):
    async def _override_admin():
        return admin_payload

    async def _override_editor():
        return admin_payload

    app.dependency_overrides[verify_admin_token] = _override_admin
    app.dependency_overrides[verify_editor_access] = _override_editor
    yield
    app.dependency_overrides.pop(verify_admin_token, None)
    app.dependency_overrides.pop(verify_editor_access, None)


@pytest_asyncio.fixture
async def client(
    override_get_db, override_admin_and_editor_auth
) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def editor_client(
    override_get_db, override_editor_auth
) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def client_no_auth(override_get_db) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_supabase_auth():
    base_url = "https://ganrqmmrwoqfiynjookl.supabase.co/auth/v1"
    with respx.mock(base_url=base_url, assert_all_called=False) as respx_mock:
        yield respx_mock


@pytest_asyncio.fixture
async def category_data() -> dict:
    return {
        "id": uuid4(),
        "name": "Test Category",
        "slug": "test-category",
    }


@pytest_asyncio.fixture
async def category(db_session: AsyncSession, category_data: dict):
    from app.modules.categories.models import Category

    cat = Category(
        id=category_data["id"],
        name=category_data["name"],
        slug=category_data["slug"],
    )
    db_session.add(cat)
    await db_session.flush()
    return cat


@pytest_asyncio.fixture
async def product_data(category) -> dict:
    return {
        "name": "Test Product",
        "price": 29.99,
        "category_id": str(category.id),
        "description": "A test product description",
        "short_description": "Short test",
        "stock": True,
        "stock_count": 10,
        "best_seller": False,
        "sku": "TST-001",
    }


@pytest_asyncio.fixture
async def product(db_session: AsyncSession, category, product_data: dict):
    from app.modules.products.models import Product

    prod = Product(
        name=product_data["name"],
        slug="test-product",
        price=product_data["price"],
        category_id=category.id,
        description=product_data["description"],
        short_description=product_data["short_description"],
        stock=product_data["stock"],
        stock_count=product_data["stock_count"],
        best_seller=product_data["best_seller"],
        sku=product_data["sku"],
    )
    db_session.add(prod)
    await db_session.flush()
    return prod

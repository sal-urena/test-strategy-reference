import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import get_session
from app.main import app

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread":False},
        poolclass=StaticPool,
        )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
            yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
async def client(session):
    def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    async with AsyncClient(
         transport=ASGITransport(app=app),
         base_url="http://test",
        ) as client:
         yield client
    app.dependency_overrides.clear()


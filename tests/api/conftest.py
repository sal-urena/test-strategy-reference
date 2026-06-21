import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from typing import NamedTuple

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

class AuthedUser(NamedTuple):
     id: int
     headers:dict

@pytest.fixture
def make_user(client):
    async def _make(username,password):
        json_body ={
            "username": username,
            "password": password
            }
        registered_response =await client.post(url=("/register"), json=json_body)
        assert registered_response.status_code==200
        registered_response_json = registered_response.json()
        user_id =registered_response_json["id"]
        response = await client.post(url="/login", json=json_body)
        assert response.status_code ==200
        response_body = response.json()
        bearer_token = response_body["access_token"]
        user = AuthedUser(id=user_id, headers={"Authorization": f"Bearer {bearer_token}"})
        return user
    return _make

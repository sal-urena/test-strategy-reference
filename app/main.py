from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import User, UserCreate, Item,ItemCreate
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(User).where(User.username == user.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    db_user = User(
        username=user.username,
        hashed_password=hash_password(user.password)
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return{"id":db_user.id, "username":db_user.username}

@app.post("/login")
def login(credentials: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.username == credentials.username)
    ).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub":user.username})
    return {"access_token":token, "token_type":"bearer"} # nosec B105 # public OAuth2 token type (RFC 6750), not a secret

def get_current_user(
        creds: HTTPAuthorizationCredentials = Depends(security),
        session: Session = Depends(get_session),
) -> User:
    token = creds.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user =session.exec(
        select(User).where(User.username ==username)
    ).first()
    if user is None:
        raise HTTPException(status_code=401, detail = "User not found")
    
    return user

@app.post("/items")
def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    assert current_user.id is not None # nosec B101 # assert it to bypass Pylance error. No risk introduced when removed at compile
    db_item = Item(
        name=item.name,
        description=item.description,
        owner_id=current_user.id,
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.get("/items")
def list_items(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    items = session.exec(
        select(Item).where(Item.owner_id == current_user.id)
    ).all()
    return items

@app.get("/items/{item_id}")
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    item = session.get(Item, item_id)
    if item is None or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}")
def update_item(
    item_id: int,
    updated: ItemCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    item = session.get(Item, item_id)
    if item is None or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.name = updated.name
    item.description = updated.description
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    item = session.get(Item, item_id)
    if item is None or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    session.delete(item)
    session.commit()
    return {"ok": True}
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password:str

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str|None= None
    owner_id: int = Field(foreign_key="user.id")

class UserCreate(SQLModel):
    username: str
    password: str

class ItemCreate(SQLModel):
    name:str
    description:str |None=None
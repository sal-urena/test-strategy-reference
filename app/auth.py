from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError

SECRET_KEY="@PPL3S@UC3"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

def hash_password(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
        )

def create_access_token(data:dict)-> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str)-> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
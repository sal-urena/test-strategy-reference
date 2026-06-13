import pytest
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.auth import hash_password, verify_password, create_access_token, decode_access_token, SECRET_KEY, ALGORITHM

password = "mypassword"
token_payload = {"sub":"bill"}

def test_hash_password():
    hashed_password = hash_password(password)
    assert password != hashed_password

def test_verify_password():
    hashed_password = hash_password(password)
    assert verify_password(hashed_password=hashed_password, plain_password=password)

def test_verify_wrong_password_identified():
    hashed_password = hash_password(password)
    assert not verify_password(hashed_password=hashed_password, plain_password="alternatepassword")

def test_verify_hash_password_salt():
    hashed_password1 = hash_password(password)
    hashed_password2 = hash_password(password)
    assert hashed_password1 != hashed_password2

def test_create_access_token():
    token = create_access_token(token_payload)
    decoded_token =decode_access_token(token)
    assert decoded_token is not None
    assert decoded_token["sub"] == "bill"

def test_expired_access_token():
    expire = datetime.now(timezone.utc)+timedelta(minutes=-30)
    expired_payload = {"sub": "bill", "exp":expire}
    expired_token = jwt.encode(expired_payload, SECRET_KEY, ALGORITHM)
    assert decode_access_token(expired_token) is None

def test_garbage_token():
    assert decode_access_token("tampered_token") is None

def test_hash_password_over_boundary():
    with pytest.raises(ValueError):
        hash_password("A"*73)

def test_hash_password_within_boundary():
    hashed_password = hash_password("A"*72) 
    assert verify_password(("A"*72), hashed_password)
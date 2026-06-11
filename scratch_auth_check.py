from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

h = hash_password("hunter2")
print("hash:     ", h)
print("good pw:  ", verify_password("hunter2", h))
print("bad pw:   ", verify_password("wrong", h))

token = create_access_token({"sub": "sal"})
print("token:    ", token)
print("decoded:  ", decode_access_token(token))

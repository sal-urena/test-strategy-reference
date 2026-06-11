# sdet-demo-api

A small, deliberately security-conscious REST API built as a **system-under-test (SUT)** for an
API automation portfolio. The application itself is the supporting cast; the headline artifact is the
**pytest + httpx** suite written against it (see [Testing](#testing)).

The API implements JWT-authenticated user accounts and **owner-scoped CRUD** on items — enough surface
to demonstrate real API-testing concerns: authentication, authorization, negative paths, and
information-disclosure defenses.

> This is a demo SUT, not a production service (see [Notes & deliberate trade-offs](#notes--deliberate-trade-offs)).

## Stack

- **FastAPI** — web framework + auto-generated Swagger docs
- **SQLModel** (SQLAlchemy + Pydantic) over **SQLite** — models and persistence
- **python-jose** — JWT signing/verification
- **bcrypt** — password hashing (called directly; see trade-offs)
- **httpx + pytest** — the test suite

Requires **Python 3.10+** (uses `int | None` union syntax).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # fish: source .venv/bin/activate.fish
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8001
```

Port 8001 is used because 8000 is commonly occupied. Once running:

- Swagger UI: http://127.0.0.1:8001/docs
- The SQLite database (`database.db`) is created automatically on startup.

## API

| Method | Path            | Auth        | Description                                   |
|--------|-----------------|-------------|-----------------------------------------------|
| POST   | `/register`     | none        | Create a user. Duplicate username → 400.      |
| POST   | `/login`        | none        | Returns a JWT access token.                   |
| POST   | `/items`        | Bearer      | Create an item (owner stamped from token).    |
| GET    | `/items`        | Bearer      | List **only the caller's** items.             |
| GET    | `/items/{id}`   | Bearer      | Fetch one of the caller's items.              |
| PUT    | `/items/{id}`   | Bearer      | Update one of the caller's items.             |
| DELETE | `/items/{id}`   | Bearer      | Delete one of the caller's items.             |

**Auth flow:** `POST /login` → copy `access_token` → send `Authorization: Bearer <token>` on item
routes (or paste it into Swagger's **Authorize** button).

## Security design decisions

These are intentional and are the most interesting things to test:

- **Server-stamped ownership.** `ItemCreate` deliberately omits `owner_id`; the server sets it from the
  authenticated user. A client cannot create or reassign items on behalf of another user
  (broken-access-control prevention).
- **404, not 403, for another user's item.** Requesting an item you don't own returns the *same* 404 as
  a non-existent item. Returning 403 would confirm the resource exists and let an attacker enumerate
  valid IDs (existence disclosure).
- **Uniform 401 on login.** Bad username and bad password return the identical 401 — no user-enumeration
  oracle.
- **Two distinct unauthenticated responses.** A *missing* `Authorization` header is rejected by the
  `HTTPBearer` scheme (**403**) before any handler runs; a *present but invalid/expired* token is rejected
  inside `get_current_user` (**401**). Tests assert both.
- **Passwords are bcrypt-hashed**, never stored or returned in plaintext.

## Project layout

```
app/
  database.py   # SQLite engine, session dependency, table creation
  models.py     # User / Item tables + UserCreate / ItemCreate request bodies
  auth.py       # bcrypt hashing + JWT create/decode
  main.py       # routes + HTTPBearer + get_current_user dependency
tests/          # pytest + httpx suite (in progress)
```

## Testing

The pytest + httpx suite is the portfolio deliverable. Planned coverage:

- Happy-path CRUD lifecycle (register → login → create → read → update → delete)
- **403 vs 401** — missing header vs. malformed/expired token
- **404 owner-scoping** — user B cannot see user A's item
- **Forged `owner_id`** in the request body is ignored
- **bcrypt 72-byte** password-length boundary

```bash
python -m pytest          # run from the project root
```

## Notes & deliberate trade-offs

- **SQLite + a committed `database.db`** keep the demo zero-setup. A real service would use a managed
  database and a clean per-test database/transaction rollback.
- **`SECRET_KEY` is hardcoded** in `auth.py` for demo convenience. In production it would come from a
  secret manager / environment variable and never be committed.
- **bcrypt is called directly** rather than via `passlib`: `passlib[bcrypt]` is effectively unmaintained
  and breaks against `bcrypt` 5.x (it reads a removed internal attribute). Calling `bcrypt` directly is
  the current FastAPI-ecosystem recommendation — and a reminder that "popular" doesn't mean "maintained,"
  exactly the kind of supply-chain risk dependency auditing in CI is meant to catch.

# Test Strategy — Reference API SUT

## 1. Purpose & scope
This repository contains a FastAPI system under test and the associated test layers. The deliverable for it is the testing suite and test strategy document outlining the testing strategy for this project, not a test catalog.

## 2. The testing pyramid, applied to this app

The testing of the SUT is focused on two main layers. It has a large collection of unit tests to cover core functionality and a middle layer of API for integration testing. There is no E2E/UI cap since the app has no UI. 

**Unit Tests**
The auth.py module is unit tested as it is pure functionality with easily tested input and output.

**API Tests**
The main.py is a collection of API routes so it's best tested through httpx to confirm the expected functionality of each route as well as authentication and security. 

The database and model modules contain wrappers for existing packages (SQLModel, SQLAlchemy) so they are tested through main.py.

## 3. Layers implemented

### 3.1 Unit layer (`tests/unit/`)
The auth.py module's functions are tested through unit tests focusing on an individual test per outcome and can return results quickly. Since only one piece of functionality is verified per test, we can quickly determine exactly what fails. These are pure functions (no HTTP, no databases, no fixtures) which makes them testable in isolation.

**Key Call Outs**
test_expired_access_token 
- This unit test creates its own expired token so that the test does not require waiting for a real token to expire. 
- The token is created using the actual SECRET_KEY and ALGORITHM as the function uses so we can confirm any failures are on expiration only, not incorrect secret or algorithm.  

test_hash_password_over_boundary
- This unit test confirms that bcrypt now returns a ValueError when going over 72 bytes instead of silently truncating

### 3.2 API layer (`tests/api/`)
This section outlines the testing done at the API layer. We are using httpx to perform async tests of the endpoints in this SUT. The API tests validate the code of the full endpoint as opposed to the unit tests which only test isolated functionality.

#### What this layer covers — and why each is an API concern, not a unit one
- **Owner-scoped 404** — another user's item returns 404, not 403 (existence-denial / no id-enumeration oracle). This is at the API layer since owner scoping requires item creation in a database so cannot be tested at the pure unit layer. 
- **Uniform 401, distinguished by layer not status** — missing/wrong-scheme header → 401 `"Not authenticated"`
  (rejected by `HTTPBearer` before any handler); present-but-bad/expired token → 401 `"Invalid or expired token"`
  (inside `get_current_user`). By verifying the specific 401 message we can verify that we tested all three versions of the error handling and are not masking a bug by only capturing the first in the chain.
- **Forged `owner_id` is ignored** — server stamps `owner_id` from the token; an `owner_id` in the body has no effect. This can only be tested at API level since the owner_id is stamped in the db and the reading of the endpoint body is handled in the API endpoint.
- **Login uniformity** — bad username and bad password are indistinguishable across body AND status (no enumeration oracle). This test is important as it ensures bad actors are prevented from testing the system for usernames by having uniform messaging on both bad usernames and passwords.

#### The isolation rig — three decisions (the architecturally interesting part)

**The trap this whole rig exists to avoid:** `app/database.py` creates a module-level `engine` bound to the
**real `database.db`**, and every route depends on `get_session`, which yields against that engine. So any
test that hits a route writes to the committed DB and fails on rerun (e.g. `/register` → 400 "Username already
taken" the second time). Each decision below is a countermeasure.

1. **In-memory SQLite + `StaticPool`** (`session` fixture)
   We created a fresh database in memory for each test so that each can be run in isolation.
   - Why `StaticPool` *specifically*: plain `sqlite://` hands each connection its own separate in-memory DB,
     so the tables the fixture creates are invisible to the connection the request runs on.
   - **Failure-if-you-don't:** confusing "empty DB" failures — tables exist in the fixture, gone in the request.

2. **`app.dependency_overrides[get_session]`** (`client` fixture)
   The override closure directs the calls to the SUT to our instanced db session for testing.
   - Why an override and not monkeypatching the engine: `dependency_overrides` is FastAPI's first-class seam
     and respects the generator-dependency lifecycle.
   - **Teardown blast radius (from the conftest review):** `.clear()` wipes *every* override, not just the one
     this fixture added. Fine today (one override); note `.pop(get_session, None)` as the surgical form for when
     a second override appears.

3. **Async `httpx.AsyncClient` + `ASGITransport`** (over `TestClient`)
   - Mental model: **async client, sync app, sync DB session — only the client is async.**
   - Why async at all: a deliberate async-fluency goal + a concurrency-ready substrate.
     **Honest caveat (don't over-claim):** for this sequential suite, async buys *neither* isolation *nor* perf —
     the value is fluency and the substrate, not speed.
   - Plumbing it needs: `pytest-asyncio` with `asyncio_mode = auto`.

#### The authenticated-client factory (`make_user`)
This fixture is used to create an async function to create users in the instanced database created for the test.
- Composes to **N users** — `alice = await make_user(...)`, `bob = await make_user(...)` — which is what the
  two-user owner-scope tests require.
- Returns an identity-rich `AuthedUser(id, headers)` so a test can assert the returned owner == the actor.
- Registers + logs in through the **real `/register` + `/login` endpoints** (not a hand-minted token) — so the
  fixture exercises the genuine auth path; the header key must be `Authorization` (that's what `HTTPBearer` reads).
- Asserts `200` on both legs inside the helper: a setup failure surfaces as a pytest *error*, not a *failure* —
  the correct signal that the test never reached the behavior under test.

## 3.3 Security Layer (bandit)
Security is tested using bandit to review the code base for potential security issues. It finds three results, one that was intentionally planted and two additional findings.  The findings were then triaged and updated accordingly. The key call out with Bandit's reports is that all results must still be reviewed by a human to verify its authenticity and true severity. 

**KEY Call outs**
Security finding 1: auth.py line 5. It flags this as a low severity potential stored password. This is actually a high security risk because it is the secret used to generate tokens and bad actors would be able to mint their own tokens with it.  This was deliberately placed in the system for demo purposes. We then created a bandit baseline so we can ignore it in CI runs. In the real world, we would have to address this issue and would never put it in baseline as this should be a hard gate for deployment. 

Security finding 2: main.py line 45. Bandit flags bearer as a possible password. No security risk as bearer is a Auth token type so we use a nosec comment to ignore the warning. There is a cosmetic issue where bandit is giving a warning that there is nothing to ignore on this line. This is possibly because of the multi key dict causing issues with the nosec-usage tracker. 

Security finding 3: main.py line 74. Bandit flags the use of an assert which would be stripped out at compile. There is no risk in this situation since the assert is there to silence a Pylance error and its removal has no impact on the code. This would only be an issue if the assert was being used in code for security reasons. This is also ignored using a nosec. 

Security issues 1 is a true finding and I use baseline to allow us to still deploy in CI but we don't want to ignore it since it is a valid finding. Finding 2 and 3 are not issues so we ignore it at the code level with nosec as we do not want them showing up in any reporting. 

## 4. Where a bug lands (unit vs API) — worked examples
Example 1: User Authentication
In a situation where the hash_password function was changed to introduce a bug such as the password not hashing and instead storing as plaintext, the unit tests would catch this at the pure functionality level. However, an API test would still pass in the case that the verify_password function was comparing plaintext to plaintext.

Example 2: Item Ownership
The database storage of item ownership can only be tested through the API since there is no pure function that establishes this. If for example, the "/items" route was broken so that it no longer verified the item ownership to the user, the API tests would surface this but there would be no way to directly test this at the unit test level.

Example 3: Expired tokens
The testing of the decode_access_token in the situation of an expired token is handled solely at the unit test level since we can test that cleanly by generating an expired token then testing the functionality. The expired token is a purely functional feature and requires no database or HTTP to access it. A test at the API level would instead focus on testing the error handling and would be validating a different piece of functionality. Keeping the test at the unit level makes it the purest version of the test. 


## 5. Test data & isolation
Each run of the test suite runs against a clean environment. For each unit test, it is a functional test in isolation and focused on testing only one outcome at a time. For the API tests a fresh database is created in memory using a test fixture. This ensures that all tests run cleanly and no unexpected data can impact the outcome.

#### The isolation guarantee
The database is made cleanly using a session fixture that overrides and directs the API calls to this in memory database. We use static pool to ensure all connections in a given run share the same database.

#### Why fixtures live at the API layer, not the unit layer
We have fixtures in the API layer to facilitate isolated testing. By generating our instanced session, client and users we can ensure isolation in our tests. This is not required at the unit test level since it is purely functional testing.

#### Test data approach
The unit tests use simple string variables for their testing since that is all that is required to test their pure functionality. 

The API tests require the use of string variables as well as dictionaries of the API payloads. We also use a make_user factory fixture to generate test users in the isolated session for each test run.

## 6. Considered but out of scope (and why)
For this test example we are leaving out the following testing focuses as it is out of scope for this demo.
- Database persistence: We are testing using fresh databases so do not test the persistence of data in a real database
- UI testing - The SUT is solely an API-driven application with no UI so end to end testing would not be required for this application.

## 7. Future layers (roadmap)
- Mutation testing (mutmut). Mutation testing will ensure that the test suite will actually catch bugs if they occur by introducing small bugs into the code and verifying the tests fail. This is ideal for running on our unit tests to make sure they carry their weight.
- Schemathesis - This tool tests the API contract off of the OpenAPI schema. While the http tests catch what I explicitly write, the tool catches the edge cases that aren't covered and catches contract drift. 
- k6 - Performance testing. This tool simulates a customizable load on the API endpoints to ensure functionality under load.
- CI/CD pipeline. Set up the CI/CD pipeline with the above tests as gates to be deployed with GitHub Actions.


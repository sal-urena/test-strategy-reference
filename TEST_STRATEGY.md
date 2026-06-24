# Test Strategy — Reference API SUT

<!-- Guidance prompts are in HTML comments so they won't render on GitHub if you miss one.
     Delete each comment as you replace it with your own prose. -->

## 1. Purpose & scope

<!-- One paragraph: this repo is a SUT; the suite + this doc are the deliverable.
     State what "done" means, and what this doc is NOT (not a test catalog). -->

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

<!-- Intro paragraph (your prose): this layer drives the real routes over httpx with the DB
     overridden — real request in, real response out. Contrast with 3.1: a unit test isolates a
     pure function; an API test exercises the whole stack (HTTPBearer → handler → DB session).
     State the current count if you want it (17 green at time of writing). -->

#### What this layer covers — and why each is an API concern, not a unit one

<!-- For each bullet: one line on the behavior, one line on why it CAN'T live in the unit layer
     (needs the HTTP stack and/or a real DB session — there's no pure function to call). -->

- **Owner-scoped 404** — another user's item returns 404, not 403 (existence-denial / no id-enumeration oracle).
  <!-- Why API: owner-scoping is a property of the route + DB lookup, not a pure function. -->
- **Uniform 401, distinguished by layer not status** — missing/wrong-scheme header → 401 `"Not authenticated"`
  (rejected by `HTTPBearer` before any handler); present-but-bad/expired token → 401 `"Invalid or expired token"`
  (inside `get_current_user`).
  <!-- Why API: the distinction only exists once requests pass through the two guard layers.
       NOTE the real-framework finding: this FastAPI version returns 401 (not the old 403) on a
       missing header — distinction moved from status code to detail + layer. -->
- **Forged `owner_id` is ignored** — server stamps `owner_id` from the token; an `owner_id` in the body has no effect.
  <!-- Why API: only observable end-to-end (POST a forged body, assert the returned owner == the actor). -->
- **Login uniformity** — bad username and bad password are indistinguishable across body AND status (no enumeration oracle).
  <!-- Why API: it's an assertion about two real HTTP responses being identical. -->

#### The isolation rig — three decisions (the architecturally interesting part)

**The trap this whole rig exists to avoid:** `app/database.py` creates a module-level `engine` bound to the
**real `database.db`**, and every route depends on `get_session`, which yields against that engine. So any
test that hits a route writes to the committed DB and fails on rerun (e.g. `/register` → 400 "Username already
taken" the second time). Each decision below is a countermeasure.

1. **In-memory SQLite + `StaticPool`** (`session` fixture)
   <!-- Your prose: a fresh per-test in-memory engine means every test starts from a known-empty DB. -->
   - Why `StaticPool` *specifically*: plain `sqlite://` hands each connection its own separate in-memory DB,
     so the tables the fixture creates are invisible to the connection the request runs on.
   - **Failure-if-you-don't:** confusing "empty DB" failures — tables exist in the fixture, gone in the request.

2. **`app.dependency_overrides[get_session]`** (`client` fixture)
   <!-- Your prose: the override is a closure that yields the test session; FastAPI swaps it in for the real
        get_session for the duration of the test. -->
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

<!-- Your prose: why this is a *factory* fixture (returns an inner async fn) and not a plain fixture. -->

- Composes to **N users** — `alice = await make_user(...)`, `bob = await make_user(...)` — which is what the
  two-user owner-scope tests require.
- Returns an identity-rich `AuthedUser(id, headers)` so a test can assert the returned owner == the actor.
- Registers + logs in through the **real `/register` + `/login` endpoints** (not a hand-minted token) — so the
  fixture exercises the genuine auth path; the header key must be `Authorization` (that's what `HTTPBearer` reads).
- Asserts `200` on both legs inside the helper: a setup failure surfaces as a pytest *error*, not a *failure* —
  the correct signal that the test never reached the behavior under test.

## 4. Where a bug lands (unit vs API) — worked examples

<!-- The section that proves you understand boundaries, not just that you can write tests.
     2–3 concrete bugs, each routed to its layer:
       - token-expiry logic breaks → unit
       - broken owner-scope → API
       - (pick a third) -->

## 5. Test data & isolation

<!-- Keep this section at the GUARANTEE altitude. The mechanism (StaticPool, per-test engine,
     dependency_overrides) lives in §3.2 — reference it here, don't re-explain it. -->

#### The isolation guarantee

<!-- Your prose: every test starts from a known DB state — a fresh, empty in-memory DB per test,
     torn down after. State it as a guarantee the reader can rely on, then point at §3.2 for HOW
     it's enforced (the StaticPool + override rig). One or two sentences, no plumbing here. -->

#### Why fixtures live at the API layer, not the unit layer

<!-- Your prose: the unit layer is pure functions — no HTTP, no DB, so nothing to isolate and no
     fixtures (3.1 already says this). Isolation only becomes a problem once a test touches the
     module-level engine, which is the API layer. So the fixtures exist exactly where the shared
     mutable state is, and nowhere else. -->

#### Test data approach

<!-- Your prose: how test data is shaped at each layer.
       - Unit layer: plain values / string constants passed straight to the function.
       - API layer: JSON payload dicts posted to the endpoints (e.g. the register/login body),
         and identities built through the make_user factory rather than seeded into the DB by hand.
     Note WHY you build users via the real endpoints instead of inserting rows: the data arrives
     through the same auth path the SUT actually uses (no divergence between test setup and reality). -->

## 6. Considered but out of scope (and why)

<!-- The senior move. Map the rest of the pyramid and mark each:
       - DB/persistence-layer tests → covered transitively by the API layer; testing the framework
       - E2E / UI → no UI; the API layer IS the end-to-end here
       - full CI wiring → how you'd gate it, not built yet
     Knowing what to leave out — and saying so — is the point. -->

## 7. Future layers (roadmap)

<!-- Brief, ranked, one line each:
       - mutation testing (mutmut) — top differentiator: "coverage shows what ran,
         mutation shows whether assertions mean anything"
       - Schemathesis — contract/property testing off /openapi.json
       - Bandit — static security scan; will flag the planted hardcoded SECRET_KEY
       - k6 — performance, Phase 2 -->

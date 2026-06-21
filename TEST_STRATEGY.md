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

### 3.2 API layer (`tests/api/`) — planned

<!-- What it WILL cover and why these are API, not unit, concerns:
     owner-scoping (404), 401, forged owner_id, login uniformity.
     Infra decisions and their rationale:
       - in-memory SQLite + StaticPool — why StaticPool is required
       - dependency_overrides on get_session — why (module-level engine hits the real DB)
       - async httpx.AsyncClient + ASGITransport — "async client, sync app, sync DB" -->

## 4. Where a bug lands (unit vs API) — worked examples

<!-- The section that proves you understand boundaries, not just that you can write tests.
     2–3 concrete bugs, each routed to its layer:
       - token-expiry logic breaks → unit
       - broken owner-scope → API
       - (pick a third) -->

## 5. Test data & isolation

<!-- Your data approach (str constant now, payload dicts at the API layer) and the
     isolation guarantee: every test starts from a known DB state. Why fixtures
     belong at the API layer and not the unit layer. -->

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

# SQLviz — Security & Roles
**Version:** v0.1.0 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-08
**Prerequisites:** DOC 2 (Modes & CLI, Sections 5-6), DOC 3 (Technical Stack, Section 3)

---

## 1. Purpose of This Document

DOC 2 already established the high-level design: admin logs in
with a password, viewers access via hashed links without
logging in, and Quack handles concurrency. This document goes
one level deeper — the exact data model, the exact request
flows, and the exact failure modes for every security-relevant
operation in SQLviz V0.1.

```
DOC 2, Section 5-6  →  WHAT exists (admin login, share links)
DOC 7 (this doc)    →  HOW it works precisely (hashing algorithm,
                        token format, session lifetime, what
                        happens when a password is wrong,
                        what happens when a link is revoked
                        mid-session, etc.)
```

V0.1 has exactly two roles. No more, no fewer:

```
Admin    one per project, full read/write, set at project creation
Viewer   zero or more, read-only, no account, access via link only
```

There is no multi-admin, no per-dashboard permissions, no
"editor" role in V0.1. Anything beyond admin/viewer is
explicitly deferred (Section 7).

---

## 2. Threat Model — What V0.1 Defends Against, And What It Does Not

Being honest about scope prevents both under- and
over-engineering.

```
V0.1 DOES defend against:
✓ A stranger on the local network guessing a dashboard URL
  (mitigated by unguessable hashed tokens, Section 4)
✓ A viewer with a link editing the dashboard
  (mitigated by Quack read-only connections, Section 6)
✓ Someone finding the .sqlviz file and reading the admin
  password in plaintext
  (mitigated by bcrypt hashing, Section 3)
✓ A revoked share link continuing to work
  (mitigated by session secret rotation, Section 5)

V0.1 does NOT defend against, by design (revisit in V0.2+ if
real usage demands it):
✗ A malicious admin (the admin is trusted by definition —
  there is only one, and they created the project)
✗ Network-level attacks (no TLS in V0.1 — SQLviz binds to
  localhost/LAN, not the public internet, by default; see
  DOC 2 Section 1 "Cloud Mode" for when this changes)
✗ Brute-force password guessing at scale (no rate limiting
  on login in V0.1 — acceptable because this is a local tool,
  not a public multi-tenant service; revisit before any
  public-mode deployment)
✗ SQL injection via $variable filters — NOT a concern in the
  traditional sense, because the user IS the one writing the
  SQL (SQLviz is a tool for the SQL author, not a public form
  that takes untrusted SQL from end users). Viewer-supplied
  filter VALUES are still parameterized, never string-
  concatenated into SQL — see Section 6.3.
```

---

## 3. Admin Authentication

### 3.1 Password Storage

```
Algorithm:  bcrypt (via the `bcrypt` Python package — already
            a transitive dependency of common web stacks,
            pure-C extension, no extra service required,
            satisfies DOC 3 Section 9 dependency philosophy)
Cost factor: 12 (bcrypt default, ~250ms per hash on commodity
            hardware in 2026 — deliberately slow to resist
            brute force, fast enough not to annoy the one
            admin logging in)
Storage:    _sqlviz_auth.password_hash (DOC 2, Section 4 schema)
Never:      plaintext password is never written to disk, never
            logged, never included in any error message
```

```python
# sqlviz-storage/src/sqlviz_storage/auth.py

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Hash a password for storage. Called once, at project
    creation or password change.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a login attempt against the stored hash.
    Constant-time comparison is handled internally by bcrypt.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed hash (corrupted .sqlviz, manual tampering) —
        # fail closed, never raise a confusing error to the user
        return False
```

### 3.2 Login Flow

```
1. Admin opens http://localhost:4000
2. sqlviz-web shows the login screen (no dashboard content
   is ever sent to the browser before authentication —
   the API returns 401 for any dashboard/panel endpoint
   without a valid session)
3. Admin submits password via POST /api/v1/auth/login
4. sqlviz-api calls verify_password() against _sqlviz_auth
5. On success: issue a session token (Section 3.3), set as
   an HttpOnly cookie
6. On failure: generic "Invalid password" — never reveal
   whether the project even has a password set, never reveal
   timing differences beyond what bcrypt's constant-time
   comparison already guarantees
```

### 3.3 Session Tokens

```
Format:     opaque random token (32 bytes, base64url-encoded),
            NOT a JWT — V0.1 has no need for self-contained
            claims; a JWT would be over-engineering here
            (DOC 3 Section 9, dependency philosophy: "is it
            necessary?")
Storage:    in-memory dict on the FastAPI process,
            {token: {created_at, last_seen_at}}
            — NOT persisted to .sqlviz. Restarting `sqlviz`
            invalidates all admin sessions, which is the
            correct and expected behavior for a local tool.
Lifetime:   24 hours of inactivity, sliding window
            (last_seen_at updated on every authenticated
            request; session dict entry deleted after 24h
            with no requests)
Transport:  HttpOnly, SameSite=Strict cookie. Never exposed
            to JavaScript (mitigates XSS token theft). Not
            marked Secure in V0.1 because SQLviz runs over
            plain HTTP on localhost/LAN by default (see
            Section 2 threat model) — revisit when Cloud
            Mode (DOC 2, Section 1, V0.4) introduces TLS.
```

```python
# sqlviz-api/src/sqlviz_api/routers/auth.py

import secrets
import time
from fastapi import APIRouter, Response, HTTPException, Request
from sqlviz_storage.auth import verify_password

router = APIRouter()

# In-memory session store — see Section 3.3 rationale
_sessions: dict[str, dict] = {}

SESSION_LIFETIME_SECONDS = 24 * 60 * 60  # 24 hours


@router.post("/api/v1/auth/login")
async def login(request: Request, response: Response, password: str):
    stored_hash = get_stored_password_hash()  # reads _sqlviz_auth

    if not verify_password(password, stored_hash):
        # Deliberately generic — see Section 3.2
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_urlsafe(32)
    now = time.time()
    _sessions[token] = {"created_at": now, "last_seen_at": now}

    response.set_cookie(
        key="sqlviz_session",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=SESSION_LIFETIME_SECONDS,
    )
    return {"status": "ok"}


def require_admin(request: Request) -> None:
    """
    Dependency injected into every admin-only route.
    Raises 401 if the session is missing, unknown, or expired.
    """
    token = request.cookies.get("sqlviz_session")
    session = _sessions.get(token) if token else None

    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    now = time.time()
    if now - session["last_seen_at"] > SESSION_LIFETIME_SECONDS:
        del _sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")

    session["last_seen_at"] = now  # sliding window


@router.post("/api/v1/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("sqlviz_session")
    if token in _sessions:
        del _sessions[token]
    response.delete_cookie("sqlviz_session")
    return {"status": "ok"}
```

### 3.4 Password Change

```
Endpoint:   POST /api/v1/auth/change-password
Requires:   require_admin (must already be logged in)
            AND current password must be re-verified
            (not just "trust the existing session" — this
            protects against a session left open on a
            shared machine being used to lock out the
            real admin)
Effect:     1. Verify current password against stored hash
            2. Hash and store the new password
            3. Invalidate ALL existing sessions (force
               re-login everywhere — including the session
               that just made the change, which must log
               in again with the new password)
```

---

## 4. Share Links

### 4.1 Token Generation

```
Algorithm:  SHA256(dashboard_id + ":" + session_secret),
            truncated to 24 hex characters (96 bits — far
            beyond brute-force range for a local-network
            tool, per DOC 2 Section 6.5)
session_secret:  a separate, longer-lived secret from the
            session tokens in Section 3.3. Stored in
            _sqlviz_auth.session_secret (DOC 2, Section 4
            schema — already defined there). Generated once
            at project creation, rotated only on explicit
            "revoke all shares" action.

Why a separate secret from admin sessions:
            Admin login sessions (Section 3.3) are short-lived
            and in-memory — they disappear on restart by
            design. Share tokens must survive restarts (a
            link sent last week must still work today), so
            they are derived from a persisted secret instead.
```

> **Correction (fourth review round):** the original design below
> computed `token = SHA256(dashboard_id + secret)` — fully
> deterministic from only those two inputs. That meant (a) a given
> dashboard could only ever have ONE possible token value, so
> "create a second share link for the same dashboard" was
> impossible, and (b) `verify_share_token()` never actually
> consulted the `shares` table — it recomputed the expected value
> and compared, which made the per-row `revoked` flag (Section 4.4)
> meaningless for an individual share, since any non-revoked
> request would still recompute the *same* token regardless of
> which row it matched. The fix adds a random `share_nonce` per
> share row, making each share's token independently unguessable
> and independently revocable, while keeping the original "derive
> from a persisted secret, not an in-memory one" property that
> made tokens survive restarts.

```python
# sqlviz-storage/src/sqlviz_storage/sharing.py

import hashlib
import secrets


def generate_session_secret() -> str:
    """
    Called once, at project creation. Stored in _sqlviz_auth.
    Used as a "master" secret for the regenerate-all-shares
    revocation path (Section 4.4) — NOT used directly to compute
    individual tokens anymore (see share_nonce below).
    """
    return secrets.token_urlsafe(32)


def generate_share_nonce() -> str:
    """
    Called once per share, at share-creation time (Section 4.2).
    Stored in shares.nonce. This — not the dashboard_id — is what
    makes each share's token unique and independently revocable.
    """
    return secrets.token_urlsafe(16)


def generate_share_token(
    dashboard_id: str,
    share_nonce: str,
    session_secret: str
) -> str:
    """
    The token is now a function of THREE inputs: which dashboard,
    which specific share (nonce), and the project-wide secret
    (so "regenerate secret" — Section 4.4 — still invalidates
    every share at once, by changing an input every token depends on).
    """
    payload = f"{dashboard_id}:{share_nonce}:{session_secret}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def verify_share_token(token: str, share_row: dict, session_secret: str) -> bool:
    """
    Verification now ALWAYS starts from a real row looked up by
    token in the `shares` table (sqlviz-api does this lookup
    before calling this function) — never by recomputing from
    just dashboard_id. This function exists to confirm the looked-up
    row's stored data is still consistent with the current secret
    (i.e. the secret hasn't been regenerated since this row's
    token was issued) and that the row isn't revoked.
    """
    if share_row.get("revoked"):
        return False
    expected = generate_share_token(
        share_row["dashboard_id"],
        share_row["nonce"],
        session_secret
    )
    return secrets.compare_digest(token, expected)
```

### 4.2 The Three Sharing Modes — Exact Request Flows

Per DOC 2, Section 6, there are three modes. This section
defines the exact data stored and the exact verification flow
for each, closing the gap DOC 2 left at a conceptual level.

```sql
-- shares table, already defined in DOC 2 Section 4 — extended
-- here with the `nonce` column required by the fix above:

CREATE TABLE shares (
    id            VARCHAR PRIMARY KEY,
    dashboard_id  VARCHAR NOT NULL,
    nonce         VARCHAR NOT NULL,   -- from generate_share_nonce(),
                                      -- NEW column (fourth review fix)
    token         VARCHAR NOT NULL,   -- from generate_share_token(),
                                      -- stored so lookups are by
                                      -- token, never recomputed blind
    mode          VARCHAR NOT NULL,   -- 'private' | 'password' | 'public'
    password_hash VARCHAR,            -- bcrypt hash, ONLY for mode='password'
    created_at    VARCHAR NOT NULL,
    revoked       BOOLEAN DEFAULT false
);
```

```
The lookup flow at the API layer (every mode):
    GET /view/{token}
        → SELECT * FROM shares WHERE token = ?
        → if no row found: HTTP 404 (Section 4.2 anti-enumeration
          principle, unchanged)
        → if row found: call verify_share_token(token, row, secret)
          to confirm it's not revoked and the secret hasn't rotated
        → only then branch by row.mode
```

**Private mode:**
```
Creation:   POST /api/v1/dashboards/{id}/share {"mode": "private"}
            → generates nonce, derives token from
              (dashboard_id, nonce, session_secret),
              inserts row with password_hash=NULL
Access:     GET /view/{token}
            → look up by token (see lookup flow above),
              verify_share_token() ✓ AND mode == 'private'
            → return dashboard data directly, no further prompt
Failure:    invalid/revoked token → HTTP 404 (not 403 — never
            confirm or deny that a token "almost" matched
            something; a generic 404 leaks no information)
```

**Password mode:**
```
Creation:   POST /api/v1/dashboards/{id}/share
            {"mode": "password", "password": "..."}
            → generates nonce, derives token, hashes the
              share-specific password with bcrypt (Section 3.1
              algorithm, reused — same function, different
              stored value), inserts row with that password_hash
Access:     Step 1 — GET /view/{token}
              → look up by token, verify_share_token() ✓
                AND mode == 'password'
              → if all true, return ONLY a "password required"
                page — NOT the dashboard data
            Step 2 — POST /view/{token}/unlock {"password": "..."}
              → verify_password() against this share's
                password_hash (NOT the admin password —
                these are independent secrets)
              → on success, issue a short-lived viewer token
                (Section 4.3) and return dashboard data
              → on failure, generic "Invalid password",
                same anti-enumeration principle as Section 3.2
```

**Public mode:**
```
Creation:   POST /api/v1/dashboards/{id}/share {"mode": "public"}
            → identical to private mode generation, only the
              mode column differs
Access:     identical flow to private mode — the ONLY

            difference between private and public in V0.1 is
            intent/documentation, not mechanism. Both produce
            an unguessable token requiring no password.
            (DOC 2, Section 6 distinguishes them as "intended
            for LAN" vs "intended to be shared anywhere" — but
            since SQLviz V0.1 has no network-level access
            control beyond the token itself, the technical
            difference is currently zero. This is logged
            explicitly in Section 7 as a known gap, not hidden.)
```

### 4.3 Viewer Session (Password Mode Only)

Private and public mode viewers need no session — the URL
itself is the credential, checked on every request. Password
mode is the one case requiring a short-lived viewer token so
the password isn't re-prompted on every panel refresh.

```
Format:     same opaque token scheme as Section 3.3
Storage:    separate in-memory dict, _viewer_sessions,
            keyed by share token + viewer token
Lifetime:   2 hours of inactivity (shorter than admin's 24h —
            viewers are anonymous and the cost of re-entering
            a shared password is low; shorter exposure window
            if a viewer's browser is left open on a shared
            machine)
Scope:      a viewer token is valid ONLY for the specific
            share token it was issued against — it cannot be
            reused to access a different dashboard's
            password-protected share, even if somehow guessed
```

### 4.4 Revocation

```
Revoke ONE share:
    PATCH /api/v1/shares/{share_id} {"revoked": true}
    → sets shares.revoked = true
    → that specific token stops working immediately: the lookup
      flow (Section 4.2) finds the row by token, then
      verify_share_token() returns false because revoked=true
    → because each share now has its own nonce (Section 4.1
      fix), this row's token is structurally distinct from
      every other share's token — revoking it cannot accidentally
      affect any other share for the same or a different
      dashboard, which was NOT true before the nonce fix

Revoke ALL shares at once (DOC 2, Section 6.4):
    POST /api/v1/auth/regenerate-secret
    → requires require_admin
    → calls generate_session_secret() again, overwrites
      _sqlviz_auth.session_secret
    → every existing share row's token was derived from
      (dashboard_id, nonce, OLD secret) — verify_share_token()
      now recomputes using the NEW secret for any row it looks
      up, and that recomputed value no longer matches the
      `token` column stored on any existing row, so every
      previously issued link fails verification simultaneously
    → existing rows in `shares` are NOT deleted (kept for
      audit/history — DOC 2 already implies this), they
      simply become permanently unverifiable until/unless
      the admin re-shares the dashboard (creating new rows
      with new nonces and tokens derived from the new secret)
```

---

## 5. Quack Integration — Connecting Auth to Concurrency

DOC 3, Section 3 already established that Quack exposes DuckDB
as a PostgreSQL-compatible server, with admin getting read/write
and viewers getting read-only. This section specifies exactly
how the HTTP-layer auth above (Sections 3-4) maps to Quack-layer
DuckDB connections.

```
sqlviz-api never lets the browser talk to Quack directly.
The flow is always:

Browser → sqlviz-api (HTTP, cookie-authenticated per Section 3/4)
              ↓
        sqlviz-api holds ONE Quack admin (read/write) connection
        and a POOL of Quack viewer (read-only) connections
              ↓
        sqlviz-storage / sqlviz-inference execute against
        whichever connection sqlviz-api selected based on
        the HTTP request's authentication result
```

```python
# sqlviz-api/src/sqlviz_api/quack_server.py

class QuackConnectionRouter:
    """
    Decides which Quack connection a given HTTP request uses.
    This is the single chokepoint where "is this an admin or
    a viewer" (Sections 3-4) becomes "which DuckDB connection
    do they get" (DOC 3, Section 3).
    """

    def __init__(self, admin_conn, viewer_pool):
        self._admin_conn = admin_conn      # read/write
        self._viewer_pool = viewer_pool    # read-only pool

    def connection_for_request(self, request) -> "DuckDBConnection":
        # Admin-authenticated request (Section 3.3 cookie present
        # and valid) → the single read/write connection
        if is_admin_authenticated(request):
            return self._admin_conn

        # Viewer request (valid share token per Section 4.2,
        # checked BEFORE this router is ever reached — see
        # routers/shares.py) → any available read-only connection
        return self._viewer_pool.acquire()
```

```
Why a pool for viewers and a single connection for admin:
    There is only ever one admin (V0.1 has exactly one admin
    role per project, Section 1). There can be many concurrent
    viewers (multiple people opening the same share link).
    Quack's read-only connections are cheap and stateless —
    pooling them is straightforward and exactly what DOC 3
    Section 3 promised ("unlimited simultaneous viewers,
    zero conflicts").
```

---

## 6. Filter Value Safety

### 6.1 The $variable Substitution Boundary

DOC 5, Section 10 already defines how `$variable` placeholders
are detected and matched to UI controls. This section defines
the security boundary at execution time — the one place in
SQLviz where a value chosen by someone who is NOT the SQL
author (a viewer adjusting a filter) flows into a query.

```
The author of the SQL is always the admin (Section 1 — V0.1
has one role that can write SQL). The viewer can only choose
VALUES for placeholders the admin already declared. This is
fundamentally different from a public form taking arbitrary
SQL from an untrusted user — the SQL shape is fixed by a
trusted party; only leaf values vary.
```

### 6.2 Parameterization, Never String Interpolation

```python
# WRONG — never do this, even though the "SQL author is trusted"
# argument above might tempt a shortcut:
sql = panel.sql_content.replace("$region", f"'{viewer_value}'")

# CORRECT — DuckDB prepared statement parameter binding:
conn.execute(
    panel.sql_content.replace("$region", "?"),
    [viewer_value]
)
```

```
Why this matters even though the SQL author is trusted:
    A viewer's filter VALUE is still untrusted input. If
    interpolated as a string, a viewer could submit a value
    like `'; DROP TABLE sales; --` as their "region" filter
    selection and break out of the intended value position.
    Parameter binding makes this structurally impossible
    regardless of trust level — it is the correct default,
    not a defense against a specific attacker.
```

### 6.3 Range and Multi-Value Filters

```
FilterEngine (DOC 5, Section 10.4) already merges $desde/$hasta
into a single date_range_picker and similar for numeric ranges.
Each resulting bound value is still bound as a separate
parameter — a range filter is never built by concatenating
two values into one SQL fragment.

MultiSelect filters (ANY($variable) per DOC 5 Section 10.3) bind
the entire list as a single array parameter — DuckDB's Python
API supports list parameters natively for ANY(?) clauses; no
manual "IN (1,2,3)" string building is ever performed.
```

---

## 7. Known Gaps — Explicitly Logged, Not Hidden

Following the same discipline established in DOC 5 (Sections 16.3
and 16.4) and DOC 8 (Section 6): every limitation identified while
writing this document is recorded here with its resolution
version, rather than silently left as an undocumented assumption.

```
Gap                              Why it exists in V0.1       Resolves
─────────────────────────────────────────────────────────────────
Private vs Public mode are        No network-level access      V0.2
mechanically identical            control exists yet beyond
(Section 4.2)                     the token. A true distinction
                                  would require, e.g., binding
                                  private-mode shares to LAN-only
                                  origins/IP ranges. Logged here
                                  so this is fixed deliberately,
                                  not "discovered" as a surprise
                                  bug later.

No TLS by default                 SQLviz V0.1 targets local/LAN  V0.4
(Section 3.3)                     use (DOC 2, Section 1). TLS
                                  becomes mandatory the moment
                                  Cloud Mode exists — tracked
                                  there, not solved here.

No login rate limiting            Single local admin, not a      V0.2 if
(Section 2)                       public multi-tenant service.   needed
                                  Acceptable for V0.1's threat
                                  model (Section 2). Add
                                  exponential backoff per-IP
                                  if/when Cloud Mode or any
                                  public-facing deployment
                                  pattern becomes common.

Only two roles                    Sufficient for V0.1's single-  V0.3+
(admin/viewer), no per-           admin-per-project model
dashboard permissions             (Section 1). Multi-admin or
                                  per-dashboard ACLs are a
                                  meaningfully different product
                                  shape and should not be
                                  retrofitted speculatively.

Session store is in-memory,       Acceptable because a single    not
not distributed                   `sqlviz` process serves one     planned
                                  project (DOC 2 design). Would    (by
                                  only matter for a clustered      design)
                                  deployment, which is out of
                                  scope for the entire V0.x line
                                  per DOC 1's "sustainable by one
                                  person" principle (Principle 5).
```

---

## 8. Definition of Done — Security & Roles (feeds DOC 8, Phase 4)

```
[ ] Admin password is hashed with bcrypt, never stored plaintext
[ ] Wrong password returns a generic error, no information leak
[ ] Admin session cookie is HttpOnly + SameSite=Strict
[ ] Sessions expire after 24h of inactivity (sliding window)
[ ] Password change invalidates all existing sessions
[ ] Each share has its own random nonce (Section 4.1); two shares
    for the SAME dashboard produce two DIFFERENT, independently
    valid tokens — this must be tested explicitly, since the
    pre-fix design (token = f(dashboard_id, secret) only) could
    not do this
[ ] Share token lookup is ALWAYS by querying the `shares` table
    for the token first (Section 4.2 lookup flow), never by
    blindly recomputing from a dashboard_id and comparing
[ ] All three sharing modes (private/password/public) follow
    the exact flows in Section 4.2
[ ] Revoking one share does not affect any other share, even
    other shares of the SAME dashboard (Section 4.4 — this is
    the specific guarantee the nonce fix exists to provide)
[ ] Regenerating the session secret invalidates ALL existing
    share links simultaneously (Section 4.4)
[ ] Admin gets exactly one Quack read/write connection; viewers
    share a read-only pool; browser never talks to Quack directly
[ ] All $variable filter values are parameter-bound, never
    string-interpolated into SQL — including range and
    multi-select filters
[ ] Section 7's gap list is reviewed and still accurate before
    V0.1 ships (no gap silently resolved or silently expanded
    without updating this table)
```

### 8.1 Fourth Review Round — Log

A fourth external review (covering all 8 documents together,
after the third round's cross-document pass) found one design
bug in this document: the original `generate_share_token()`
(Section 4.1) derived a token from only `dashboard_id` and the
project-wide `session_secret`. Since both inputs are fixed once
a dashboard exists, this made the token for a given dashboard
fully deterministic — there was structurally only one possible
token value per dashboard, which silently broke two things this
document claimed worked: creating a second independent share
link for the same dashboard, and revoking one share without
affecting others sharing the same `dashboard_id`. The fix adds a
random `nonce` per share row (Section 4.1) and changes
verification to always look up by token first rather than
recomputing blind (Section 4.2). This is now reflected in
Sections 4.1, 4.2, and 4.4 above, and in the checklist items
added to this section.

---

*SQLviz Security & Roles — v0.1.0 Draft*
*"Two roles. One admin. Zero plaintext secrets."*

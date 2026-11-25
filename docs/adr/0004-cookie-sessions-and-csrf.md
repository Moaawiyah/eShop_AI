# ADR-0004: Cookie-Based Sessions with CSRF Protection

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

The web frontend is the only client. Authentication must resist token
theft through XSS, support immediate revocation, session rotation and
idle and absolute timeouts, and work with Next.js server rendering.

## Decision

Use **server-side sessions identified by a cookie**, with CSRF protection
for every state-changing request.

- Cookie: `HttpOnly`, `Secure` outside local HTTP development,
  `SameSite=Lax` or stricter, `__Host-` prefix in TLS environments; only
  an opaque random identifier is stored in the cookie.
- Session state is stored server-side; the store (Redis or PostgreSQL)
  is decided by UD-08 before authentication work.
- Session ID rotation on sign-in and privilege change; configurable idle
  and absolute timeouts, stricter for back-office roles.
- CSRF: synchronizer token bound to the session (or signed double-submit),
  sent in the `X-CSRF-Token` header, plus `Origin` verification.
- Same-origin `/api/v1` routing avoids cross-site cookies (ARCHITECTURE
  section 6.5).
- Passwords are hashed with Argon2id (12–128 characters).

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| JWT access tokens in browser storage | Exposed to XSS; revocation is hard |
| JWT in cookies (stateless) | Still needs CSRF protection; revocation needs a deny-list, i.e. server state |
| External identity provider | Extra cost and dependency; unnecessary for synthetic demo users |

## Consequences

**Positive**

- Tokens are never readable by JavaScript.
- Immediate revocation and session listing are straightforward.
- Fits server-rendered pages.

**Negative**

- Requires CSRF handling in the frontend client and backend middleware.
- Server-side state must be available for authenticated requests.
- Non-browser clients (if ever added) need a separate mechanism.

## Related Requirements and Tasks

- Requirements: FR-AUTH-002 to FR-AUTH-007, NFR-SEC-001 to NFR-SEC-004, NFR-SEC-009
- Tasks: SHOP-030, SHOP-031, SHOP-032
- Documents: ARCHITECTURE sections 6.5, 8 and 12

## Reconsideration Conditions

Revisit only through a new ADR if a non-browser client (mobile app or
third-party API consumer) becomes in scope, or if the deployment model
prevents same-origin routing.

# Security Rules (always loaded)

Applies to all work. Root essentials are in CLAUDE.md section 11; this file
adds detail. PRD reference: section 13 (NFR-SEC).

## Authentication and Sessions
- Hash passwords with Argon2id using recommended parameters.
- Passwords: 12–128 characters, no composition rules; reject common passwords.
- Use server-side, cookie-based sessions: `HttpOnly`, `Secure` (outside local
  HTTP development), `SameSite=Lax` or stricter.
- Rotate the session ID on sign-in and privilege change; enforce idle and
  absolute timeouts, stricter for back-office roles.
- Protect every state-changing request with CSRF tokens (synchronizer or
  signed double-submit) plus `Origin` verification.
- Rate limit sign-in, registration, search and AI endpoints.
- Never reveal whether an account exists.
- Revisit token-based authentication only through an ADR.

## Authorization
- Enforce authorization on the server for every endpoint, including
  object-level checks (customers access only their own data).
- Never rely on the frontend, an LLM or an MCP client for authorization.

## Input, Output and Data Handling
- Validate all untrusted input with Pydantic schemas.
- Use SQLAlchemy parameterized queries; never build SQL from strings.
- Output-encode user-generated and imported content; never render raw HTML.
- Limit upload size and type; parse files safely.
- Neutralize spreadsheet formula injection in CSV exports.
- Protect outbound requests against SSRF (host allow-lists, block private
  address ranges).
- Customer-facing inventory data exposes availability categories only.

## Errors and Logging
- Never expose stack traces or internal details; return a correlation ID.
- Never log passwords, tokens, session IDs, API keys or full personal data.
- Log security events (sign-in failures, role changes, AI tool denials).

## Secrets
- Never commit credentials. Local secrets live in `.env` (ignored);
  `.env.example` contains placeholders only.
- Cloud secrets use a managed secrets service.
- Never place secrets in images, Helm values, Terraform files, CI logs,
  notifications or LLM prompts.

## Dependencies and Supply Chain
- Commit lockfiles (`uv.lock`, `package-lock.json`).
- Justify every new dependency (purpose, maintenance, license, alternatives).
- Scanning: Gitleaks, Dependabot, pip-audit and npm audit from M1;
  Trivy image and IaC scanning from M7.

## Security Review Checklist (every change)
- Untrusted input validated? Authorization enforced server-side?
- Secrets or personal data exposed in code, logs or responses?
- New dependency, network call or permission justified?
- AI or MCP changes reviewed against `.claude/rules/ai-mcp.md`?

# eShop_AI — Security

| Field | Value |
|---|---|
| Document | Security baseline and threat model |
| Version | 0.1 — Draft |
| Status | Draft, pending project owner approval |
| Jira | SHOP-004 |
| Milestone | M0 — Project Initialization |
| Last updated | 2026-11-25 |
| Related | [PRD](PRD.md) section 13 · [Architecture](ARCHITECTURE.md) section 12 · [ADR-0004](adr/0004-cookie-sessions-and-csrf.md) · [`.claude/rules/security.md`](../.claude/rules/security.md) |

> **Implementation status:** no application code exists yet. Every
> application control below is **Planned** and lists the task that
> implements it. Only the repository controls in section 2 are
> **Implemented**.

Normative rules live in `CLAUDE.md` section 11 and
`.claude/rules/security.md`; requirements live in PRD section 13
(NFR-SEC). This document explains how those rules are applied, the
threat model, and the operational procedures.

## Status Legend

| Status | Meaning |
|---|---|
| **Implemented** | In place and verifiable in the repository today |
| **Planned** | Approved design; implemented in the listed task or milestone |
| **Deferred** | Depends on an unresolved decision (UD-nn) |

## 1. Security Objectives

| ID | Objective | Measure |
|---|---|---|
| SO-1 | No real payment or personal data is ever processed | Simulated payments only (FR-PAY-003); synthetic data (NFR-PRIV-001) |
| SO-2 | Customers can access only their own data | Server-side, object-level authorization on every endpoint (NFR-SEC-005) |
| SO-3 | Credentials and secrets never leave their managed store | No secrets in Git, images, logs or prompts (NFR-SEC-013, NFR-SEC-014) |
| SO-4 | AI features cannot be used to escalate privileges or leak data | Read-only, authorized tools; no personal data to LLMs (NFR-AI-002, NFR-AI-003) |
| SO-5 | Known-vulnerable dependencies and images are detected before release | Automated scanning from M1, blocking thresholds from M7 |
| SO-6 | Security incidents are detectable, traceable and recoverable | Audit events, correlation IDs, alerts, tested restores |
| SO-7 | No cloud cost or exposure without explicit approval | `CLAUDE.md` section 12; [ADR-0006](adr/0006-local-first-incremental-cloud.md) |

## 2. Implemented Controls (M0)

| Control | Evidence |
|---|---|
| Secret files ignored by Git (`.env`, `.env.*` except `.env.example`, keys, Terraform state and variables, cloud configuration) | `.gitignore`; `git check-ignore -v .env` |
| `.env.example` contains placeholders only | `.env.example` |
| Human approval required for commits, pushes, cloud access, paid APIs and destructive operations | `CLAUDE.md` section 12 |
| Security rules always loaded for AI-assisted work | `.claude/rules/security.md` (no `paths:` filter) |
| Documentation consistency checks, read-only | `scripts/validate_docs.py` |
| Claude Code permission rules: secret files denied for reading; force pushes, `terraform apply`/`destroy`, cloud CLIs and `sudo` denied; dependency installs, Git history changes, GitHub and Jira writes and database tools require approval; bypass mode disabled; auto-approved `python3` commands are exact validation commands only (SHOP-007) | `.claude/settings.json` |
| Deterministic PreToolUse hooks covering forms the rules cannot express (`git -C . push -f`, `sh -c`, heredocs and stdin fed to shells, wrapper options, `$(...)`, credential-shaped content, deletions outside the project); any command naming a secret file is denied unless it only handles the name (Git commands that print content are checked too, and `git diff`/`git grep` on files outside the repository require approval), with case-insensitive matching and symlinks resolved. Defense in depth, not a sandbox: secrets opened by a program's own code (`python3 -c "open('.env')"`), variables or globs expanded at run time, aliases and scripts run from files are not inspected (SHOP-007) | `.claude/hooks/`; `scripts/tests/test_claude_hooks*.py`, `scripts/tests/test_claude_git_checks.py` |

## 3. Trust Boundaries and Attack Surface

Trust boundaries TB-1 to TB-7 are defined in
[ARCHITECTURE section 12.1](ARCHITECTURE.md#121-trust-boundaries).

| Attack surface | Exposed through | Main threats | Primary controls (section) |
|---|---|---|---|
| Authentication endpoints | `/api/v1/auth/*` | Credential stuffing, enumeration, session fixation | 5, 6, 9 |
| Customer APIs | `/api/v1/me`, cart, orders | IDOR, CSRF, price tampering | 6, 7, 8 |
| Back-office APIs and UI | `/api/v1/admin/*` | Privilege escalation, mass assignment | 7, 8 |
| Search and catalog | `/api/v1/products`, `/search` | Injection, scraping, expensive queries | 8, 9 |
| File imports | CSV and JSON upload | Oversized or malicious files, formula injection, stored XSS | 8 |
| External product sources | Integration adapters | SSRF, malicious responses, quota exhaustion | 10 |
| AI assistants | `/api/v1/assistant`, `/api/v1/ops` | Prompt injection, data exfiltration, cost abuse | 11, 12 |
| CI/CD | GitHub Actions | Secret leakage, poisoned dependencies or actions | 13, 14 |
| Containers and clusters | Images, Compose, kind | Vulnerable bases, root containers, exposed ports | 15 |
| Cloud account | AWS (deferred) | Over-privileged roles, public resources, cost abuse | 16 |

## 4. Threat Model

STRIDE summary per boundary; the condensed version is in
[ARCHITECTURE section 12.2](ARCHITECTURE.md#122-threat-model-summary-stride).

| ID | Threat | Boundary | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|---|---|
| T-01 | Credential stuffing or brute force on sign-in | TB-2 | High | Medium | Rate limits with back-off, Argon2id, uniform errors | Planned, SHOP-031, SHOP-033 |
| T-02 | Session hijacking via XSS | TB-1, TB-2 | Medium | High | `HttpOnly` cookies, CSP, output encoding | Planned, SHOP-019, SHOP-031 |
| T-03 | Cross-site request forgery | TB-2 | Medium | High | Synchronizer token plus `Origin` check | Planned, SHOP-032 |
| T-04 | Insecure direct object reference | TB-2 | Medium | High | `/me` endpoints, object-level checks, authorization sweep tests | Planned, SHOP-031, SHOP-040 |
| T-05 | Client-side price or total tampering | TB-2 | Medium | Medium | Server-side totals in cents (FR-CART-004) | Planned, SHOP-036, SHOP-037 |
| T-06 | Overselling through concurrent checkouts | TB-3 | Medium | Medium | Single-transaction stock decrement (FR-CHK-007) | Planned, SHOP-037 |
| T-07 | SQL injection | TB-3 | Low | High | SQLAlchemy parameterized queries only | Planned, SHOP-023 |
| T-08 | Stored XSS through imported product data or reviews | TB-1, TB-4 | Medium | High | Validation, output encoding, no raw HTML | Planned, SHOP-026, SHOP-055 |
| T-09 | SSRF through external source URLs or image fetching | TB-4 | Low | High | Host allow-list, private range blocking (NFR-SEC-017) | Planned, SHOP-053, SHOP-062 |
| T-10 | Direct or indirect prompt injection | TB-5 | High | Medium | Instruction/data separation, tool allow-list, output validation | Planned, SHOP-066 to SHOP-069 |
| T-11 | Personal data or secrets sent to an LLM | TB-5 | Medium | High | No personal data in prompts; redaction for DevOps AI | Planned, SHOP-065, M11 |
| T-12 | AI cost abuse | TB-5 | Medium | Medium | Gatekeeper budgets, per-session limits, mock default | Planned, SHOP-054 |
| T-13 | Secret committed to Git | Repository | Medium | High | `.gitignore`, Gitleaks in CI, review | Implemented (`.gitignore`); Planned, SHOP-018 |
| T-14 | Vulnerable or malicious dependency | CI | Medium | High | Lockfiles, Dependabot, pip-audit, npm audit, pinned actions | Planned, SHOP-018 |
| T-15 | Vulnerable container base image | TB-6 | Medium | Medium | Minimal pinned bases, Trivy | Planned, SHOP-075, SHOP-079 |
| T-16 | Over-privileged cloud credentials | TB-6 | Low | High | OIDC, least-privilege roles, no long-lived keys | Deferred, SHOP-094 |
| T-17 | Repudiation of back-office changes | TB-2 | Low | Medium | Append-only audit events | Planned, SHOP-041 |
| T-18 | Denial of service through expensive search or AI | TB-1 | Medium | Medium | Pagination caps, rate limits, timeouts | Planned, SHOP-033, SHOP-054 |

Likelihood and impact are qualitative and reviewed at each milestone exit.

## 5. Authentication and Passwords

**Status: Planned** (SHOP-031; [ADR-0004](adr/0004-cookie-sessions-and-csrf.md)).

| Control | Design |
|---|---|
| Hashing | Argon2id through a maintained library (selected in SHOP-031). Parameters no weaker than the OWASP minimum (memory 19 MiB, 2 iterations, parallelism 1); the RFC 9106 low-memory profile is preferred if sign-in stays under about 500 ms on the reference hardware. |
| Rehashing | Hashes record their parameters; a hash with outdated parameters is upgraded at the next successful sign-in. |
| Password length | 12 to 128 characters; no composition rules (NFR-SEC-002). |
| Common passwords | Rejected using a bundled list of common and breached passwords (offline; no external call). |
| Normalization | Passwords are accepted as Unicode and normalized (NFKC) before hashing; no silent truncation. |
| Account enumeration | Identical responses and timing for unknown accounts and wrong passwords (FR-AUTH-007). |
| Password change | Requires the current password and invalidates the user's other sessions (FR-AUTH-008). |
| Password reset (ADV) | Single-use, time-limited token, stored hashed, delivered only to the local mail catcher (FR-AUTH-009, UD-15, SHOP-057). |
| MFA (ADV) | TOTP for back-office roles (FR-AUTH-010, SHOP-047). |

## 6. Sessions and CSRF Protection

**Status: Planned** (SHOP-030, SHOP-031, SHOP-032). Session store is
**Deferred** (UD-08).

| Control | Design |
|---|---|
| Session identifier | At least 128 bits from a cryptographically secure generator; stored server-side only as a hash. |
| Cookie attributes | `HttpOnly`; `Secure` outside local HTTP development; `SameSite=Lax`; `Path=/`; `__Host-` prefix in TLS environments; no `Domain` attribute. |
| Rotation | New session ID on sign-in, sign-out and any privilege change (FR-AUTH-004). |
| Timeouts | Configurable idle and absolute timeouts (FR-AUTH-005). **Approved initial defaults (SHOP-006):** customers 30 minutes idle / 7 days maximum lifetime; back-office roles 15 minutes idle / 8 hours maximum lifetime. |
| Revocation | Sign-out deletes the server-side session; password change and account disabling revoke all sessions. Session listing and revocation by users is ADV (FR-AUTH-011, SHOP-048). |
| CSRF | Synchronizer token bound to the session, returned by `GET /api/v1/auth/csrf`, sent in the `X-CSRF-Token` header on every unsafe method, compared in constant time. The `Origin` header (or `Referer` when `Origin` is absent) must match an allowed origin. Failures return 403 and are logged as security events. |
| Same-origin API | The browser calls `/api/v1` on the frontend origin ([ARCHITECTURE section 6.5](ARCHITECTURE.md#65-api-client-and-same-origin-access)). CORS allows only configured origins (NFR-SEC-009). |

## 7. Authorization (RBAC)

**Status: Planned** (SHOP-040; fine-grained roles SHOP-049, ADV).

- Roles and the permission matrix are defined in PRD section 5. A user may
  hold several roles; permissions are the union.
- Every endpoint declares its required permission through a FastAPI
  dependency; there is no default-allow route.
- Object-level checks: customer endpoints resolve the owner from the
  session (`/me`), never from a client-supplied user ID; objects the caller
  may not see return 404.
- Role changes are audited and rotate the affected user's sessions.
- The frontend, an LLM or an MCP client never makes authorization
  decisions; the frontend only hides navigation.
- Authorization sweep tests call every endpoint with every role and
  assert the expected allow or deny result.

## 8. Input Validation, Injection and XSS

**Status: Planned** (SHOP-010 onwards).

| Area | Control |
|---|---|
| Request validation | Pydantic models for every request; unknown fields rejected; length, range and pattern limits; money as non-negative integer cents. |
| SQL injection | SQLAlchemy Core/ORM with bound parameters only; no SQL assembled from strings; dynamic sorting and filtering from allow-lists. |
| XSS | React output encoding; no `dangerouslySetInnerHTML` for user or imported content; Content-Security-Policy without `unsafe-inline` scripts where practical (NFR-SEC-008). |
| Mass assignment | Separate create, update and response schemas; server-controlled fields (prices in carts, roles, status) never accepted from clients. |
| File uploads | Maximum 10 MB by default; CSV and JSON only, checked by content; streamed parsing with row limits; files never executed or served back (NFR-SEC-011). |
| CSV exports | Cells beginning with `=`, `+`, `-`, `@`, tab or carriage return are prefixed to neutralize formula injection (NFR-SEC-012). |
| Error responses | RFC 9457 problem details without stack traces; correlation ID included (NFR-SEC-010). |
| Security headers | CSP, HSTS (TLS only), `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors` (SHOP-019). |

## 9. Rate Limiting and Gatekeeper

**Status: Planned** (inbound limits SHOP-033; consolidated Gatekeeper
SHOP-054). Gatekeeper is described in
[ARCHITECTURE section 5](ARCHITECTURE.md#5-platform-components).

| Responsibility | Detail |
|---|---|
| Inbound rate limits | Per client address and per account or session; returns 429 with `Retry-After`. |
| Outbound provider quotas | Checked before each external call and recorded after it. |
| AI token budgets | Per session and global daily budget (NFR-AI-015); exhaustion triggers the non-AI fallback. |
| Fallback decisions | Deny, degrade (keyword search instead of AI) or delay (job retry). |
| Observability | Metrics and security events for denials (FR-PLAT-005, ADV). |

**Approved initial defaults (SHOP-006).** Every limit is configurable (see
`.env.example`); implementation is planned for SHOP-033 and SHOP-054, not M0.
Authentication limits apply to both the account identifier and the client IP
address, so neither rotating accounts nor rotating addresses bypasses them.

| Endpoint | Limit |
|---|---|
| Sign-in | 5 requests per minute, counted separately per account identifier and per client IP address, with progressive back-off |
| Registration | 10 requests per hour per client IP address |
| Search | 60 requests per minute per client IP address |
| Assistant | 30 requests per session per hour (NFR-AI-014) |
| Real-provider AI tokens | Daily budget 0 by default: no real-provider token use until the owner explicitly configures a budget (NFR-AI-015, UD-06) |

Authentication limits fail closed if the rate-limit store is unavailable;
catalog limits fail open with an alert
([ARCHITECTURE section 12.5](ARCHITECTURE.md#125-failure-handling)).

## 10. External Integrations and the Internal SDK

**Status: Planned** (SHOP-053; [ADR-0003](adr/0003-internal-sdk-and-provider-abstraction.md)).

- All outbound calls go through `backend/app/integrations/` and the shared
  HTTP client with explicit timeouts and connection limits.
- **SSRF:** destination hosts come from a configured allow-list; resolved
  addresses in private, loopback, link-local and metadata ranges are
  blocked; redirects are re-validated; response sizes are limited.
- Responses are untrusted: validated with Pydantic, size-limited, and
  output-encoded when displayed.
- Provider credentials have the narrowest scope offered, are read from
  configuration or managed secrets, and are never logged.
- External data sources must be authorized (NFR-COST-007, UD-03); terms,
  rate limits and attribution are respected.
- CI never calls live providers; contract tests use recorded fixtures.

## 11. AI Prompt Injection Protection

**Status: Planned** (SHOP-065 to SHOP-069;
[ADR-0002](adr/0002-ai-inside-backend.md)). Rules:
`.claude/rules/ai-mcp.md`.

- System instructions are fixed on the server. User messages, product
  text, reviews, logs and tool results are passed as delimited data and
  never as instructions (NFR-AI-002).
- The model extracts structured intent; deterministic code filters, ranks
  and prices. Unknown product references are discarded; prices and
  availability come from the database (FR-AI-004, FR-AI-005).
- Every structured output is validated; invalid output is retried once,
  then rejected with a non-AI fallback (NFR-AI-001).
- Message length, tool calls, output tokens, history and timeouts are
  limited (PRD section 10.6).
- The assistant receives no personal data, credentials or session data
  (NFR-AI-003). Only metadata is logged (NFR-AI-004).
- A prompt-injection suite with direct and indirect cases runs in CI on
  the mock provider (NFR-AI-005, AC-043).

## 12. MCP Tool Authorization

**Status: Planned** (SHOP-066). Transport and external exposure are
**Deferred** (UD-10).

- Tools are read-only and listed in PRD section 10.3; each assistant has
  an explicit allow-list.
- Each tool call is executed with the **caller's** identity and
  permissions and authorized on the server independently of the model
  (FR-AI-020).
- Tool arguments and results are schema-validated and size-limited.
- Tools never expose database credentials, raw SQL, shell access or write
  operations (FR-AI-021).
- Denied tool calls are logged as security events (NFR-SEC-019).
- The DevOps assistant (ADV) only drafts reports and Jira incidents;
  submission and any remediation require explicit human approval and are
  audited (FR-OPSAI-005 to FR-OPSAI-007).

## 13. Secret Management and Rotation

| Environment | Storage | Status |
|---|---|---|
| Local | `.env` copied from `.env.example`, git-ignored | Implemented (ignore rules); Planned (application settings, SHOP-016) |
| CI | GitHub Actions encrypted secrets, scoped to the workflows that need them; OIDC for cloud | Planned, SHOP-017 |
| Cloud | Managed secrets service (Secrets Manager or SSM Parameter Store, decided by cost in SHOP-093) | Deferred |

Rules: secrets never appear in source code, images, Helm values,
Terraform files, CI logs, notifications or LLM prompts. Generate local
secrets with a cryptographically secure generator, for example
`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.

| Secret | Rotation trigger | Procedure |
|---|---|---|
| Session signing key | Suspected exposure; before public deployment | Replace the value; all sessions become invalid (users sign in again) |
| Database passwords | Suspected exposure; staff change; yearly in cloud | Create the new credential, update the secret, restart, then revoke the old credential |
| LLM and provider API keys | Suspected exposure; provider change | Revoke at the provider, issue a new key with the same narrow scope, update the secret |
| Jira API token (ADV) | Suspected exposure; 90 days | Revoke and reissue a read- or draft-scoped token |
| Cloud credentials | Never long-lived; OIDC short-lived tokens only | Not applicable |

## 14. Sensitive Data and Logging

- Data is synthetic (NFR-PRIV-001). Personal fields are masked in admin
  list views (FR-ADM-009).
- Logs are structured JSON with correlation IDs (NFR-OBS-001) and must
  never contain passwords, password hashes, session IDs, CSRF tokens, API
  keys, full email addresses or addresses (NFR-SEC-014, NFR-PRIV-002).
  Redaction is applied in the logging configuration, not left to callers.
- Logged security events: sign-in failures, lockouts, CSRF failures,
  authorization denials, role changes, account disabling, import of
  rejected files, AI tool denials and budget exhaustion (NFR-SEC-019).
- Audit events record actor, action, target, time and changed fields,
  excluding secrets (FR-ADM-010).
- Log retention is limited locally and, in the cloud, set per log group
  for cost and privacy.

## 15. Dependency and Supply-Chain Security

| Control | Scope | Status |
|---|---|---|
| Lockfiles committed (`uv.lock`, `package-lock.json`); CI uses frozen installs (`uv sync --locked`, `npm ci`) | Backend, frontend | Planned, SHOP-010, SHOP-014 |
| Dependency justification (purpose, maintenance, license, alternatives) | Every new dependency | Rule in force (`.claude/rules/security.md`) |
| **Gitleaks** secret scanning on pull requests; full-history scan | Repository | Planned, SHOP-018; history scan SHOP-079 |
| **Dependabot** version and security updates (pip/uv, npm, GitHub Actions, Docker) | Repository | Planned, SHOP-018 |
| **pip-audit** against the locked backend dependencies | Backend | Planned, SHOP-018 (reporting), blocking in M7 |
| **npm audit** against the lockfile | Frontend | Planned, SHOP-018 (reporting), blocking in M7 |
| **Trivy** image, filesystem and IaC scanning; fails on unresolved critical findings; SBOM generation | Images, Terraform, Helm | Planned, SHOP-079 (FR-DEV-007) |
| Third-party GitHub Actions pinned to full commit SHAs; least-privilege `permissions:` | CI | Planned, SHOP-017 |

Exceptions to a blocking finding require a documented justification with
an expiry date in the pull request.

## 16. Docker and Kubernetes Security

**Status: Planned** ([ADR-0008](adr/0008-docker-and-kubernetes-adoption.md)).

| Area | Control | Milestone |
|---|---|---|
| Images | Multi-stage builds, minimal pinned bases, non-root user, no secrets in layers, `.dockerignore`, health checks | Basic M1 (SHOP-122), hardened M7 (SHOP-075) |
| Compose | Ports bound to `127.0.0.1`; configuration from `.env`; named volumes | M1–M5 |
| Runtime | Read-only root filesystem where practical; dropped capabilities; no privileged containers (NFR-SEC-018) | M7 |
| Kubernetes | Resource requests and limits, probes, `runAsNonRoot`, `allowPrivilegeEscalation: false`, seccomp `RuntimeDefault`, network policies where supported (FR-DEV-019) | M8 |
| Secrets in Kubernetes | Never committed in plaintext; injected from a secrets mechanism decided in M8 or M10 | M8 |
| GitOps | Argo CD deploys only from Git; no manual cluster changes (FR-DEV-013) | M8 |

## 17. AWS IAM and Least Privilege

**Status: Deferred.** No AWS account access or resource exists. All AWS
work requires explicit approval and a cost proposal (`CLAUDE.md` section
12; `.claude/rules/aws-infrastructure.md`).

Principles for SHOP-094 and later:

- Root account used only for account setup; MFA on every human identity.
- Human access through short-lived, role-based sign-in; no IAM user
  access keys.
- CI uses GitHub OIDC roles restricted to this repository and specific
  branches or environments; separate roles for plan and apply.
- Workload roles grant only the actions and resources needed (for example
  read of named secrets, write to one log group, read/write to one bucket
  prefix); no wildcard actions on wildcard resources.
- Data stores are not publicly accessible; security groups allow only
  required ports from known sources.
- AWS Budgets alerts are configured before the first deployment and are
  **not** spending caps (NFR-COST-005).

## 18. Incident Response

**Status: Planned** (procedure defined now; tooling from M8).

| Severity | Examples | Target response |
|---|---|---|
| SEV-1 | Secret exposed publicly; unauthorized cloud spend; data exposed from a public deployment | Immediately when discovered |
| SEV-2 | Authorization bypass found; vulnerable dependency exploitable in a deployed environment | Within 1 day |
| SEV-3 | Vulnerability with no deployed exposure; failed security scan | Within 1 week |

Response steps:

1. **Detect and record:** open a Jira incident (draft may come from the
   DevOps assistant, ADV) with time, reporter and evidence. Do not post
   secrets or exploit details in public issues.
2. **Contain:** revoke or rotate exposed credentials first; disable the
   affected feature flag or endpoint; scale down or tear down cloud
   environments if needed (requires owner approval).
3. **Eradicate:** fix the cause on a `fix/` branch with a regression test.
4. **Recover:** redeploy the fixed image by digest; restore data from
   backup if required (section 19); verify.
5. **Review:** write a short post-incident review (timeline, cause,
   impact, actions) within one week and update this document or the rules.

**Committed secret runbook:** treat the secret as compromised even if the
commit was never pushed or was removed. Revoke and rotate it at the
source, then remove it from the working tree. Rewriting published Git
history requires a force push, which needs explicit owner approval
(`CLAUDE.md` section 12) and does not make the secret safe again.

## 19. Backup and Recovery

**Status: Planned** ([ARCHITECTURE section 12.4](ARCHITECTURE.md#124-backup-and-recovery)).

- Local and CI data is reproducible from seeders; no backup is required.
- Cloud environments meet RPO ≤ 24 hours and RTO ≤ 4 hours
  (NFR-REL-006) using managed snapshots or scheduled `pg_dump` to
  encrypted storage, decided with the AWS platform.
- Backups are encrypted, access-restricted and retained only as long as
  needed; restore is tested before any public deployment and after major
  schema changes.
- Destructive database operations (drop, truncate, restore over existing
  data) require explicit owner approval.

## 20. Security Testing Requirements

| Test | Scope | Milestone |
|---|---|---|
| Unit tests for password policy, hashing parameters, CSRF validation, CSV escaping | Backend | M3, M5 |
| Authorization sweep: every endpoint × every role, including object-level cases | API tests | M3, M4 |
| CSRF tests: missing, invalid and cross-origin requests rejected | API tests | M3 |
| Rate-limit tests including back-off and `Retry-After` | API tests | M3 |
| Injection tests: SQL metacharacters, HTML and script payloads in all text inputs and imports | API tests | M3, M5 |
| Upload tests: oversized, wrong type, malformed and formula-injection files | API tests | M5 |
| SSRF tests: private addresses, redirects and DNS rebinding cases | Integration tests | M5 |
| Prompt-injection and tool-authorization suite | AI evaluation | M6 |
| Secret, dependency and image scans | CI | M1, M7 |
| Security review against OWASP Top 10 and OWASP Top 10 for LLM Applications, plus a log leakage scan, recorded here | Whole system | SHOP-082 (Tier 1 release); repeated before any public deployment (NFR-SEC-020) |

Security tests follow `.claude/rules/testing.md`; they are never weakened
or skipped to make a build pass.

## 21. Vulnerability Reporting

eShop_AI is an educational, non-commercial portfolio project with
synthetic data and simulated payments. Reports are still welcome.

- Report privately using GitHub's **private vulnerability reporting**
  ("Report a vulnerability" on the repository's Security tab), enabled
  in SHOP-008. If it is unavailable, contact the
  repository owner through their GitHub profile.
- Do **not** open public issues for vulnerabilities, and do not test
  against any deployment you do not own.
- Include the affected component, steps to reproduce and impact.
- Expected handling: acknowledgement within 7 days and a fix or mitigation
  plan following the severity targets in section 18. There is no bug
  bounty.

## 22. Maintenance

Review this document at every milestone exit and whenever a control's
status changes from Planned to Implemented. Record significant security
design changes as ADRs.

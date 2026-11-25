---
paths:
  - "backend/app/integrations/**"
  - "backend/app/platform/**"
---

# SDK, Integration and Platform Component Rules

PRD references: section 6.11 (FR-PLAT), section 11 (FR-IMP).

## General
- Prefer existing framework and infrastructure capabilities (worker
  framework retries, library rate limiters, Kubernetes probes, Prometheus
  alerting) before custom implementations. Custom components need an ADR.
- Keep providers interchangeable and selectable by configuration.

## Internal SDK and Integration Layer
- External services live under `backend/app/integrations/<provider>/`.
- Consumers depend on typed interfaces (ports); adapters implement them.
- Use official third-party SDKs behind these interfaces where appropriate;
  SDK types never leak beyond the adapter.
- Every port has a mock or fake implementation, the default for local
  development and tests.
- Use one shared, configured HTTP client per application, managed by the
  application lifecycle, with explicit timeouts and connection limits.
  Never create a client per call. Use a generic user agent.
- Treat responses as untrusted: validate with Pydantic and limit sizes.
- Load provider credentials from environment variables or managed secrets
  with least-privilege scopes; never log them.
- Comply with source terms, rate limits, robots directives and attribution.
  Never bypass access restrictions. Record source and license data.
- Cache external responses with a configurable TTL.
- No live external calls in CI; use contract tests with recorded fixtures.

## Gatekeeper
- All outbound provider calls and AI token usage pass through Gatekeeper:
  check quota before the call, record usage after.
- Gatekeeper also centralizes inbound rate limits.
- Limits are configuration-driven; denial triggers a defined fallback.

## Resilience
- Retries are bounded (maximum attempts and total duration), use
  exponential back-off with jitter, honor `Retry-After`, and apply only to
  transient errors on idempotent operations. Never retry validation or
  authorization failures.
- Use circuit breakers only for external dependencies with demonstrated
  failure patterns; document thresholds.

## Jobs, Schedules and Dead Letters
- Job handlers are idempotent and persist their state.
- Schedules guarantee a single execution; external-source schedules are
  disabled by default.
- Jobs exhausting retries move to the dead-letter queue with error details
  and attempt history; admin retry or discard is audited.

## Other Components
- Watchdog detects and reports failures; it never remediates autonomously.
- Notifications use channel abstractions (in-app, local mail catcher);
  no real email or SMS; no secrets in content.
- Feature flags are typed, default to the safe (off) state and are
  evaluated on the server; the frontend receives only public flags.
- Audit logging goes through one append-only audit service.

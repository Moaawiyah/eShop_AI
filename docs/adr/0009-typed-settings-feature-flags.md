# ADR-0009: Typed Settings for Feature Flags

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-28 |
| Deciders | Project owner (accelerated M1 Batch A authorization) |
| Jira | SHOP-016 |

## Context

Features such as the AI assistant, external product sources and
notifications must be switchable and safe (off) by default (FR-PLAT-013).
The frontend needs to know a subset of the flags. UD-13 left the
implementation open: typed settings, database-backed flags or an
OpenFeature-compatible library. No database exists before M2 and there is
no requirement yet for runtime toggling or user targeting.

## Decision

Feature flags are typed, environment-driven Pydantic settings
(`FEATURE_<NAME>`), evaluated on the server and **off by default**. Invalid
values stop start-up.

- `app/platform/flags.py` provides a `Flag` enum and `FeatureFlags` with
  `is_enabled(flag)` and `public_flags()`.
- An explicit allow-list (`PUBLIC_FLAGS`) decides which flags reach the
  frontend through `GET /api/v1/config/public-flags`; server-only flags
  never leave the backend.
- The `context` argument in the illustrative interface of ARCHITECTURE
  section 5 is omitted until targeting exists.
- Database-backed or OpenFeature flags require a future ADR, when runtime
  toggling or targeting is needed.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Database-backed flags | Needs the M2 database and an audit trail; premature |
| OpenFeature SDK and provider | Extra dependency; no targeting need yet |

## Consequences

**Positive**

- No new dependency; flags are validated, typed and testable.
- Safe defaults; a minimal, explicit public surface.

**Negative**

- Changing a flag requires a restart or redeployment.
- No per-user targeting or percentage rollouts.

## Related Requirements and Tasks

- Requirements: FR-PLAT-013, NFR-PORT-002, FR-DEV-020
- Tasks: SHOP-016
- Documents: `docs/ARCHITECTURE.md` sections 5 and 8

## Reconsideration Conditions

Revisit when a flag must change without a restart, be targeted per user or
role, or need an audit trail.

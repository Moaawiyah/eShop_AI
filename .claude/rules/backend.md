---
paths:
  - "backend/**"
---

# Backend Rules

## Tooling
- Python 3.13. Manage dependencies with uv only (`uv add`, committed
  `uv.lock`); never use `pip install` in the project.
- Ruff for formatting and linting, mypy for static type checking,
  pytest for tests, Pydantic for validation and settings.
- Use the `logging` module with structured JSON output; never `print()`.

## Structure (proposed; finalized in docs/ARCHITECTURE.md)
```
backend/app/
  core/          configuration, logging, database, security primitives
  modules/       domain modules: identity, catalog, cart, orders,
                 payments, inventory, imports, admin
  platform/      cross-cutting components (Gatekeeper, jobs, audit,
                 feature flags, notifications, Watchdog)
  integrations/  internal SDK and external provider adapters
  ai/            agents, LLM ports and MCP tools
backend/tests/
```
- Modules interact through service interfaces; never import another
  module's repositories or ORM models directly.
- Business logic must not depend on FastAPI, SQLAlchemy or provider SDKs.

## FastAPI
- Keep routers thin; put logic in services.
- Declare explicit Pydantic request and response models.
- Use dependency injection (`Depends`) for sessions, services and auth.
- Keep OpenAPI accurate with stable operation IDs; it generates the
  frontend API types.
- Map domain exceptions to consistent error responses without
  internal details.
- Never block the event loop; use async drivers or a thread pool.

## Persistence
- SQLAlchemy 2.x typed models; explicit transaction boundaries.
- Change schemas only through Alembic migrations. Never edit an applied
  migration. Follow expand/contract so the previous release keeps working.
- Use row-level locking or equivalent for stock reservation.
- Destructive database operations require explicit user approval.

## Domain Conventions
- Money is integer cents in USD; validate non-negative; never use floats.
- Customer-facing APIs return availability categories
  (`in_stock`, `low_stock`, `out_of_stock`), never exact stock counts.
- Payments use the internal simulator only.
- Background work runs in the worker framework with idempotent handlers.
- Configuration comes from environment variables via Pydantic Settings.

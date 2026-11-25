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

## Structure (see docs/ARCHITECTURE.md section 3)
```
backend/app/
  api/           versioned router assembly, shared dependencies,
                 middleware, error handlers, OpenAPI configuration
  core/          configuration, logging, errors, security primitives
  database/      PostgreSQL engine and sessions, Redis client, migrations
  modules/       auth, users, catalog, inventory, cart, orders,
                 payments, admin, ai
  integrations/  internal SDK and external provider adapters
  platform/      Gatekeeper, jobs, scheduler, audit, feature flags,
                 notifications, resilience, Watchdog
backend/tests/
```
- Follow the dependency rules in ARCHITECTURE section 3.2; no cycles.
- Modules interact through each other's public service interfaces; never
  import another module's repositories or ORM models directly.
- Domain rules must not depend on FastAPI request objects or provider SDKs.

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
- Check and decrement stock atomically inside the order transaction
  (conditional update or row lock) to prevent overselling; no stock
  reservation in the initial checkout.
- Destructive database operations require explicit user approval.

## Domain Conventions
- Money is integer cents in USD; validate non-negative; never use floats.
- Customer-facing APIs return availability categories
  (`in_stock`, `low_stock`, `out_of_stock`), never exact stock counts.
- Payments use the internal simulator only.
- Background work runs in the worker framework with idempotent handlers.
- Configuration comes from environment variables via Pydantic Settings.

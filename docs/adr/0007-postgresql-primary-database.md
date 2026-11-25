# ADR-0007: PostgreSQL as the Primary Database

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

The domain is relational (products, categories, inventory, carts, orders,
payments, audit) and needs strong transactional guarantees to prevent
overselling. Search, faceting and optionally semantic retrieval are
required, preferably without extra infrastructure.

## Decision

Use **PostgreSQL** as the system of record for all application data,
accessed through SQLAlchemy 2.x with Alembic migrations.

- Transactions, row locks and check constraints enforce inventory
  consistency (ARCHITECTURE section 7.5).
- Built-in search capabilities are evaluated first for keyword search;
  the exact design is decided by UD-07.
- Redis is a supporting store (rate limits, cache, queue, and sessions if
  UD-08 selects it), never the system of record.
- Tests run against real PostgreSQL, not SQLite.
- The cloud hosting option (managed RDS or container) is decided with the
  AWS platform (ARCHITECTURE section 11).

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| MySQL or MariaDB | Viable, but weaker built-in search and JSON support for this use case |
| Document database | Weak multi-entity transactions for checkout |
| SQLite | Inadequate concurrency and behavioural differences from production |
| Dedicated search engine now | Extra infrastructure before measured need (UD-07) |

## Consequences

**Positive**

- ACID transactions and constraints for correctness.
- One database covers relational data, search and JSON snapshots.
- Widely supported locally, in CI and on AWS.

**Negative**

- Search relevance and scale are limited compared with a search engine.
- Managed PostgreSQL in the cloud has a fixed monthly cost.

## Related Requirements and Tasks

- Requirements: NFR-REL-001, NFR-REL-002, NFR-MNT-004, FR-CHK-007
- Tasks: SHOP-021, SHOP-022, SHOP-023, SHOP-024, SHOP-029
- Documents: ARCHITECTURE section 7

## Reconsideration Conditions

Revisit search (not the system of record) if search latency misses the
NFR-PERF targets on the 10,000-product performance dataset after indexing
work.

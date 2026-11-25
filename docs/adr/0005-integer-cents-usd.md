# ADR-0005: Money as Integer Cents in USD

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-25 |
| Deciders | Project owner |
| Jira | SHOP-003 |

## Context

Prices, cart totals, orders, payments, price history and AI budget
filters all handle money. Binary floating-point values cannot represent
most decimal amounts exactly, and rounding errors in totals are a classic
defect. The product scope is a single currency with no tax.

## Decision

Represent every monetary amount as an **integer number of US cents**.

- Database columns are integers named `*_cents` with `CHECK (… >= 0)`;
  no currency column, because USD is the only currency.
- Pydantic models use `int` fields named `*_cents`; the API exchanges
  cents, never formatted strings or floats.
- Totals are computed on the server from integer values; client-supplied
  prices are ignored.
- The frontend formats cents with one shared `en-US` USD formatter.
- Order items store the unit price in cents at purchase time.
- AI intents express budgets in cents; prices shown to users come from
  the database, never from model text.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Floating-point amounts | Inexact; rounding defects |
| `NUMERIC` / `Decimal` with currency | Correct, but adds conversion and multi-currency complexity outside scope |
| Money library with currency objects | Unnecessary for a single currency |

## Consequences

**Positive**

- Exact arithmetic and simple comparisons in every layer.
- Clear, self-describing field names.

**Negative**

- Every display needs formatting; user input in dollars must be converted.
- Adding currencies or tax later requires a new ADR and migration.

## Related Requirements and Tasks

- Requirements: FR-CART-004, FR-PAY-005, NFR-LOC-001
- Tasks: SHOP-023, SHOP-024, SHOP-034, SHOP-036, SHOP-037
- Documents: ARCHITECTURE section 7.3

## Reconsideration Conditions

Revisit if multiple currencies, tax calculation or fractional-cent pricing
become in scope.

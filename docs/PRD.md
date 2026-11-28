# eShop_AI — Product Requirements Document

| Field | Value |
|---|---|
| Document | Product Requirements Document (PRD) |
| Version | 0.4 — Draft |
| Status | Approved by the project owner (2026-11-28, M0 exit); changes through pull requests |
| Jira | SHOP-001, SHOP-002, SHOP-003, SHOP-009 |
| Milestone | M0 — Project Initialization |
| Last updated | 2026-11-25 |
| Owner | Project owner |

> **Implementation status:** nothing in this document is implemented yet.
> Every requirement below is **planned**. Delivery order is defined in
> `docs/ROADMAP.md`.

### Revision History

| Version | Date | Jira | Changes |
|---|---|---|---|
| 0.1 | 2026-11-25 | SHOP-001 | Initial draft |
| 0.2 | 2026-11-25 | SHOP-002 | Approved password policy; configurable AI limits (2,000-character default); staged demo datasets (50 → 500) plus 10,000-product performance dataset; defined performance test environment and workload; availability-category rule; platform components (section 6.11) |
| 0.3 | 2026-11-25 | SHOP-003 | Initial checkout uses a single-transaction stock check-and-decrement (FR-CHK-007); stock reservation (FR-CHK-004) becomes optional (`ADV`) |
| 0.4 | 2026-11-25 | SHOP-009 | A-05: Jira project key `ESHOP`; roadmap IDs remain `SHOP-NNN` and are mapped to Jira keys |

## Document Conventions

- **MUST / SHOULD / MAY** follow RFC 2119 meaning.
- **Scope tags:** `MVP` = required for the Minimum Viable Product.
  `ADV` = advanced portfolio feature delivered after the MVP.
- **Identifiers** are unique and stable. Never reuse a retired ID.

| Prefix | Meaning | Section |
|---|---|---|
| `O-` | Project objective | 3 |
| `FR-<AREA>-` | Functional requirement | 6, 10, 11, 12 |
| `PE-` | Performance test environment | 14.1 |
| `NFR-<AREA>-` | Non-functional requirement | 7, 10, 13, 14, 15 |
| `CW-` / `AW-` | Customer / administrator workflow | 8, 9 |
| `AC-` | Acceptance criterion | 19 |
| `R-` / `A-` / `UD-` | Risk / assumption / unresolved decision | 20 |

- **Money:** all amounts are integer cents in USD (e.g. `129999` = $1,299.99).
- **Payments:** every payment flow is simulated. No real money and no real
  payment card data are involved.

### Confirmed Product Constraints

Confirmed by the project owner in SHOP-002:

- English-only user interface.
- All payments simulated.
- USD pricing only, stored as integer cents.
- No tax calculation.
- Customer-facing inventory information is limited to availability
  categories (`in_stock`, `low_stock`, `out_of_stock`).
- Unresolved infrastructure decisions (section 20.3) remain deferred until
  the milestone that requires them.

---

## 1. Executive Summary

eShop_AI is a non-commercial, educational electronics e-commerce application
built as an advanced engineering portfolio. It is inspired by the breadth and
catalog depth of large electronics retailers such as KSP, but has **no
affiliation** with any retailer and uses none of their branding, content or
data.

The product combines three things:

1. **A full-featured storefront** for laptops, smartphones, TVs, gaming,
   components, storage, networking, audio and accessories, with advanced
   filtering, comparison, cart, wishlist and simulated checkout.
2. **An administration back office** covering catalog, inventory, orders,
   product data imports, price synchronization, audit logs and analytics.
3. **Grounded AI capabilities:** a customer shopping assistant that answers
   only from the real catalog, and a DevOps assistant that analyzes logs,
   CI failures and alerts in read-only mode.

It is engineered as a FastAPI modular monolith with a Next.js frontend,
runs completely on a local machine with demo data and mock AI providers,
and is designed for optional, cost-approved deployment to AWS using
Terraform, Kubernetes, Helm and Argo CD.

## 2. Project Vision

> Demonstrate, through a realistic and polished electronics store, how a
> single engineer can design, build, secure, operate and observe a
> production-grade, AI-augmented system — at near-zero cost.

Guiding principles:

- **Realistic, not real.** Production-quality engineering on simulated
  commerce: no real payments, customers or orders.
- **Local first.** Every feature works offline-from-cloud with demo data
  and a mock LLM.
- **Grounded AI.** AI adds value where deterministic logic is insufficient
  and never invents products, prices or stock.
- **Lawful data.** Only authorized, free data sources. No scraping that
  bypasses access controls or terms.
- **Cost discipline.** Cloud resources exist only when approved, estimated
  and removable.

## 3. Project Objectives

| ID | Objective | Success measure |
|---|---|---|
| O-1 | Deliver a complete, responsive electronics storefront | All MVP customer workflows (section 8) pass end-to-end tests |
| O-2 | Deliver an operational admin back office | All MVP admin workflows (section 9) pass end-to-end tests |
| O-3 | Integrate grounded, provider-independent AI | Assistant evaluation suite passes (AC-040 to AC-044) |
| O-4 | Demonstrate DevOps and IaC maturity | CI pipeline, containers, kind, Helm and Argo CD operational (section 12) |
| O-5 | Demonstrate observability | Logs, metrics, traces and alerts available for every environment |
| O-6 | Demonstrate security engineering | Section 13 requirements verified; zero unresolved critical findings |
| O-7 | Minimize cost | Local development at zero cloud cost; AWS spend within approved budget |
| O-8 | Maintain professional documentation | All documents in CLAUDE.md section 13 exist and reflect actual state |

## 4. Target Users

| Persona | Description | Primary goals |
|---|---|---|
| Everyday shopper | Buys consumer electronics with limited technical knowledge | Find a suitable product within budget quickly |
| Technical enthusiast | Builds PCs and compares detailed specifications | Filter precisely, compare specs, check compatibility |
| Store administrator | Operates the catalog, inventory and orders | Keep data accurate, process orders, monitor imports |
| DevOps operator | Operates the platform | Detect, diagnose and resolve incidents quickly |
| Portfolio reviewer | Recruiter, hiring manager or engineer evaluating the project | Understand architecture and quality quickly, run a demo |

## 5. User Roles

Authorization uses role-based access control (RBAC). A user may hold multiple
roles. Permissions are checked on the server for every request.

| Role | Description | Scope |
|---|---|---|
| Guest | Unauthenticated visitor | MVP |
| Customer | Registered shopper | MVP |
| Administrator | Full back-office access, including role assignment | MVP |
| Catalog Manager | Products, categories, imports and prices | ADV |
| Order Manager | Orders and customer support views | ADV |
| DevOps Operator | Operational dashboards and the DevOps AI assistant | ADV |

Permission summary (`R` read, `W` write, `—` none):

| Capability | Guest | Customer | Catalog Mgr | Order Mgr | DevOps Op | Admin |
|---|---|---|---|---|---|---|
| Browse, search, compare | R | R | R | R | R | R |
| Cart and wishlist | W (cart only) | W | — | — | — | — |
| Checkout and own orders | — | W | — | — | — | — |
| Products, categories, inventory | — | — | W | R | — | W |
| Imports and price sync | — | — | W | — | R | W |
| Orders (all customers) | — | — | — | W | — | W |
| Customers (demo data) | — | — | — | R | — | W |
| Audit logs | — | — | R (own) | R (own) | R | R |
| DevOps AI and operational data | — | — | — | — | R | R |
| Roles and user administration | — | — | — | — | — | W |

## 6. Functional Requirements

AI, product data integration and DevOps functional requirements are specified
in sections 10, 11 and 12 respectively.

### 6.1 Accounts and Authentication (FR-AUTH)

| ID | Requirement | Scope |
|---|---|---|
| FR-AUTH-001 | Guests MUST be able to register with email, display name and password. | MVP |
| FR-AUTH-002 | Users MUST be able to sign in and sign out using secure, server-side, cookie-based sessions. | MVP |
| FR-AUTH-003 | The system MUST protect all state-changing requests with CSRF protection. | MVP |
| FR-AUTH-004 | The system MUST rotate the session identifier on sign-in and privilege change. | MVP |
| FR-AUTH-005 | Sessions MUST expire after configurable idle and absolute timeouts, with stricter defaults for back-office roles. | MVP |
| FR-AUTH-006 | Sign-in MUST be rate limited per account and per client address, with progressive back-off. | MVP |
| FR-AUTH-007 | Authentication errors MUST NOT reveal whether an email address is registered. | MVP |
| FR-AUTH-008 | Users MUST be able to change their password while signed in, which invalidates other sessions. | MVP |
| FR-AUTH-009 | Users SHOULD be able to reset a forgotten password through a time-limited, single-use token delivered by a local mail catcher (no real email delivery). | ADV |
| FR-AUTH-010 | Back-office users SHOULD be able to enroll in time-based one-time password (TOTP) multi-factor authentication. | ADV |
| FR-AUTH-011 | Users SHOULD be able to view and revoke their active sessions. | ADV |

### 6.2 Storefront and Catalog (FR-CAT)

| ID | Requirement | Scope |
|---|---|---|
| FR-CAT-001 | The storefront MUST provide a responsive, premium-quality home page with featured categories, promotions and products. | MVP |
| FR-CAT-002 | The catalog MUST support the eight top-level categories: Laptops & Computers; Smartphones & Tablets; TVs & Monitors; Gaming Consoles & Accessories; Computer Components; Storage & Networking; Audio; Electronics Accessories. | MVP |
| FR-CAT-003 | Categories MUST support a hierarchy of subcategories (at least two levels below top level). | MVP |
| FR-CAT-004 | Each category MUST define a specification attribute schema (name, data type, unit, filterable flag, comparable flag). | MVP |
| FR-CAT-005 | Category listing pages MUST paginate results and show name, image, price, availability status and rating. | MVP |
| FR-CAT-006 | Products MUST have a lifecycle status (draft, active, archived); only active products are visible to customers. | MVP |
| FR-CAT-007 | The storefront MUST display breadcrumbs reflecting the category hierarchy. | MVP |
| FR-CAT-008 | Products MAY show a list price and a current price; a discount is shown only when the current price is lower. | MVP |
| FR-CAT-009 | The storefront SHOULD show recently viewed products for the current session. | ADV |
| FR-CAT-010 | Customer-facing UI, APIs and AI tools MUST expose inventory only as availability categories (`in_stock`, `low_stock`, `out_of_stock`), never exact stock counts. Exact counts are restricted to authorized back-office roles. | MVP |

### 6.3 Search, Filtering and Sorting (FR-SRCH)

| ID | Requirement | Scope |
|---|---|---|
| FR-SRCH-001 | Users MUST be able to search products by keyword across name, brand, model and key specifications. | MVP |
| FR-SRCH-002 | Search MUST tolerate minor typos and partial terms. | MVP |
| FR-SRCH-003 | Listings MUST provide faceted filters derived from the category attribute schema (e.g. RAM, storage, screen size, refresh rate). | MVP |
| FR-SRCH-004 | Listings MUST provide filters for brand, price range, availability and minimum rating. | MVP |
| FR-SRCH-005 | Facets MUST display result counts and update when filters change. | MVP |
| FR-SRCH-006 | Users MUST be able to sort by relevance, price (ascending/descending), newest and rating. | MVP |
| FR-SRCH-007 | Filter, sort and page state MUST be reflected in the URL so results are shareable and bookmarkable. | MVP |
| FR-SRCH-008 | Search SHOULD provide autocomplete suggestions for products, brands and categories. | ADV |
| FR-SRCH-009 | Search MAY support semantic (embedding-based) retrieval in addition to keyword search. | ADV |

### 6.4 Product Details and Comparison (FR-PDP, FR-CMP)

| ID | Requirement | Scope |
|---|---|---|
| FR-PDP-001 | Product pages MUST show name, brand, model, images, price, availability, description and rating summary. | MVP |
| FR-PDP-002 | Product pages MUST show a structured specification table grouped by attribute group, with units. | MVP |
| FR-PDP-003 | Product pages MUST show the data source attribution and image attribution where required by the source license. | MVP |
| FR-PDP-004 | Product pages SHOULD show price history and the lowest price in the last 30 days. | ADV |
| FR-PDP-005 | Product pages SHOULD show related and alternative products. | ADV |
| FR-CMP-001 | Users MUST be able to add up to four products from the same top-level category to a comparison. | MVP |
| FR-CMP-002 | The comparison view MUST align comparable attributes side by side and allow highlighting differences. | MVP |
| FR-CMP-003 | The comparison MUST persist for the session and be shareable through a URL. | MVP |

### 6.5 Cart and Wishlist (FR-CART, FR-WISH)

| ID | Requirement | Scope |
|---|---|---|
| FR-CART-001 | Guests and customers MUST be able to add, update the quantity of and remove products in a cart. | MVP |
| FR-CART-002 | Quantities MUST be limited by available stock and a configurable per-item maximum; rejection messages MUST NOT reveal exact stock counts (FR-CAT-010). | MVP |
| FR-CART-003 | A guest cart MUST merge into the customer cart on sign-in without duplicating lines. | MVP |
| FR-CART-004 | Cart totals MUST be computed on the server in integer cents; the client never supplies prices. | MVP |
| FR-CART-005 | The cart MUST notify the user when a product's price or availability changed since it was added. | MVP |
| FR-WISH-001 | Customers MUST be able to add products to and remove products from a wishlist. | MVP |
| FR-WISH-002 | Customers MUST be able to move wishlist items to the cart. | MVP |
| FR-WISH-003 | Customers SHOULD see a price-drop indicator for wishlist items. | ADV |

### 6.6 Checkout and Simulated Payments (FR-CHK, FR-PAY)

| ID | Requirement | Scope |
|---|---|---|
| FR-CHK-001 | Only signed-in customers MUST be able to check out. | MVP |
| FR-CHK-002 | Checkout MUST collect a shipping address (synthetic data permitted) and a simulated shipping method. | MVP |
| FR-CHK-003 | Checkout MUST revalidate prices and stock on the server before placing the order. | MVP |
| FR-CHK-004 | Checkout MAY reserve stock for a configurable period (releasing expired reservations) only if a multi-step checkout later requires it; the initial single-step checkout does not reserve stock. | ADV |
| FR-CHK-005 | Order placement MUST be idempotent so repeated submissions do not create duplicate orders or charges. | MVP |
| FR-CHK-006 | The order summary MUST show item subtotal, simulated shipping and total in USD; tax is not calculated and the UI states this. | MVP |
| FR-CHK-007 | Order placement MUST check and decrement stock atomically within one database transaction together with order and payment records, so that concurrent checkouts never oversell; a declined simulated payment leaves stock unchanged. | MVP |
| FR-PAY-001 | Payments MUST be processed by an internal payment simulator; no external payment provider is called. | MVP |
| FR-PAY-002 | The simulator MUST support deterministic outcomes: approved, declined and processing error. | MVP |
| FR-PAY-003 | The UI MUST NOT contain inputs for real payment card numbers, CVV or bank details. | MVP |
| FR-PAY-004 | Every payment page MUST clearly state that payments are simulated and no money is charged. | MVP |
| FR-PAY-005 | Each payment attempt MUST be recorded with outcome, amount in cents and timestamp. | MVP |
| FR-PAY-006 | Administrators SHOULD be able to issue simulated full refunds. | ADV |

### 6.7 Orders and Tracking (FR-ORD)

| ID | Requirement | Scope |
|---|---|---|
| FR-ORD-001 | Orders MUST follow a defined state machine: pending_payment, paid, processing, shipped, delivered, cancelled, payment_failed, refunded. | MVP |
| FR-ORD-002 | Invalid state transitions MUST be rejected. | MVP |
| FR-ORD-003 | Orders MUST store a snapshot of product name, SKU and unit price in cents at the time of purchase. | MVP |
| FR-ORD-004 | Customers MUST be able to view order history and order details. | MVP |
| FR-ORD-005 | Customers MUST be able to view a tracking timeline with simulated shipment events and a simulated tracking number. | MVP |
| FR-ORD-006 | Customers MUST be able to cancel an order before it is shipped. | MVP |
| FR-ORD-007 | In demo mode, a scheduled job SHOULD advance shipped orders through simulated tracking events. | ADV |

### 6.8 Customer Profile (FR-PROF)

| ID | Requirement | Scope |
|---|---|---|
| FR-PROF-001 | Customers MUST be able to view and update their display name. | MVP |
| FR-PROF-002 | Customers MUST be able to manage saved shipping addresses. | MVP |
| FR-PROF-003 | Customers SHOULD be able to delete their account, anonymizing personal data while retaining order records. | ADV |
| FR-PROF-004 | Customers MAY export their personal data in JSON format. | ADV |

### 6.9 Product Reviews (FR-REV)

| ID | Requirement | Scope |
|---|---|---|
| FR-REV-001 | Product pages MUST display reviews and an aggregate rating from deterministic, synthetic demo data. | MVP |
| FR-REV-002 | Demo reviews MUST be labeled as demo content. | MVP |
| FR-REV-003 | Customers SHOULD be able to submit one review per purchased and delivered product. | ADV |
| FR-REV-004 | Submitted reviews SHOULD require moderation approval before publication, and review content MUST be rendered safely (no HTML execution). | ADV |

### 6.10 Administration (FR-ADM)

| ID | Requirement | Scope |
|---|---|---|
| FR-ADM-001 | Back-office routes and APIs MUST require an authenticated user holding an authorized role. | MVP |
| FR-ADM-002 | Administrators MUST be able to assign and revoke roles. | MVP |
| FR-ADM-003 | Authorized users MUST be able to create, read, update and archive products, including specifications and images. | MVP |
| FR-ADM-004 | Product forms MUST validate attributes against the category attribute schema. | MVP |
| FR-ADM-005 | Authorized users MUST be able to create, rename, reorder, move and archive categories and edit attribute schemas. | MVP |
| FR-ADM-006 | Authorized users MUST be able to adjust stock with a mandatory reason, recorded as an inventory movement. | MVP |
| FR-ADM-007 | The system MUST flag products whose available stock is below a configurable low-stock threshold. | MVP |
| FR-ADM-008 | Authorized users MUST be able to search, filter and view orders and perform valid state transitions. | MVP |
| FR-ADM-009 | Administrators MUST be able to view and disable customer accounts (demo data), with personal fields masked in list views. | MVP |
| FR-ADM-010 | The system MUST record an append-only audit log entry for every back-office write: actor, action, target, timestamp, and changed fields (excluding secrets). | MVP |
| FR-ADM-011 | Authorized users MUST be able to search and filter audit logs by actor, action, target and time range. | MVP |
| FR-ADM-012 | The admin dashboard MUST show: simulated revenue, order count, average order value, low-stock products and recent import job status. | MVP |
| FR-ADM-013 | The dashboard SHOULD show trends over selectable periods, top products and category performance. | ADV |
| FR-ADM-014 | Archiving MUST be preferred over deletion; hard deletion requires an explicit confirmation step and is audited. | MVP |

Product import, price synchronization, job history and retry controls are
specified in section 11.

### 6.11 Platform and SDK Components (FR-PLAT)

These components are **planned only**; none is built during M0. Delivery
milestones are defined in `docs/ROADMAP.md`. Components MUST reuse existing
framework and infrastructure capabilities before introducing custom code.

| ID | Requirement | Scope |
|---|---|---|
| FR-PLAT-001 | **Internal SDK and integration layer:** all external services MUST be accessed through typed interfaces, with adapters initially located in `backend/app/integrations/`. Official third-party SDKs SHOULD be used behind these interfaces where appropriate, and SDK types MUST NOT leak beyond the adapter. | MVP |
| FR-PLAT-002 | Every integration interface MUST have a mock or fake implementation, selectable by configuration and used by default in local development and automated tests. Providers MUST be interchangeable without changes to business logic. | MVP |
| FR-PLAT-003 | Each application MUST use one shared, configured HTTP client with explicit timeouts, connection limits and managed lifecycle. | MVP |
| FR-PLAT-004 | **Gatekeeper:** a central component MUST enforce inbound rate limits, outbound API quotas per provider and AI token budgets, and apply a defined fallback when a limit is reached. | MVP |
| FR-PLAT-005 | Gatekeeper SHOULD expose usage metrics and current consumption to authorized operators. | ADV |
| FR-PLAT-006 | **Watchdog:** a component SHOULD aggregate the health of dependencies (database, Redis, workers, schedules, external providers, queue and dead-letter depth), expose status and metrics and raise alerts. It detects and reports only; it MUST NOT remediate autonomously. Basic health endpoints (NFR-OBS-002) are delivered earlier. | ADV |
| FR-PLAT-007 | **Background workers** MUST execute asynchronous jobs with persisted state and idempotent handlers. | MVP |
| FR-PLAT-008 | **Scheduled jobs** MUST be declared in configuration, guarantee a single execution per schedule and be disabled by default for external sources (e.g. expired session and stale guest-cart cleanup, price synchronization, tracking progression). | MVP |
| FR-PLAT-009 | **Bounded retries** MUST limit attempts and total duration, use exponential back-off with jitter and apply only to transient errors on idempotent operations (implements FR-IMP-018 and NFR-REL-004). | MVP |
| FR-PLAT-010 | **Circuit breakers** SHOULD protect external providers where failure data justifies them, with documented thresholds (implements FR-IMP-020). | ADV |
| FR-PLAT-011 | **Audit logging** MUST be provided by a single append-only audit service used by all modules for back-office writes, security events and approvals of AI actions (implements FR-ADM-010 and FR-ADM-011). | MVP |
| FR-PLAT-012 | **Notification management** SHOULD deliver channel-independent notifications (in-app and a local mail catcher) using templates, with delivery status. Real email or SMS delivery is out of scope. | ADV |
| FR-PLAT-013 | **Feature flags** MUST be typed and configuration-driven, default to the safe (disabled) state and be evaluated on the server; the frontend receives only explicitly public flags. Flags gate AI features, real providers and schedules. | MVP |
| FR-PLAT-014 | **Dead-letter queue:** jobs that exhaust retries MUST move to a dead-letter queue with error details and attempt history; authorized users can inspect, retry or discard them (audited); growth raises an alert. | MVP |
| FR-PLAT-015 | **Typed frontend API client:** frontend API types SHOULD be generated from the FastAPI OpenAPI specification; a single client MUST handle credentials, CSRF tokens and error normalization; CI MUST fail when generated types are out of date. | MVP |
| FR-PLAT-016 | A custom implementation of any component in this section requires an ADR explaining why existing frameworks or infrastructure capabilities are insufficient. | MVP |

## 7. Non-Functional Requirements

Security, performance and reliability, and cost NFRs are specified in
sections 13, 14 and 15. AI-specific NFRs are in section 10.6.

| ID | Requirement | Scope |
|---|---|---|
| NFR-USE-001 | The storefront MUST be responsive from 360 px to 1920 px viewport width. | MVP |
| NFR-USE-002 | User-facing errors MUST be clear and actionable and MUST NOT expose internal details. | MVP |
| NFR-USE-003 | Loading, empty and error states MUST be designed for every data-driven view. | MVP |
| NFR-ACC-001 | The storefront and back office MUST target WCAG 2.2 level AA. | MVP |
| NFR-ACC-002 | All interactive elements MUST be keyboard operable with visible focus. | MVP |
| NFR-COMP-001 | The UI MUST support the latest two major versions of Chrome, Firefox, Safari and Edge. | MVP |
| NFR-LOC-001 | The UI language is English; prices are displayed in USD using `en-US` formatting. | MVP |
| NFR-MNT-001 | The backend MUST be a modular monolith with explicit module boundaries (e.g. identity, catalog, cart, orders, payments, inventory, imports, ai, admin). | MVP |
| NFR-MNT-002 | Business logic MUST be independent of frameworks and infrastructure adapters. | MVP |
| NFR-MNT-003 | Code MUST pass Ruff and mypy (backend) and ESLint, Prettier and TypeScript strict checks (frontend) in CI. | MVP |
| NFR-MNT-004 | Database schema changes MUST be managed through Alembic migrations only. | MVP |
| NFR-TST-001 | Critical backend business logic MUST have at least 80% line coverage. | MVP |
| NFR-TST-002 | Every external dependency (LLM, data sources, payment simulator) MUST have a mock or fake for tests. | MVP |
| NFR-TST-003 | All MVP workflows MUST be covered by automated end-to-end tests. | MVP |
| NFR-OBS-001 | Services MUST emit structured JSON logs with a correlation/request ID. | MVP |
| NFR-OBS-002 | Services MUST expose health (liveness and readiness) endpoints. | MVP |
| NFR-OBS-003 | Services SHOULD emit OpenTelemetry traces and Prometheus metrics. | ADV |
| NFR-PRIV-001 | All customer data MUST be synthetic; no real personal data is collected for demo purposes. | MVP |
| NFR-PRIV-002 | Logs, traces and AI prompts MUST NOT contain passwords, tokens, session IDs or full personal data. | MVP |
| NFR-PORT-001 | The full application MUST run locally with Docker Compose without any cloud account. | MVP |
| NFR-PORT-002 | Configuration MUST be supplied through environment variables, documented in `.env.example`. | MVP |
| NFR-DOC-001 | Every major architectural decision MUST be recorded as an ADR and indexed in `docs/DECISIONS.md`. | MVP |

## 8. Customer Workflows

**CW-01 — Register and sign in** (FR-AUTH-001 to 007)
1. Guest opens registration, enters email, name and password.
2. System validates input, hashes the password and creates the account.
3. Guest signs in; system creates a session cookie and rotates the ID.
4. Any guest cart is merged into the customer cart.

**CW-02 — Browse and filter** (FR-CAT, FR-SRCH-003 to 007)
1. User selects a category and subcategory.
2. User applies facets (e.g. brand, RAM ≥ 16 GB, price ≤ $1,200).
3. System returns paginated results with facet counts; URL reflects state.
4. User changes sort order and opens a product.

**CW-03 — Search** (FR-SRCH-001, 002, 006)
1. User enters a keyword query, possibly with a typo.
2. System returns relevant results ranked by relevance.
3. User refines with filters.

**CW-04 — Compare products** (FR-CMP)
1. User adds two to four products of the same category to comparison.
2. User opens the comparison and highlights differences.
3. User adds the preferred product to the cart.

**CW-05 — Cart to simulated checkout** (FR-CART, FR-CHK, FR-PAY)
1. Customer reviews the cart; system revalidates price and stock.
2. Customer enters or selects a shipping address and method.
3. System shows the order summary with revalidated prices and availability.
4. Customer selects a simulated payment outcome and confirms.
5. In one transaction, the system checks stock and runs the simulator. On
   approval, stock is decremented and the order becomes `paid`; on decline,
   the order becomes `payment_failed` and stock is unchanged (FR-CHK-007).

**CW-06 — Track an order** (FR-ORD-004, 005)
1. Customer opens order history and selects an order.
2. System shows status, items, totals and the simulated tracking timeline.

**CW-07 — Wishlist** (FR-WISH)
1. Customer saves a product to the wishlist.
2. Later, customer moves it to the cart.

**CW-08 — AI-assisted product discovery** (FR-AI)
1. User asks: "I need a laptop for video editing under $1,500."
2. Assistant extracts structured requirements and queries the catalog
   through authorized tools.
3. Assistant returns recommended products as cards rendered from live
   catalog data, with an explanation of the trade-offs.
4. User asks a follow-up or opens a comparison of the suggestions.

**CW-09 — Manage profile** (FR-PROF-001, 002)
1. Customer updates display name and addresses.

## 9. Administrator Workflows

**AW-01 — Create a product** (FR-ADM-003, 004, 010)
1. Catalog manager creates a draft product in a category.
2. System validates specifications against the attribute schema.
3. Manager uploads or links permitted images and publishes the product.
4. An audit entry is recorded.

**AW-02 — Import products from CSV or JSON** (FR-IMP)
1. Manager uploads a file and runs a dry-run validation.
2. System reports per-row errors and detected duplicates.
3. Manager confirms; an import job runs asynchronously.
4. Manager reviews the job summary (created, updated, skipped, failed).

**AW-03 — Retry a failed job** (FR-IMP-015 to 017)
1. Manager opens import job history and filters by `failed`.
2. Manager inspects the error details and retries the job.
3. System creates a new linked attempt and records the outcome.

**AW-04 — Review price synchronization** (FR-IMP-010 to 013)
1. Manager reviews the latest scheduled price sync run.
2. Manager inspects significant price changes and price history.

**AW-05 — Adjust inventory** (FR-ADM-006, 007)
1. Manager filters low-stock products.
2. Manager records a stock adjustment with a reason.

**AW-06 — Process an order** (FR-ADM-008, FR-ORD-001, 002)
1. Order manager filters `paid` orders.
2. Manager moves the order to `processing` and then `shipped`.

**AW-07 — Investigate an audit trail** (FR-ADM-011)
1. Administrator filters audit logs by actor and time range.
2. Administrator reviews before/after values of a change.

**AW-08 — Triage an incident with DevOps AI** (FR-OPSAI)
1. An alert fires; the DevOps operator opens the DevOps assistant.
2. Assistant summarizes the alert, related logs and recent deployments.
3. Assistant drafts an incident report, suggested remediation and a Jira
   incident draft.
4. Operator reviews, edits and explicitly approves any outward action.

## 10. AI Requirements

### 10.1 Architecture Constraints

- AI modules MUST live inside the backend modular monolith initially.
  `services/ai/` is reserved for future extraction approved by an ADR.
- Orchestration uses LangGraph. Tool exposure uses MCP.
- LLM access MUST go through a provider-independent interface. A mock
  provider MUST be the default for local development and tests.
- Enabling any paid AI API requires explicit project owner approval.
- AI is used only where deterministic logic is insufficient (intent
  parsing, explanation, summarization). Filtering, ranking and pricing
  remain deterministic.

### 10.2 Customer Shopping Assistant (FR-AI)

| ID | Requirement | Scope |
|---|---|---|
| FR-AI-001 | Users MUST be able to search the catalog in natural language. The assistant converts the request into a validated structured query (category, filters, budget, sort). | MVP |
| FR-AI-002 | When AI is disabled or unavailable, natural-language search MUST fall back to keyword search. | MVP |
| FR-AI-003 | The assistant MUST recommend products based on stated budget and requirements, using deterministic filtering and ranking on catalog data. | MVP |
| FR-AI-004 | Every product referenced in a response MUST exist and be active in the catalog; unknown references are discarded before display. | MVP |
| FR-AI-005 | Prices and availability MUST be rendered from live catalog data, never from LLM-generated text. | MVP |
| FR-AI-006 | The assistant MUST explain technical specifications (e.g. "What does 144 Hz mean?") in plain language. | MVP |
| FR-AI-007 | The assistant MUST compare up to four catalog products and explain key differences. | MVP |
| FR-AI-008 | The assistant MUST say when no suitable product exists rather than inventing one. | MVP |
| FR-AI-009 | The assistant MUST refuse requests unrelated to shopping in the store and MUST NOT perform account, order or payment actions. | MVP |
| FR-AI-010 | Conversation state SHOULD persist for the session to support follow-up questions. | MVP |
| FR-AI-011 | Responses SHOULD stream incrementally to the UI. | ADV |
| FR-AI-012 | The assistant MAY use semantic retrieval over product descriptions and specifications. | ADV |

### 10.3 MCP Tools

All tools are read-only and execute with the caller's permissions. Tool
inputs and outputs are schema-validated.

| Tool | Purpose | Caller | Scope |
|---|---|---|---|
| `catalog.search_products` | Structured product search with filters | Customer assistant | MVP |
| `catalog.get_product` | Product details and specifications | Customer assistant | MVP |
| `catalog.compare_products` | Aligned specification comparison | Customer assistant | MVP |
| `catalog.list_categories` | Category tree and attribute schemas | Customer assistant | MVP |
| `inventory.get_availability` | Availability category only (`in_stock`, `low_stock`, `out_of_stock`), never exact counts (FR-CAT-010) | Customer assistant | MVP |
| `inventory.get_stock_levels` | Exact stock levels | Back-office roles | ADV |
| `ops.query_logs` | Read-only, redacted application log queries | DevOps assistant | ADV |
| `ops.get_ci_failures` | Failed CI run details | DevOps assistant | ADV |
| `ops.list_alerts` | Active and recent alerts | DevOps assistant | ADV |
| `ops.draft_jira_incident` | Produce a Jira incident draft (no submission) | DevOps assistant | ADV |

| ID | Requirement | Scope |
|---|---|---|
| FR-AI-020 | MCP tools MUST enforce authorization on the server, independent of the LLM. | MVP |
| FR-AI-021 | MCP tools MUST NOT expose database credentials, raw SQL or write operations. | MVP |
| FR-AI-022 | The MCP server SHOULD be usable from an external MCP client for demonstration, limited to public catalog tools. | ADV |

### 10.4 DevOps AI Assistant (FR-OPSAI)

| ID | Requirement | Scope |
|---|---|---|
| FR-OPSAI-001 | The assistant MUST analyze application logs in read-only mode and summarize errors, frequency and likely causes. | ADV |
| FR-OPSAI-002 | The assistant MUST analyze failed CI/CD runs and identify the failing step and probable cause. | ADV |
| FR-OPSAI-003 | The assistant MUST summarize active infrastructure and application alerts. | ADV |
| FR-OPSAI-004 | The assistant MUST generate a structured incident report (summary, timeline, impact, suspected cause, evidence, next steps). | ADV |
| FR-OPSAI-005 | The assistant MUST propose remediation steps clearly labeled as suggestions; it MUST NOT execute them. | ADV |
| FR-OPSAI-006 | The assistant MUST generate Jira incident drafts; submission to Jira requires explicit human approval. | ADV |
| FR-OPSAI-007 | Any sensitive or destructive action MUST require explicit human approval and MUST be audited. | ADV |
| FR-OPSAI-008 | Log and CI content MUST be redacted of secrets and personal data before being sent to an LLM. | ADV |
| FR-OPSAI-009 | Integrations MUST use read-only, least-privilege credentials. | ADV |

### 10.5 AI Safety and Guardrails

| ID | Requirement | Scope |
|---|---|---|
| NFR-AI-001 | All LLM outputs consumed by code MUST be validated against Pydantic schemas; invalid outputs are retried once and then rejected. | MVP |
| NFR-AI-002 | Imported product text, reviews, logs and tool results MUST be treated as untrusted data and isolated from system instructions (indirect prompt-injection defense). | MVP |
| NFR-AI-003 | The assistant MUST NOT receive customer personal data, credentials or session information. | MVP |
| NFR-AI-004 | Prompts, model, provider, token counts, latency and outcome MUST be logged as metadata without sensitive content. | MVP |
| NFR-AI-005 | A prompt-injection test suite MUST verify the assistant does not follow injected instructions or call unauthorized tools. | MVP |

### 10.6 AI Limits (configurable defaults)

Every limit below is configurable through validated application settings;
the values are initial defaults. Requests exceeding a limit are rejected
or truncated with a clear user-facing message.

| ID | Limit | Default | Scope |
|---|---|---|---|
| NFR-AI-010 | Maximum user message length (configurable) | 2,000 characters | MVP |
| NFR-AI-011 | Maximum tool calls per assistant turn (configurable) | 5 | MVP |
| NFR-AI-012 | LLM request timeout (configurable) | 30 seconds | MVP |
| NFR-AI-013 | Maximum output tokens per response | 800 | MVP |
| NFR-AI-014 | Assistant requests per session per hour | 30 | MVP |
| NFR-AI-015 | Global daily token budget for real providers; requests fall back to non-AI behavior when exhausted | Owner-defined (UD-06) | MVP |
| NFR-AI-016 | Conversation history sent to the model | Last 10 turns | MVP |
| NFR-AI-017 | Limit configuration MUST be validated at startup; invalid values prevent the application from starting rather than silently falling back. | — | MVP |

## 11. Product Data Integration Requirements

### 11.1 Principles

- Prioritize **authorized, free** data sources and comply with their terms,
  rate limits, attribution and licensing requirements.
- **Never** bypass authentication, paywalls, robots directives, CAPTCHAs or
  other access restrictions, and never scrape retailer websites (including
  KSP) without explicit permission.
- **Do not assume** any free API provides complete electronics prices and
  specifications. Expect partial coverage and combine sources.
- Import only product images whose license permits use, and record the
  license and attribution.
- Keep the product domain **provider-independent** through a source adapter
  interface.
- When no external source is available, the system MUST remain fully
  functional with **deterministic demo data**.

Candidate sources (manufacturer or open product catalogs, retailer
developer programs with free tiers, and owner-curated datasets) are
evaluated in a dedicated ADR before integration (UD-03). No candidate is
approved by this PRD.

### 11.2 Functional Requirements (FR-IMP)

| ID | Requirement | Scope |
|---|---|---|
| FR-IMP-001 | Imports MUST go through a source adapter interface (fetch, map, validate) that is independent of any specific provider. | MVP |
| FR-IMP-002 | Authorized users MUST be able to import products from CSV and JSON files using documented schemas. | MVP |
| FR-IMP-003 | Imports MUST support a dry-run mode that validates and reports without writing data. | MVP |
| FR-IMP-004 | Each record MUST be validated (required fields, types, units, category attribute schema, price as non-negative integer cents); invalid rows are reported with row number and reason. | MVP |
| FR-IMP-005 | Imports MUST be idempotent: re-importing the same source records updates existing products rather than duplicating them (upsert by source and external ID). | MVP |
| FR-IMP-006 | Each product MUST record its data source, external identifier and last synchronization timestamp. | MVP |
| FR-IMP-007 | Imports MUST support specifications and permitted images, storing image source URL, license and attribution. | MVP |
| FR-IMP-008 | The system MUST detect duplicates by validated GTIN/EAN/UPC, then normalized brand plus manufacturer part number. | MVP |
| FR-IMP-009 | Probable duplicates detected by normalized title similarity MUST be flagged for manual review, never merged automatically. | ADV |
| FR-IMP-010 | The system MUST record price history for every price change (old price, new price, source, timestamp). | MVP |
| FR-IMP-011 | The system SHOULD run scheduled price updates for sources that provide price data; schedules are disabled by default. | ADV |
| FR-IMP-012 | Price changes exceeding a configurable threshold (e.g. 30%) SHOULD be held for manual approval. | ADV |
| FR-IMP-013 | A deterministic, seeded price simulator SHOULD generate demo price changes, labeled as simulated, to exercise price history when no real price source exists. | ADV |
| FR-IMP-014 | Import and sync jobs MUST run asynchronously with states: queued, running, succeeded, partially_succeeded, failed, cancelled. | MVP |
| FR-IMP-015 | The system MUST keep a job history with timestamps, actor, source, counts (created, updated, skipped, failed) and error details. | MVP |
| FR-IMP-016 | Authorized users MUST be able to retry failed or partially succeeded jobs; each retry creates a new attempt linked to the original. | MVP |
| FR-IMP-017 | Authorized users SHOULD be able to retry only the failed records of a job. | ADV |
| FR-IMP-018 | External source calls MUST use a shared HTTP client with timeouts, per-source rate limits, retries with exponential back-off and jitter, and respect for `Retry-After`. | ADV |
| FR-IMP-019 | External source responses MUST be cached with a configurable TTL to reduce calls. | ADV |
| FR-IMP-020 | Repeated source failures SHOULD open a circuit breaker and surface an alert. | ADV |
| FR-IMP-021 | The system MUST provide a deterministic demo dataset of at least 50 products covering all eight top-level categories, with specifications, prices, stock and reviews. | MVP |
| FR-IMP-022 | Remote image fetching MUST be restricted to allow-listed hosts, block private network addresses, limit size and type, and re-encode images. | ADV |
| FR-IMP-023 | The deterministic demo dataset SHOULD grow to at least 500 products, with realistic subcategory and specification coverage. | ADV |
| FR-IMP-024 | The system MUST provide a deterministic generator for a synthetic performance dataset of 10,000 products (plus synthetic customers and orders per section 14.1). This dataset is used only for performance testing and is never loaded as storefront demo data. | MVP |

## 12. DevOps Requirements (FR-DEV)

### 12.1 Environment Strategy

| Environment | Purpose | Platform | Data | Cost |
|---|---|---|---|---|
| local | Daily development | Docker Compose | Demo seed | Zero cloud cost |
| local-k8s | Kubernetes, Helm and GitOps practice | kind | Demo seed | Zero cloud cost |
| ci | Automated validation | GitHub Actions, ephemeral containers | Test fixtures | Free tier |
| staging | Pre-production verification | AWS (platform per UD-01) | Demo seed | Only with approval; ephemeral |
| production (demo) | Public portfolio demo | AWS (platform per UD-01) | Demo seed | Only with approval; tear down when idle |

The same immutable container images (tagged by Git commit SHA) MUST be
promoted across environments. Environment differences are configuration only.

### 12.2 Requirements

| ID | Requirement | Scope |
|---|---|---|
| FR-DEV-001 | A single documented command MUST start the full local stack (frontend, backend, PostgreSQL, Redis, mail catcher, mock AI). | MVP |
| FR-DEV-002 | The backend and frontend MUST have production-grade Dockerfiles (multi-stage, non-root user, minimal base image, health checks). | MVP |
| FR-DEV-003 | CI MUST run on every pull request: lint, format check, type check, unit and integration tests and coverage report. | MVP |
| FR-DEV-004 | CI MUST run end-to-end tests against a containerized stack. | MVP |
| FR-DEV-005 | CI MUST scan for committed secrets (Gitleaks). | MVP |
| FR-DEV-006 | CI MUST audit dependencies (pip-audit, npm audit) and Dependabot MUST be enabled. | MVP |
| FR-DEV-007 | CI MUST scan container images and IaC (Trivy) and fail on unresolved critical vulnerabilities. | ADV |
| FR-DEV-008 | CI MUST build and publish versioned images only from the main branch. | ADV |
| FR-DEV-009 | All cloud infrastructure MUST be defined in Terraform; CI runs format, validate and plan; apply is manual and requires approval. | ADV |
| FR-DEV-010 | Terraform state MUST be stored remotely with locking and encryption once cloud environments exist. | ADV |
| FR-DEV-011 | The application MUST run on a local kind cluster using Helm charts. | ADV |
| FR-DEV-012 | Helm charts MUST be linted and templated in CI. | ADV |
| FR-DEV-013 | Argo CD MUST deploy from Git (GitOps); manual changes to managed clusters are prohibited. | ADV |
| FR-DEV-014 | AWS deployment MUST occur only after an approved cost estimate (section 15). | ADV |
| FR-DEV-015 | Metrics (Prometheus), dashboards (Grafana), traces (OpenTelemetry) and structured logs MUST be available in local-k8s and cloud environments. | ADV |
| FR-DEV-016 | Alerts MUST exist for: high 5xx error rate, latency above target, failed import jobs, AI provider errors and pod restarts. | ADV |
| FR-DEV-017 | A documented rollback procedure MUST exist for application releases (Argo CD revision or Helm rollback) and be rehearsed. | ADV |
| FR-DEV-018 | Database migrations MUST follow the expand/contract pattern so the previous release remains compatible during rollback. | MVP |
| FR-DEV-019 | Kubernetes workloads MUST define resource requests/limits, liveness/readiness probes and run as non-root. | ADV |
| FR-DEV-020 | Each environment's configuration and secrets MUST be supplied via environment variables locally and a managed secrets service in AWS. | MVP |

## 13. Security Requirements

| ID | Requirement | Scope |
|---|---|---|
| NFR-SEC-001 | Passwords MUST be hashed with Argon2id using recommended parameters. *(Approved in SHOP-002.)* | MVP |
| NFR-SEC-002 | Passwords MUST be 12 to 128 characters with no composition rules; common passwords SHOULD be rejected. *(Approved in SHOP-002.)* | MVP |
| NFR-SEC-003 | Session cookies MUST be `HttpOnly`, `Secure` (outside local HTTP development) and `SameSite=Lax` or stricter. | MVP |
| NFR-SEC-004 | CSRF protection MUST use synchronizer or signed double-submit tokens, plus `Origin` header verification. | MVP |
| NFR-SEC-005 | Authorization MUST be enforced on the server for every endpoint, including object-level checks (customers access only their own orders, carts and profiles). | MVP |
| NFR-SEC-006 | All input MUST be validated with Pydantic schemas; database access MUST use parameterized queries via SQLAlchemy. | MVP |
| NFR-SEC-007 | User-generated and imported content MUST be output-encoded; raw HTML rendering is prohibited. | MVP |
| NFR-SEC-008 | The application MUST send security headers: Content-Security-Policy, HSTS (in TLS environments), X-Content-Type-Options, Referrer-Policy and frame-ancestors restrictions. | MVP |
| NFR-SEC-009 | CORS MUST allow only configured frontend origins with credentials. | MVP |
| NFR-SEC-010 | Error responses MUST NOT expose stack traces or internal details; errors include a correlation ID. | MVP |
| NFR-SEC-011 | Uploaded import files MUST be limited in size (default 10 MB) and type, and parsed safely. | MVP |
| NFR-SEC-012 | CSV exports MUST neutralize spreadsheet formula injection. | MVP |
| NFR-SEC-013 | Secrets MUST never be committed; local secrets come from `.env` (ignored), cloud secrets from a managed secrets service. | MVP |
| NFR-SEC-014 | Logs MUST NOT contain passwords, tokens, session IDs or full personal data. | MVP |
| NFR-SEC-015 | Public endpoints (sign-in, registration, search, assistant) MUST be rate limited. | MVP |
| NFR-SEC-016 | Cloud IAM roles and service credentials MUST follow least privilege. | ADV |
| NFR-SEC-017 | Server-side outbound requests MUST be protected against SSRF (allow-lists, private address blocking). | ADV |
| NFR-SEC-018 | Containers MUST run as non-root with read-only root filesystems where practical. | ADV |
| NFR-SEC-019 | Security-relevant events (sign-in failures, role changes, AI tool denials) MUST be logged and auditable. | MVP |
| NFR-SEC-020 | A security review against the OWASP Top 10 and OWASP Top 10 for LLM Applications MUST be documented in `docs/SECURITY.md` before any public deployment. | ADV |

## 14. Performance and Reliability Targets

Unless stated otherwise, every target is measured using the test
environment and workload defined in section 14.1.

### 14.1 Test Environment and Workload

**Reference environments**

| ID | Environment | Definition | Scope |
|---|---|---|---|
| PE-1 | Local reference | Full Docker Compose stack in production build mode (debug off, `INFO` logging) on a developer machine with at least 4 CPU cores and 16 GB RAM. Container limits: backend 2 vCPU / 2 GB, worker 1 vCPU / 1 GB, PostgreSQL 2 vCPU / 2 GB, Redis 0.5 vCPU / 512 MB, frontend 1 vCPU / 1 GB. The load generator runs on the same host outside these limits. | MVP |
| PE-2 | Staging | The same container images and limits on the approved staging environment (when it exists). | ADV |

**Dataset:** the synthetic performance dataset (FR-IMP-024): 10,000
products across all eight categories, 500 synthetic customer accounts and
5,000 historical orders, generated from a fixed seed.

**API workload profile** (each virtual user repeats a weighted, seeded
random journey; requests go directly to the backend API):

| Operation | Share of requests |
|---|---|
| Category listing with 1–3 facet filters and sorting | 35% |
| Keyword search | 25% |
| Product detail | 20% |
| Cart operations (add, update, view) | 10% |
| Checkout with simulated approved payment | 5% |
| Product comparison | 5% |

**Load model:**

| Parameter | Value |
|---|---|
| Concurrency | 20 constant virtual users (signed-in sessions; checkout uses distinct accounts) |
| Ramp-up / steady state / ramp-down | 1 minute / 10 minutes / 30 seconds |
| Warm-up | 2 minutes before measurement, excluded from results |
| Think time | 1–3 seconds, uniformly distributed, seeded |
| Measurement point | Load generator; p95 latency and error rate computed over the steady state only |
| Error rate | HTTP 5xx responses and timeouts divided by total requests |
| Pass rule | The median of three consecutive runs meets every target |
| Recorded metadata | Hardware, commit SHA, dataset seed and version, container limits |

**Specialized tests:**

- **AI assistant:** 5 constant virtual users for 5 minutes using the mock
  provider and the AI evaluation queries (NFR-PERF-007).
- **Checkout concurrency:** 50 simultaneous purchase attempts for a product
  with 10 units (NFR-REL-001).
- **Frontend:** Lighthouse mobile profile against the production build of
  the home, listing and product pages; median of three runs
  (NFR-PERF-005, NFR-PERF-006).
- **Import throughput:** a 10,000-row valid CSV file processed by one
  worker (NFR-PERF-009).

Load-testing tools are selected by ADR (UD-12).

### 14.2 Performance (NFR-PERF)

| ID | Target | Scope |
|---|---|---|
| NFR-PERF-001 | Catalog listing and search API: p95 ≤ 300 ms | MVP |
| NFR-PERF-002 | Product detail API: p95 ≤ 200 ms | MVP |
| NFR-PERF-003 | Cart and checkout APIs: p95 ≤ 500 ms | MVP |
| NFR-PERF-004 | Server error (5xx) rate under load: < 1% | MVP |
| NFR-PERF-005 | Storefront Core Web Vitals (mobile Lighthouse profile, key pages): LCP ≤ 2.5 s, CLS ≤ 0.1, INP ≤ 200 ms | MVP |
| NFR-PERF-006 | Lighthouse performance ≥ 85 and accessibility ≥ 90 on home, listing and product pages | MVP |
| NFR-PERF-007 | AI assistant with mock provider: end-to-end p95 ≤ 1 s | MVP |
| NFR-PERF-008 | AI assistant with a real provider: first streamed token p95 ≤ 5 s (provider-dependent) | ADV |
| NFR-PERF-009 | CSV import throughput ≥ 1,000 product records per minute | MVP |

### 14.3 Reliability (NFR-REL)

| ID | Target | Scope |
|---|---|---|
| NFR-REL-001 | Concurrent checkouts MUST never oversell: 50 concurrent purchase attempts for 10 units result in exactly 10 successful orders. | MVP |
| NFR-REL-002 | Duplicate order submissions with the same idempotency key MUST produce exactly one order. | MVP |
| NFR-REL-003 | Storefront browsing MUST continue when the AI provider or external data sources are unavailable. | MVP |
| NFR-REL-004 | Background jobs MUST retry transient failures (default 5 attempts, exponential back-off) and then move to `failed`. | MVP |
| NFR-REL-005 | Cloud demo availability target: 99.0% monthly during published demo periods (no SLA). | ADV |
| NFR-REL-006 | Cloud environments: RPO ≤ 24 hours, RTO ≤ 4 hours, with a documented and tested restore procedure. | ADV |
| NFR-REL-007 | Application rollback to the previous release MUST complete within 15 minutes. | ADV |
| NFR-REL-008 | Services MUST shut down gracefully, finishing in-flight requests within a configurable timeout. | MVP |

## 15. Cost Constraints

| ID | Constraint | Scope |
|---|---|---|
| NFR-COST-001 | All features MUST be developable and demonstrable locally at zero cloud cost, using demo data and mock providers. | MVP |
| NFR-COST-002 | No AWS resource may be created without an approved proposal stating purpose, estimated cost, cheaper alternatives and removal procedure (CLAUDE.md section 12). | MVP |
| NFR-COST-003 | Cloud environments MUST be reproducible with Terraform and destroyable when idle. | ADV |
| NFR-COST-004 | Always-on, high fixed-cost resources (e.g. managed Kubernetes control planes, NAT gateways, multi-AZ databases, load balancers) require explicit justification and a cheaper-alternative analysis. | ADV |
| NFR-COST-005 | AWS Budgets alerts MUST be configured before the first deployment, acknowledging they are not spending caps. | ADV |
| NFR-COST-006 | The mock LLM provider is the default; paid AI APIs require explicit approval and a daily token budget (NFR-AI-015). | MVP |
| NFR-COST-007 | Product data MUST come from free, authorized sources or owner-curated files; paid data subscriptions are out of scope. | MVP |
| NFR-COST-008 | No domain purchase by default; use provider-assigned endpoints unless the owner approves a domain. | ADV |
| NFR-COST-009 | CI SHOULD stay within free GitHub Actions capacity, using caching and path filters to limit minutes. | MVP |
| NFR-COST-010 | The monthly AWS budget ceiling MUST be defined by the project owner before any deployment (UD-05). | ADV |

## 16. MVP Scope

The MVP is a complete, locally runnable, tested electronics store with a
grounded AI assistant. It includes every requirement tagged `MVP`,
summarized as:

- **Customer:** registration and session authentication; storefront with
  eight categories and subcategories; keyword search with typo tolerance;
  faceted filtering and sorting; product details and specifications;
  comparison; cart; wishlist; simulated checkout and payments; order
  history and simulated tracking; profile; demo reviews.
- **Admin:** Administrator role; product, category and inventory
  management; order management; customer view (demo data); basic
  dashboard; CSV/JSON import with dry run, job history and retry;
  duplicate detection by identifiers; price history; audit logs.
- **AI:** natural-language search with keyword fallback; budget and
  requirement-based recommendations; specification explanations;
  comparison; read-only catalog MCP tools; mock provider; guardrails and
  limits.
- **Platform components:** internal SDK and integration layer with mocks,
  shared HTTP client, Gatekeeper, background workers, scheduled jobs,
  bounded retries, dead-letter queue, audit logging, feature flags and the
  typed frontend API client (section 6.11).
- **Engineering:** Docker Compose local stack; CI with lint, type checks,
  tests, end-to-end tests, secrets scanning and dependency auditing;
  structured logging and health checks; deterministic demo dataset of at
  least 50 products; synthetic 10,000-product performance dataset.

**MVP exit criteria:** all `MVP` acceptance criteria in section 19 pass.

## 17. Advanced Feature Scope

Delivered after the MVP, in the order defined by `docs/ROADMAP.md`:

- **Identity:** password reset via local mail catcher, admin TOTP MFA,
  session management, fine-grained back-office roles.
- **Commerce:** customer-submitted reviews with moderation, price-drop
  indicators, price history charts, related products, simulated refunds,
  automated tracking progression, account deletion and data export.
- **Catalog and data:** external source adapters, scheduled price
  synchronization, price-change approval, price simulator, fuzzy duplicate
  review, failed-record retry, caching, rate limiting and circuit breakers,
  safe remote image ingestion, autocomplete, semantic search and a demo
  dataset of at least 500 products.
- **Platform components:** Watchdog, Gatekeeper usage reporting,
  notification management and circuit breakers.
- **AI:** response streaming, semantic retrieval, external MCP client
  access, DevOps AI assistant (logs, CI, alerts, incident reports,
  remediation suggestions, Jira drafts).
- **Platform:** image and IaC scanning, image publishing, Terraform,
  kind with Helm, Argo CD GitOps, Prometheus, Grafana and OpenTelemetry,
  alerting, rollback rehearsals, cost-approved AWS staging and demo
  environments.

## 18. Out-of-Scope Features

- Real payments, payment providers, card data handling or PCI DSS scope.
- Real shipping carriers, delivery integrations or address verification.
- Tax calculation; currencies other than USD; languages other than English.
- Real customer data, real email or SMS delivery, and marketing campaigns.
- Scraping of retailer websites or any data collection that violates
  source terms or access controls.
- Use of any retailer's or manufacturer's trademarks beyond factual product
  naming, and any claim of affiliation.
- Paid product data subscriptions.
- Multi-vendor marketplace, B2B pricing, loyalty programs, gift cards,
  coupons and returns logistics.
- Native mobile applications.
- Multi-region high availability and formal SLAs.
- Autonomous AI actions that change data or infrastructure without human
  approval.

## 19. Measurable Acceptance Criteria

Each criterion MUST be verified by an automated test or a documented,
repeatable check.

| ID | Criterion | Verifies | Scope |
|---|---|---|---|
| AC-001 | A guest can register, sign in and sign out; the session cookie has `HttpOnly`, `SameSite` and (in TLS environments) `Secure` attributes. | FR-AUTH-001, 002; NFR-SEC-003 | MVP |
| AC-002 | A state-changing request without a valid CSRF token is rejected with HTTP 403. | FR-AUTH-003 | MVP |
| AC-003 | The sixth failed sign-in attempt within one minute for one account is rate limited. | FR-AUTH-006 | MVP |
| AC-004 | Registration and sign-in responses are identical for existing and non-existing emails. | FR-AUTH-007 | MVP |
| AC-005 | The demo dataset contains ≥ 50 active products covering all eight top-level categories, and seeding twice yields identical data. | FR-CAT-002; FR-IMP-021 | MVP |
| AC-006 | Applying a facet filter returns only matching products, and facet counts equal the actual result counts. | FR-SRCH-003 to 005 | MVP |
| AC-007 | A search with a single-character typo in a product name returns that product in the top 5 results. | FR-SRCH-002 | MVP |
| AC-008 | Reloading a listing URL restores identical filters, sort order and page. | FR-SRCH-007 | MVP |
| AC-009 | Comparison accepts four products of one category and rejects a fifth product or a product from another category. | FR-CMP-001 | MVP |
| AC-010 | Cart totals equal the sum of server-side unit prices × quantities in integer cents; client-supplied prices are ignored. | FR-CART-004 | MVP |
| AC-011 | A guest cart merges into the customer cart on sign-in with no duplicate lines. | FR-CART-003 | MVP |
| AC-012 | Checkout with an "approved" simulated payment produces a `paid` order and decrements stock in the same transaction; "declined" produces `payment_failed` and leaves stock unchanged. | FR-CHK-007; FR-PAY-002 | MVP |
| AC-013 | No page contains an input for a card number or CVV (automated UI check). | FR-PAY-003 | MVP |
| AC-014 | Every payment page displays the simulated-payment notice. | FR-PAY-004 | MVP |
| AC-015 | 50 concurrent purchase attempts for a product with 10 units produce exactly 10 paid orders and zero negative stock. | NFR-REL-001 | MVP |
| AC-016 | Resubmitting an order with the same idempotency key returns the original order. | FR-CHK-005; NFR-REL-002 | MVP |
| AC-017 | Every invalid order state transition is rejected (state machine test covers all pairs). | FR-ORD-001, 002 | MVP |
| AC-018 | A customer receives HTTP 404 when requesting another customer's order. | NFR-SEC-005 | MVP |
| AC-019 | A customer receives HTTP 403 on every back-office endpoint (automated sweep of all admin routes). | FR-ADM-001 | MVP |
| AC-020 | Every back-office write creates exactly one audit log entry with actor, action, target and timestamp, and no secret values. | FR-ADM-010 | MVP |
| AC-021 | A CSV dry run writes no data and reports every invalid row with row number and reason. | FR-IMP-003, 004 | MVP |
| AC-022 | Importing the same file twice creates no duplicate products. | FR-IMP-005 | MVP |
| AC-023 | Products sharing a valid GTIN are detected as duplicates; an invalid GTIN check digit is rejected. | FR-IMP-008 | MVP |
| AC-024 | Retrying a failed job creates a new attempt linked to the original, and both appear in job history. | FR-IMP-015, 016 | MVP |
| AC-025 | Every price change creates one price history record with old price, new price, source and timestamp. | FR-IMP-010 | MVP |
| AC-026 | Importing 10,000 valid records completes at ≥ 1,000 records per minute on reference environment PE-1. | NFR-PERF-009 | MVP |
| AC-027 | The expanded demo dataset contains ≥ 500 active products, and seeding twice yields identical data. | FR-IMP-023 | ADV |
| AC-028 | The performance dataset generator produces exactly 10,000 products, 500 customers and 5,000 orders, identical across runs with the same seed, and never into the demo database. | FR-IMP-024 | MVP |
| AC-029 | No customer-facing API response, page or AI tool output contains an exact stock count (automated contract test). | FR-CAT-010 | MVP |
| AC-030 | Load test following section 14.1 meets NFR-PERF-001 to 004 on PE-1. | NFR-PERF-001 to 004 | MVP |
| AC-031 | Lighthouse (mobile) meets NFR-PERF-005 and 006 on home, listing and product pages. | NFR-PERF-005, 006 | MVP |
| AC-032 | Automated accessibility checks report zero serious or critical violations on all MVP pages. | NFR-ACC-001 | MVP |
| AC-033 | Critical backend business logic modules report ≥ 80% line coverage in CI. | NFR-TST-001 | MVP |
| AC-034 | CI fails when a test, lint, type check, secrets scan or dependency audit fails. | FR-DEV-003, 005, 006 | MVP |
| AC-035 | A fresh clone starts the full local stack with one documented command and no cloud credentials. | FR-DEV-001; NFR-PORT-001 | MVP |
| AC-036 | No log line produced during the full test suite contains a password, session ID or token (automated log scan). | NFR-SEC-014; NFR-PRIV-002 | MVP |
| AC-040 | On an evaluation set of ≥ 30 scripted shopping queries using the mock provider, 100% of referenced products exist and are active. | FR-AI-004 | MVP |
| AC-041 | 100% of displayed prices in assistant responses match catalog prices. | FR-AI-005 | MVP |
| AC-042 | For budget queries, 100% of recommended products are within the stated budget. | FR-AI-003 | MVP |
| AC-043 | On a prompt-injection suite of ≥ 20 cases (direct and via product data), the assistant calls no unauthorized tool and reveals no system instructions. | NFR-AI-002, 005; FR-AI-020 | MVP |
| AC-044 | With the AI provider disabled, natural-language search falls back to keyword search and the storefront remains fully functional. | FR-AI-002; NFR-REL-003 | MVP |
| AC-045 | Limits NFR-AI-010 to 014 are enforced with default values, changing a configured value changes enforcement without code changes, and invalid configuration prevents startup. | NFR-AI-010 to 017 | MVP |
| AC-046 | When Gatekeeper reports an exhausted quota or token budget, the request receives the defined fallback and no provider call is made. | FR-PLAT-004 | MVP |
| AC-047 | A job exhausting its retries appears in the dead-letter queue with attempt history; retrying or discarding it creates an audit entry. | FR-PLAT-009, 014; FR-PLAT-011 | MVP |
| AC-048 | CI fails when the generated frontend API types differ from the current OpenAPI specification. | FR-PLAT-015 | MVP |
| AC-049 | Every integration port has a mock implementation, and the full automated test suite runs with no outbound network access. | FR-PLAT-001, 002; NFR-TST-002 | MVP |
| AC-050 | The DevOps assistant produces a schema-valid incident report from a recorded incident fixture, and no outward action occurs without approval. | FR-OPSAI-004 to 007 | ADV |
| AC-051 | Secrets planted in log fixtures are redacted before any LLM call. | FR-OPSAI-008 | ADV |
| AC-052 | The application deploys to kind via Helm and Argo CD from Git with all pods ready. | FR-DEV-011, 013 | ADV |
| AC-053 | A rollback to the previous release completes within 15 minutes and is documented. | FR-DEV-017; NFR-REL-007 | ADV |
| AC-054 | Image scans report zero unresolved critical vulnerabilities for released images. | FR-DEV-007 | ADV |
| AC-055 | `terraform plan` runs in CI without applying, and every cloud environment has an approved cost estimate on record. | FR-DEV-009, 014 | ADV |
| AC-056 | Alerts fire in a controlled test for each condition in FR-DEV-016. | FR-DEV-016 | ADV |

## 20. Risks, Assumptions and Unresolved Decisions

### 20.1 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | No free source provides complete electronics specifications and prices | High | High | Provider-independent adapters, CSV/JSON fallback, deterministic demo data, price simulator |
| R-02 | Product image licensing is unclear or restrictive | High | Medium | Record license per image; use placeholders when rights are unclear |
| R-03 | Source terms, rate limits or availability change | Medium | Medium | Adapter isolation, caching, circuit breakers, demo-data fallback |
| R-04 | AWS costs exceed expectations | Medium | High | Approval gate, cost estimates, ephemeral environments, budget alerts, teardown procedures |
| R-05 | LLM API costs or rate limits | Medium | Medium | Mock provider default, token budgets, deterministic logic first |
| R-06 | Prompt injection through imported product data or logs | Medium | High | Untrusted-content isolation, read-only tools, server-side authorization, injection test suite |
| R-07 | AI hallucinates products, prices or specifications | Medium | High | Reference validation, prices rendered from database, evaluation suite |
| R-08 | Scope is too large for a single developer | High | High | Strict MVP/ADV separation, incremental roadmap, milestone approvals |
| R-09 | Local resources insufficient for full stack plus kind and observability | Medium | Medium | Compose profiles, optional components, documented minimum hardware |
| R-10 | Vulnerable dependencies | Medium | Medium | Dependabot, pip-audit, npm audit, Trivy |
| R-11 | Perceived affiliation with or trademark misuse of real retailers | Low | High | No retailer branding; clear non-commercial disclaimer |
| R-12 | Next.js hosting model conflicts with low-cost static hosting | Medium | Medium | Decide hosting model by ADR (UD-02) |
| R-13 | Platform components (Gatekeeper, Watchdog, workers, flags) become over-engineered custom code | Medium | Medium | Reuse framework and infrastructure capabilities first; ADR required for custom implementations (FR-PLAT-016) |

### 20.2 Assumptions

| ID | Assumption |
|---|---|
| A-01 | The project is developed primarily by a single engineer, the project owner. |
| A-02 | The UI is English-only with `en-US` USD formatting. |
| A-03 | Synthetic demo data is acceptable for customers, orders and reviews. |
| A-04 | GitHub Actions free capacity is sufficient for CI. |
| A-05 | A Jira project `eShop_AI` with the `ESHOP` key is available for task tracking. Jira generates its own `ESHOP-N` issue keys. Roadmap task IDs (`SHOP-NNN`) remain the permanent identifiers and are mapped to Jira keys in `docs/jira/issue-map.csv`. |
| A-06 | The developer machine can run Docker Compose (and kind for advanced milestones). |
| A-07 | At least one free, authorized product data source can be identified; if not, the system relies on owner-curated files and demo data. |

### 20.3 Unresolved Decisions

All items remain **deferred**. Each requires an ADR or explicit project
owner decision before the milestone that depends on it (mapped in
`docs/ROADMAP.md`).

| ID | Decision | Options under consideration | Needed by |
|---|---|---|---|
| UD-01 | AWS container platform | ECS on Fargate, ECS on EC2, EKS, single EC2 with k3s/Docker | Before cloud deployment |
| UD-02 | Frontend hosting model | Next.js server in a container; static export to S3 + CloudFront; hybrid | Before frontend deployment |
| UD-03 | Authorized product data sources | Open product catalogs, manufacturer data, retailer developer programs, owner-curated CSV/JSON | Before external imports |
| UD-04 | Background job runner | Library-based worker on Redis; PostgreSQL-backed queue; scheduler library | Before import implementation |
| UD-05 | Monthly AWS budget ceiling | Owner-defined amount | Before cloud deployment |
| UD-06 | LLM providers and daily token budget | Commercial API(s), local open-weight model runtime, mock only | Before enabling a real provider |
| UD-07 | Search implementation | PostgreSQL full-text + trigram; pgvector for semantic search; dedicated search engine | Before catalog search implementation |
| UD-08 | Session store | Redis; PostgreSQL | Before authentication implementation |
| UD-09 | Local and cloud object storage for images | Filesystem, S3-compatible local storage, Amazon S3 | Before image import |
| UD-10 | MCP transport and external exposure | In-process only; stdio for local clients; HTTP transport with authentication | Before MCP implementation |
| UD-11 | Repository visibility | Public; private until MVP | Before first push |
| UD-12 | Load-testing and end-to-end testing tools | To be selected by ADR | Before performance and E2E testing |
| UD-13 | Feature flag implementation | Typed settings only; database-backed flags; OpenFeature-compatible library | Before feature flag implementation |
| UD-14 | OpenAPI-to-TypeScript generator | To be selected by ADR | Before typed API client implementation |
| UD-15 | Local mail catcher for notifications | To be selected by ADR | Before notification implementation |

## Glossary

| Term | Definition |
|---|---|
| ADR | Architecture Decision Record, stored in `docs/adr/` |
| Availability category | Customer-facing stock indicator: `in_stock`, `low_stock` or `out_of_stock` |
| Dead-letter queue (DLQ) | Holding area for jobs that exhausted their retries |
| Facet | A filter dimension with result counts |
| Feature flag | Configuration switch that enables or disables a capability at runtime |
| Gatekeeper | Component enforcing rate limits, API quotas and AI token budgets |
| GTIN | Global Trade Item Number (includes EAN-13 and UPC-A) |
| Grounding | Restricting AI output to verified catalog data |
| MCP | Model Context Protocol, used to expose tools to AI agents |
| MPN | Manufacturer Part Number |
| RPO / RTO | Recovery Point Objective / Recovery Time Objective |
| Simulated payment | An internal, deterministic payment outcome with no real transaction |
| Watchdog | Component that aggregates health signals and detects failures without remediating |

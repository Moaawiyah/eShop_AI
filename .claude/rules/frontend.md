---
paths:
  - "frontend/**"
---

# Frontend Rules

## Tooling
- Node.js: a currently supported LTS release, pinned (`.nvmrc` and
  `engines`) when the frontend is initialized.
- npm with a committed `package-lock.json`; CI uses `npm ci`.
- Next.js with React and TypeScript in strict mode.
- ESLint and Prettier; never disable a rule without a justification comment.
- Tailwind CSS and shadcn/ui.

## TypeScript
- Avoid `any` unless explicitly justified in a comment.
- Prefer explicit types at module boundaries and for component props.

## API Access
- Access the backend only through the single typed API client.
- Generate API types from the FastAPI OpenAPI specification; never
  hand-write duplicate request or response types.
- The client sends credentials (session cookie), attaches the CSRF token
  and normalizes errors.
- The server is authoritative for prices, totals, stock and permissions.

## UI and Accessibility
- Build reusable, accessible components; target WCAG 2.2 AA.
- All interactive elements are keyboard operable with visible focus.
- Responsive from 360 px to 1920 px.
- Design loading, empty and error states for every data-driven view.
- Meet performance budgets in PRD NFR-PERF-005 and NFR-PERF-006.

## Domain Display
- Format money from integer cents with one shared `en-US` USD formatter.
- English-only UI; no tax calculation is displayed.
- Show availability categories only, never exact stock counts.
- Show the simulated-payment notice on every payment page; never render
  inputs for card numbers, CVV or bank details.

## Security
- Never use `dangerouslySetInnerHTML` for user-generated or imported content.
- Never expose secrets in client bundles; only intentionally public
  configuration may use the `NEXT_PUBLIC_` prefix.

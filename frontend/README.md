# eShop_AI frontend

Next.js (App Router, `src/`), React, strict TypeScript, Tailwind CSS v4 and
shadcn/ui. Requires Node.js 26 (`.nvmrc`).

```bash
npm ci               # install locked dependencies
npm run dev          # http://localhost:3000
npm run lint         # ESLint, zero warnings
npm run format:check # Prettier (npm run format to fix)
npm run typecheck    # tsc --noEmit
npm test             # Vitest + Testing Library (jsdom)
npm run build        # production build (standalone output)
```

Notes:

- `output: "standalone"` means production is started with
  `node .next/standalone/server.js` (copy `.next/static` and `public` beside
  it); the container image is added in SHOP-122.
- Design tokens (light and dark) live in `src/app/globals.css`.
- shadcn/ui primitives in `src/components/ui/` are generated; add more with
  `npx shadcn@latest add <component>`.

See `docs/DEVELOPMENT.md` and `docs/ARCHITECTURE.md` section 6.

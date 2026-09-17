# BRAHMO Rules Engine — frontend

Next.js 16 · React 19 · Tailwind 4. Visualises the pipeline; holds no pipeline
logic of its own.

```bash
npm install
npm run dev     # → http://localhost:3000
```

Expects the API at `http://localhost:8000`. Override with `NEXT_PUBLIC_API_URL`
in `.env.local` — it is read once in `src/lib/api.ts` and inlined at build time,
so a deployed build needs the variable set *before* it is built, not after.

## Tests

```bash
npm run test:unit   # 37 component tests — Vitest + Testing Library, mocked payloads
npm run test:e2e    # 23 browser specs — Playwright
npm test            # both
```

The Playwright config starts uvicorn on 8000 and Next on 3001 itself, reusing
them if they are already running, so the e2e suite needs no second terminal.

See the root [README](../README.md) for deployment and
[docs/architecture.md](../docs/architecture.md) for the design.

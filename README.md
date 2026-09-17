# BRAHMO Rules Engine — BFS Traversal + 5-Check Filter Pipeline

Takes a graph of 50 knowledge nodes and filters it to the candidate set for one
specific user: their department, their authority, their clearance, right now.
**Zero LLM calls.** Deterministic, sub-millisecond, auditable.

```
Nurse Priya   (VIEWER,  L10, ortho)     50 nodes  →  13
Dr. Vikram    (HOD,     L4,  ortho)     50 nodes  →  22
Admin Suresh  (ADMIN,   L1,  hospital)  50 nodes  →  42
```

Same graph. Same code path. Three different answers, and Priya's set contains
zero Cardiology nodes, zero MNPI-tagged nodes, zero superseded protocols and
zero facts the model already knows — while still containing the hospital-wide
"never give NSAIDs to a patient on Warfarin" constraint and her own patient's
contraindication.

---

## Quick start (60 seconds, no accounts, no keys, $0)

```bash
git clone <this repo> && cd brahmo-rules-engine

python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt

python -m backend.verify          # prints the acceptance table for all 7 users
pytest backend/tests -q           # 67 tests
uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend && npm install && npm run dev     # → http://localhost:3000
```

The backend runs against Supabase when `SUPABASE_URL` / `SUPABASE_KEY` are set,
and otherwise parses `supabase/seed.sql` into memory. Both paths run exactly the
same pipeline — `GET /api/health` reports which one is live.

<details>
<summary>Windows (PowerShell)</summary>

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m backend.verify
uvicorn backend.main:app --reload --port 8000
```
</details>

## Optional: run it against Supabase

1. Create a free project at [supabase.com](https://supabase.com).
2. SQL Editor → run `supabase/schema.sql`, then `supabase/seed.sql`.
3. Verify: `SELECT COUNT(*) FROM knowledge_nodes;` → 50, `FROM users;` → 7.
4. `cp .env.example .env`, fill in Project URL + anon key, restart uvicorn.

`GET /api/health` should now report `"backend": "supabase"`. Every test and the
verify script pass identically against either backend.

---

## What it does

```
user_id
   |
[0] Permission Compiler ..... once per session → {level: {read, write}}  O(1)
[1] Entry Point Resolver .... department → the DAG level the user stands on
[2] BFS Traversal ........... up through parents, down only within the
   |                          user's own department; visited set makes the
   |                          multi-parent DAG safe
[3] Zone 2 Injection ........ hospital-wide safety nodes, path-independent,
   |                          injected BEFORE the checks so they are still filtered
[4] Five Sequential Checks .. isolation → compliance → permission
   |                          → temporal → derivability
[5] Candidate Set Assembler . fetch content for SURVIVORS ONLY, annotate
   v
candidate set (type, importance, distance, zone, compression_hint)
```

The design decisions, the two judgement calls, and the one place the spec
contradicts itself are written up in **[docs/architecture.md](docs/architecture.md)**.

---

## Verify it yourself

```
$ python -m backend.verify

USER            ROLE     ENTRY POINT     BFS  +Z2   C1   C2   C3   C4   C5  FINAL   ms
--------------------------------------------------------------------------------------
Nurse Priya     VIEWER   HL-10-ORTHO-W    20   30   30   25   15   15   13     13   0.3
Dr. Vikram (HOD HOD      HL-05-ORTHO      20   30   30   26   26   26   22     22   0.3
Dr. Ananya      EDITOR   HL-08-MED-GEN    13   23   23   20   13   13   11     11   0.2
Dr. Sharma (HOD HOD      HL-05-MED        13   23   23   20   20   19   15     15   0.2
Pharmacist Ravi VIEWER   HL-01            50   50   50   44   13   13   11     11   0.3
Dr. Sunita (QA) QUALITY  HL-01            50   50   50   45   24   24   22     22   0.3
Admin Suresh    ADMIN    HL-01            50   50   50   50   50   49   42     42   0.3

  [PASS] Priya: no other-department nodes
  [PASS] Priya: no MNPI nodes
  [PASS] Priya: no superseded nodes
  [PASS] Priya: no derivable nodes
  [PASS] Priya: global drug safety present
  [PASS] Priya: patient constraint present
```

All seven seeded users run through the same code — including Ravi, Sunita and
Sharma, who are not in the demo script. None of them is special-cased.

---

## API

| endpoint | returns |
|---|---|
| `GET /api/health` | backend in use, node/user counts, `llm_calls: 0` |
| `GET /api/users` | the 7 seeded users |
| `GET /api/graph` | hierarchy DAG + a content-free node index + typed edges |
| `GET /api/pipeline/{user_id}` | a full run: funnel, per-stage timings, per-check SQL, exclusions, candidate set |
| `GET /api/compare?users=a,b,c` | 2–4 independent runs + shared / exclusive node ids |

Nothing is cached. Switching users in the UI re-executes BFS and all five checks.

<details>
<summary>Sample response (trimmed)</summary>

```json
{
  "user": "U-PRIYA",
  "role": "VIEWER",
  "ceiling_level": 10,
  "entry_point": "HL-10-ORTHO-W",
  "pipeline_timing": { "bfs_ms": 0.031, "check2_compliance_ms": 0.014, "total_ms": 0.284 },
  "funnel": {
    "total_nodes": 50, "after_bfs": 20, "after_zone2": 30,
    "after_check1": 30, "after_check2": 25, "after_check3": 15,
    "after_check4": 15, "after_check5": 13, "candidate_set": 13
  },
  "llm_calls": 0,
  "candidate_set": [
    {
      "id": "N-O14",
      "type": "CONSTRAINT",
      "title": "Patient Rajan: Absolute NSAID Contraindication",
      "importance": 0.99,
      "hierarchy_level": 12,
      "distance_from_entry": 1,
      "compression_hint": "FULL",
      "reached_via": "BFS"
    },
    {
      "id": "N-G01",
      "type": "CONSTRAINT",
      "title": "Warfarin-NSAID Interaction",
      "importance": 0.98,
      "hierarchy_level": 3,
      "distance_from_entry": 4,
      "compression_hint": "CONSTRAINT_ONLY",
      "reached_via": "ZONE_2_INJECTION"
    }
  ]
}
```
</details>

---

## The UI

* **Stage cards** — 50 → BFS → +Zone 2 → candidate set.
* **Filter funnel** — a bar per stage; click any check to see the SQL predicate
  it is equivalent to and the exact nodes it removed, with reasons.
* **Timing panel** — per-stage milliseconds against the 500 ms budget, plus
  levels reached, revisits prevented, and the LLM call count (0).
* **DAG viewer** — the whole hierarchy, marking the entry point, reached levels
  with their distance, unreachable levels, Zone 2, and the multi-parent edge.
* **Candidate table** — grouped by type, with level, distance, importance and
  compression hint; click a row for the content.
* **Comparison** — 2–4 users side by side with shared and exclusive node ids.

Exclusions appear only in the demo's audit panel. The end user never sees an
error, a redaction marker, or an "access denied" — a filtered node simply does
not exist from where they are standing.

---

## Deployment

Two Vercel projects are live. **The UI is the first one** — the backend URL
serves JSON only and will look broken in a browser.

| | URL | serves |
|---|---|---|
| UI | https://brahmo-rules-engine-live-07c4.vercel.app | the Next.js app — start here |
| API | https://backend-live-07c4.vercel.app | FastAPI; every route returns JSON |

The root `vercel.json` uses Vercel's `services` preset to build the Next.js
frontend and the FastAPI backend from this one repo. `backend/` also deploys
standalone as its own project, and that standalone API is what the deployed UI
calls.

```bash
vercel deploy --prod --project brahmo-rules-engine   # UI, from the repo root
cd backend && vercel deploy --prod                   # the standalone API
```

### Two settings the deployment will not work without

**`NEXT_PUBLIC_API_URL`** must be set on the *frontend* project for Production
and Preview, pointing at the API. Next.js inlines `NEXT_PUBLIC_*` at build time,
so setting the variable is not enough on its own — the project has to be
redeployed before the change reaches the browser. Unset, the client falls back
to `http://localhost:8000` and every fetch hits the *visitor's* machine.

**Vercel Authentication must be off** on the frontend project. While it is on,
anonymous visitors are redirected to a Vercel login instead of the app, so the
UI looks like it was never deployed even though it builds and renders fine:

```bash
vercel project protection brahmo-rules-engine               # show current state
vercel project protection disable --sso brahmo-rules-engine
```

`SUPABASE_URL` / `SUPABASE_KEY` stay optional in production exactly as they are
locally: unset, or left at their `your_…` placeholders, the deployed API parses
the bundled seed. `GET /api/health` reports which backend is live. Set
`CORS_ORIGINS` to pin the API's allowed origins; unset means any origin.

One Vercel detail worth knowing: the per-build URLs (`…-<hash>-….vercel.app`)
are immutable and permanently serve the build that created them. Promoting a new
deployment moves the aliases above, not those. Always test the alias.

---

## Layout

```
backend/
  pipeline/      permission_compiler · entry_point_resolver · bfs_traversal
                 zone2_injector · five_check_filter · candidate_assembler · engine
  data/          repository (Supabase | local seed) · sql_seed_parser · seed.sql
  models/        user · node · candidate_set
  tests/         67 tests
  api/index.py   Vercel entrypoint
  main.py        FastAPI
  verify.py      the acceptance table above
frontend/
  src/           Next.js 16 · React 19 · Tailwind 4
  src/__tests__/ 37 component tests (Vitest)
  e2e/           23 browser specs (Playwright)
supabase/        schema.sql · seed.sql
docs/            architecture.md
vercel.json      Vercel `services` preset — builds frontend and backend together
```

`backend/data/seed.sql` is a byte-identical copy of `supabase/seed.sql`, vendored
so the standalone backend deployment has the seed inside its own bundle. The two
must stay in sync; `supabase/seed.sql` is the original.

## Tests

```bash
pytest backend/tests -q            # 67 passed
cd frontend && npm run test:unit   # 37 passed — Vitest + Testing Library
cd frontend && npm run test:e2e    # 23 passed — Playwright
```

`npm test` in `frontend/` runs both JS suites. The Playwright config starts
uvicorn on 8000 and Next on 3001 itself, reusing them if they are already up, so
the e2e run needs no separate terminal.

The backend tests cover the guarantees rather than the implementation: upward
traversal, department-scoped descent, multi-parent processed exactly once,
each check's responsibility, the sequential contract (an excluded node is never
evaluated again), monotonic funnels for all seven users, determinism, and that
content is fetched **only** for nodes that survived all five checks.

Two suites guard the edges of the system:

* `test_seed_integrity.py` enforces every constraint `schema.sql` declares —
  foreign keys, CHECK domains, numeric ranges, acyclicity, one root, no orphans
  — so a broken seed fails here rather than in the Supabase SQL editor.
* `test_frontend_contract.py` pins the JSON shape `frontend/src/lib/types.ts`
  declares. `tsc` checks the components against those types; this checks the
  types against the live API.

### One fix to the provided schema

The spec's `hierarchy_levels` table declares
`UNIQUE(org_id, level_number, department)`. That constraint **rejects the
provided seed**: Orthopaedics has three level-8 units — Ortho General, Ortho TKR
Unit and the Post-TKR Protocol Area — so `schema.sql` and `seed.sql` cannot both
run as given. It is removed, with the reasoning in a comment at the
constraint's old location; `id` already guarantees uniqueness, and one-unit-per-
(department, depth) would forbid exactly the multi-unit, multi-parent shape this
DAG exists to model. `test_seed_integrity.py` asserts the collision still exists
in the seed and that the constraint has not come back.

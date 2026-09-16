# BRAHMO Rules Engine — Architecture

> BFS traversal + 5-check filter pipeline. 50 knowledge nodes in, 11–42 out,
> depending entirely on who is asking. **Zero LLM calls anywhere in this layer.**

---

## 1. The shape of the thing

```
user_id
   |
   v
[0] Permission Compiler ....... once per session -> {level: {read, write}}  O(1)
   |
[1] Entry Point Resolver ...... department -> the DAG level the user stands on
   |
[2] BFS Traversal ............. structural reach: which levels can they inherit?
   |
[3] Zone 2 Injection .......... hospital-wide safety nodes, path-independent
   |
[4] Five Sequential Checks .... isolation -> compliance -> permission
   |                            -> temporal -> derivability
   v
[5] Candidate Set Assembler ... fetch content for SURVIVORS ONLY, annotate
```

Two properties hold at every stage:

* **Deterministic.** Same inputs, same output, every time. No scoring model, no
  embedding, no LLM. `test_pipeline_is_deterministic` asserts it.
* **ID-only until the end.** Stages 1–4 move node *identifiers* around. Content
  is loaded once, in stage 5, for nodes that already passed all five checks.

---

## 2. Separation of structure and policy

This is the central design decision, and everything else follows from it.

| | asks | implemented by | user-specific? |
|---|---|---|---|
| **Structure** | "where in the graph does this user stand, and what does that position inherit?" | BFS | by department |
| **Policy** | "of what they can reach, what may they actually read?" | 5 checks | by role, ceiling, clearance |

Priya and Vikram are both in Orthopaedics, so their **traversals are identical**
— 9 levels, 20 nodes. Their candidate sets are 13 and 22 nodes and differ in
kind, not just size. All of that difference is produced by the checks. Mixing
policy into the traversal would have hidden it, and would have meant re-walking
the graph whenever a permission changed.

---

## 3. Stage notes

### [0] Permission Compiler — `pipeline/permission_compiler.py`

Compiles a user row into a 15-entry dict, once, at session start. Every later
permission question is one dict lookup rather than a policy evaluation. For a
50-node graph this is irrelevant; at Supra's real 842 nodes it is the difference
between 842 rule evaluations and 842 hash lookups, and the compile cost is paid
once.

**Ceiling semantics: a *lower* number is *more* authority.** Level 1 is the
hospital board, level 12 is a single patient. `can_read(level) = level >= ceiling`,
so a user reads their own stratum and everything more granular, never anything
more strategic. The seed data confirms this reading: Dr. Sunita (QA) has
`ceiling_level 6` and `write_ceiling 8` — she can read more broadly than she can
write, which only makes sense if higher numbers are narrower.

| role | reads | writes |
|---|---|---|
| VIEWER | `>= ceiling` | nothing |
| EDITOR | `>= ceiling` | `>= write_ceiling` |
| QUALITY / AUDITOR | `>= ceiling` | `>= write_ceiling` |
| HOD | all levels | `>= ceiling` |
| ADMIN | all levels | all levels |

### [1] Entry Point Resolver — `pipeline/entry_point_resolver.py`

Of the levels belonging to the user's department, enter at the **shallowest one
the user may read**.

* Priya (ortho, ceiling 10) → levels 10 and 12 qualify → **L10 Ortho Ward**
* Vikram (ortho, ceiling 4) → every ortho level qualifies → **L5 Orthopaedics**

Three of the seven seeded users — Admin Suresh, QA Sunita, Pharmacist Ravi —
have departments (`admin`, `quality`, `pharmacy`) with no hierarchy level at
all. Rather than special-casing each, they are treated as **cross-departmental**:
they enter at the org root and descend without a department restriction, and
their ceiling alone decides what they read. This is why Ravi (VIEWER, ceiling 12)
reaches all 50 nodes and keeps 11 — patient-level medication facts plus global
drug safety, which is exactly a pharmacist's remit. Handling these three by rule
rather than by exception is what makes "try a user not in your demos" work.

### [2] BFS Traversal — `pipeline/bfs_traversal.py`

One FIFO queue, one visited set, two movement rules:

* **Up** (`child -> parent_ids`) — always. Walking up is *how* a ward inherits
  its department's, division's and hospital's context.
* **Down** (`parent -> child`) — only into the user's own department subtree.

The downward rule is load-bearing. Without it "up then down" makes the DAG
effectively undirected, every user reaches the root, and from the root reaches
Cardiology — total isolation failure. With it, Priya reaches sibling ortho units
(TKR Unit, Post-TKR) but never Medicine, Cardiology, Paediatrics or ICU.

**Multi-parent handling.** `HL-08-POST-TKR` has `parent_ids = [HL-05-ORTHO,
HL-05-SURG]`. It is enqueued from whichever path reaches it first and the
visited set drops every later arrival — processed exactly once, asserted by
`test_multi_parent_node_is_processed_exactly_once`. The second parent is not
merely deduplicated, it *widens* reach: `HL-05-SURG` is reachable by an ortho
nurse **only** through that edge, and the traversal result reports
`revisits_prevented` (8 for Priya) so the demo can show the visited set working.

Distance is hop count from the entry point, and is what drives compression later.

### [3] Zone 2 Injection — `pipeline/zone2_injector.py`

Ten hospital-wide nodes (Warfarin–NSAID interaction, two-person transfusion
verification, patient-ID rules…) are injected into the reachable set regardless
of traversal path.

**Injected before the checks, never after.** They are ordinary candidates from
that point on: `N-G04` (hand hygiene, derivability 0.75) and `N-G06` (two-
identifier rule, 0.80) are injected for every user and then dropped by check 5,
because a model already knows them. Injecting after the checks would have been a
back door around compliance and temporal validity.

Injected nodes have no traversal distance, so they are assigned the distance
from entry to the traversal's furthest point — they are the most distant context
the user has, which gives them the `CONSTRAINT_ONLY` compression treatment:
keep the rule, drop the prose.

### [4] The five checks — `pipeline/five_check_filter.py`

Sequential, each taking the previous check's survivors:

| # | check | predicate | purpose |
|---|---|---|---|
| 1 | ISOLATION | `org_id = :org` | tenant boundary |
| 2 | COMPLIANCE | `NOT (compliance_tags && :blocked_tags)` | clearance |
| 3 | PERMISSION | `hierarchy_level >= :ceiling OR zone = 2` | authority |
| 4 | TEMPORAL | `status NOT IN ('SUPERSEDED','EXPIRED') AND (valid_until IS NULL OR valid_until > NOW())` | currency |
| 5 | DERIVABILITY | `derivability_score < :threshold` | token economy |

**Why this order.** It is cheapest-and-most-absolute first. A node from another
tenant must never be compliance-evaluated; a node the user has no clearance for
must never be permission-evaluated, temporally evaluated, or scored. Each check
is a narrowing of the previous result set, so nothing downstream can resurrect an
exclusion — asserted by `test_an_excluded_node_never_reaches_a_later_check`.
Derivability is last on purpose: it is the only check that is a *quality*
judgement rather than a *security* one, and quality judgements are never allowed
to run before security ones.

Each check also carries the SQL predicate it is the in-process equivalent of,
and the API returns it, so the UI can show these are `WHERE` clauses rather than
application-side post-filtering.

#### Two decisions worth arguing about

**(a) Zone 2 nodes bypass the ceiling in check 3.**
They are subject to checks 1, 2, 4 and 5 but not the level ceiling. Applying it
would put "never prescribe NSAIDs to a patient on Warfarin" — authored at L3 —
above the ceiling of every ward nurse in the hospital, which is precisely the
failure this system exists to prevent. The assessment's own sample output shows
`N-G01` in Priya's candidate set at `hierarchy_level 3` with her ceiling at 10,
which only holds under this reading. It is a single flag on the compiled
permissions (`zone2_bypasses_ceiling`), so an org that disagrees can turn it off.

**(b) HOD compliance clearance is scoped to their own department.**
Vikram has no explicit `compliance_clearance`, yet the expected results require
that he sees `N-O11` (his own department's budget, tagged MNPI) and not `N-O12`
(tagged MNPI **and** CONFIDENTIAL). So an HOD carries implicit MNPI clearance
**for nodes in their own department only** — he authored that budget; Cardiology's
budget stays blocked. CONFIDENTIAL is never implicit, which is what separates
the two nodes. One table in `permission_compiler.py` (`_ROLE_SCOPED_CLEARANCE`)
holds this, and `blocking_tags()` applies it only when `node.department ==
user.department`.

#### The ambiguity in check 3, and how it is handled

The spec states check 3 as `hierarchy_level >= user.ceiling_level`, and states
"Nurse at L10 can't see L4 HOD decisions". Taken literally, Priya also loses
`N-O02` (Paracetamol post-TKR, L8) — while the spec's illustrative JSON shows
exactly that node in her set. The two cannot both be true.

The literal rule is the default here, because it is the rule as written, it is
the conservative direction for a security boundary, and it is what produces the
differentiation the assessment asks for:

| policy | Priya | Vikram | Suresh |
|---|---|---|---|
| **literal ceiling (default)** | **13** | **22** | **42** |
| `PERMISSION_INHERIT_DEPT_PATH=1` | 21 | 22 | 42 |

The alternative reading — that own-department levels on your traversal path are
*inherited* authority — is implemented and one environment variable away. It is
not the default because it collapses Priya and Vikram to 21 vs 22 nodes, and
"Priya and her HOD see the same thing" is the exact failure mode the assessment
calls broken.

### [5] Candidate Set Assembler — `pipeline/candidate_assembler.py`

The first and only place content is read. Survivors are annotated with type,
importance, zone, distance, and a compression hint derived from distance
(`0–1 FULL`, `2 COMPRESSED`, `3+ CONSTRAINT_ONLY`), then ranked by importance,
then proximity, then id, and capped at the org's `max_candidate_set`.

The output is a candidate set, not a prompt. Compressing and assembling it is
the downstream Composition Agent's job and is out of scope here.

---

## 4. GAP 5 — permission before retrieval

The repository exposes two calls, and the split is the point:

```python
load_filter_index(org_id)   # id, level, zone, status, tags, derivability — NO content
fetch_content(survivor_ids) # content, for nodes that already passed all 5 checks
```

A node the user may not read never has its content in process memory.
`test_content_is_fetched_only_for_survivors` spies on the repository and asserts
that the requested ids are exactly the candidate set — `N-O11` (MNPI, dropped at
check 2) is never fetched.

Against Supabase this is literally a narrower `select=` on the first query and an
`in_('id', ...)` on the second. The next step, not taken here, is pushing checks
1/2/4/5 into the first query as PostgREST filters and check 3 into a Postgres RLS
policy, so the rows never leave the database — which is why every check carries
its SQL predicate rather than only a Python closure.

---

## 5. Data access

| backend | when | why |
|---|---|---|
| `LocalSeedRepository` | default | parses `supabase/seed.sql` into memory — the demo runs with no keys, no network, $0 |
| `SupabaseRepository` | `SUPABASE_URL` + `SUPABASE_KEY` set | PostgREST over Postgres |

The local backend parses *the same SQL file Supabase executes*, so there is one
source of seed truth and no hand-maintained JSON fixture that can silently drift
from the schema.

---

## 5b. One correction to the provided schema

`hierarchy_levels` was specified with `UNIQUE(org_id, level_number, department)`.
It is incompatible with the seed data it ships alongside: Orthopaedics has three
level-8 units — `HL-08-ORTHO-GEN`, `HL-08-ORTHO-TKR` and `HL-08-POST-TKR`, all
`department = 'ortho'` — so loading `seed.sql` against that schema fails on the
second of them.

The constraint is removed rather than the seed edited, because the seed is
right and the constraint is wrong: a department having several units at the same
depth is the normal case, and `HL-08-POST-TKR` in particular is the multi-parent
node the whole traversal design turns on. The `id` primary key already
guarantees uniqueness. `test_seed_integrity.py::test_schema_does_not_declare_the_broken_unique_constraint`
asserts both halves — that the seed still collides, and that the constraint has
not been reintroduced.

---

## 6. Performance

The full pipeline runs in **under 1 ms** on the 50-node seed (budget: 500 ms), so
the interesting question is how it scales to Supra's real 842 nodes:

| stage | cost | notes |
|---|---|---|
| permission compile | `O(15)`, once | 15 levels, not 842 nodes |
| entry point | `O(levels)` | |
| BFS | `O(V + E)` over **levels**, not nodes | 20 vertices, not 842 |
| zone 2 injection | `O(n)` | one pass, set union |
| 5 checks | `O(n)` total, `O(1)` per node per check | narrowing input each time |
| content fetch | `O(survivors)` | the only content read |

BFS walks the *hierarchy* graph (20 vertices), never the node graph — node count
affects only the linear passes. Check ordering is also a performance property:
the most selective checks run first, so check 5 evaluates 25 nodes for Priya
rather than 50.

---

## 7. What is deliberately not here

* **No Composition Agent** — the pipeline ends at the candidate set.
* **No authentication** — user selection is a dropdown, as specified.
* **No node editing** — the graph is seeded and static.
* **No LLM** — including for derivability, which is a stored column. Scoring it
  at write time is a separate (LLM-using) layer; at read time it is a number.
* **No caching** — every request re-runs the pipeline, so user switching in the
  UI demonstrably re-executes rather than replaying a fixture.

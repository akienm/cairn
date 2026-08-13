# Cairn — the fact sheet

**Measured 2026-08-11.** Every number below was produced by a command run that day, and
the command is printed beside it. Nothing here is asserted from a record, a memory, or a
previous document.

This file exists because the press office now ships more than a dozen pieces, and fifteen
documents that each carry their own numbers are fifteen documents that drift apart. Law 1:
the answered question becomes structure. **A press office piece cites this sheet; it does
not restate a measurement.** When the numbers move, they move here once.

Law 3 governs the whole file: *nothing is known until measured, and an unmeasured claim is
labeled as a hypothesis.* Where a thing is designed but not built, this sheet says so in
the same breath as the thing it is about — never in a footnote.

---

## 0. The shape of the claim

Cairn is 28 days old. It is not a product, it has no users other than its author, and its
runtime spine has never run. What it *is* is a corpus in which a specific method was
applied to itself continuously for four weeks and left a complete, machine-readable record
of doing so. Every number below is a measurement of that record.

Read the numbers as evidence about the **method**, not as a claim about the **artifact**.

---

## 1. The corpus

| Fact | Value | Instrument |
|---|---|---|
| First commit | 2026-07-14 | `git log --reverse --format=%cd \| head -1` |
| Latest commit at measurement | 2026-08-10 | `git log -1 --format=%cd` |
| Elapsed | 28 days | — |
| Commits, `cairn` (code) | 268 | `git log --oneline \| wc -l` |
| Commits, `CairnCommons` (knowledge) | 379 | same, in the sibling repo |
| Charters (`intention+why.json`) in the code repo | 39 | `find . -name "intention+why.json" \| wc -l` |
| Charters compiled into the help surface | 39 | `cairn cairnmap` (footer) |
| Components under `cairn/` | 24 | `device_census()` |
| Python, whole tree | 52,652 lines | `find cairn bin skills launchers learning -name "*.py" \| xargs wc -l` |
| Python living in `proofs/` | 27,259 lines | `find . -path "*proofs*" -name "*.py" \| xargs wc -l` |
| **Proof share of the codebase** | **51.8%** | derived from the two rows above |
| Proof files (`proofs/test_*.py`) | 93 | `find . -name "test_*.py" -path "*proofs*" \| wc -l` |
| Probe directories | 12 | `find . -name probes -type d` |

The proof share is the number most worth staring at. More than half of Cairn's Python is
the code that tries to falsify the other half. That is not a testing-culture flourish; it
is Law 8 — *nothing enters proven-space without a proof a hollow build couldn't pass* —
showing up as a line count.

## 2. What the census says

`device_census()` measures, per component: is a charter on disk, how many proofs exist,
what verdict the latest validation carries, and how many `emit()` call sites live outside
the proofs.

| Fact | Value |
|---|---|
| Components measured | 24 |
| Components with a charter on disk | 24 of 24 |
| Proofs counted by the census | 78 |
| Validation records | 69 |
| Validations green | 69 |
| Validations red | 0 |
| `cairnmap` completeness verdict | **green** — every command, skill and component traces to a charter, and nothing renders without one |

Instrument: `PYTHONPATH=$PWD python3 -m cairn.tools.orient.orient census` and `cairn cairnmap`.

**Do not read "0 red" as health.** A validation carries a horizon and expires; a green
seal means the proof passed when it was sealed against a source fingerprint that has since
been re-checked, not that the component is right. The census counts seals, not correctness.
See §7.

## 3. The knowledge repo

`CairnCommons` holds what would be lost if it were lost — decisions, questions, tickets,
troubles, ideas, and the session-continuity slates.

| Store | Count |
|---|---|
| Tickets | 101 |
| Decisions (Akien's rulings, verbatim + a checkable reading) | 33 |
| Notes | 40 |
| Slates (session-boundary continuity records) | 77 |
| Troubles (live failure records) | 11 |
| Ideas (captured verbatim, interpretation deferred) | 9 |
| Open questions | 6 (5 open + the store's charter) |
| Adjudications | 4 |
| Node classes | 6 |
| Intentions in the congruency lab (compiled copy) | 49 |

Ticket cursors — where each of the 101 boats stands in its workflow:

| Cursor | Count | Meaning |
|---|---|---|
| `PROVED` | 56 | built, proved, sealed, closed |
| `CORPUS` | 13 | filed to the question corpus rather than built |
| `AKIEN` | 12 | standing at his gate, awaiting a ruling |
| `BUILDME` | 7 | cast and charted, not yet built |
| `PROVEME` | 5 | built, not yet sealed |
| `THINKME` | 2 | born, still in design |
| `TICKETME` | 2 | design wrapped, not yet cast |
| `MEASURED` | 2 | closed by measurement rather than by build |
| *(no cursor)* | 2 | predates the workflow string |

Instrument: `python3` over `tickets/*.json`, taking the last `[BRACKETED]` token.

**55% of the tickets ever filed are closed.** The 12 at `AKIEN` are the honest cost of a
system with exactly one human in the loop.

## 4. Inference compilation — the Telos 1 measurement

This is the headline number, and the reason the system exists at all. Every call to an
inference host goes through one door (`inference_domain`), which canonicalises the request
and serves a stored answer when one exists whose horizon still holds. A served answer is a
host call that did not happen.

| Fact | Value |
|---|---|
| Calls through the domain | 1,400 |
| Cache hits | 560 |
| Cache misses | 840 |
| **Hit rate** | **40.0%** |
| Tokens spent | 274,348 |
| Tokens avoided | 142,948 |
| **Share of would-be tokens avoided by structure** | **34.3%** |

Instrument: `from cairn.devices.inference_domain.domain import yield_report; yield_report()`.

The arithmetic: had every call reached the host, 417,296 tokens would have been spent.
142,948 of them were answered from structure instead. That fraction *is* inference
compilation, measured, over 1,400 real calls made during the system's own construction.

**What this number is not.** The canonicaliser is exact-match, not semantic — the domain's
own charter says so: *"today it learns WHETHER the cache pays (the yield); it does not yet
learn WHICH questions are the same."* So 40% is the floor a dumb canonicaliser reaches, not
a ceiling anyone has approached.

## 5. The stores

Fifteen tables in one Postgres database, every one of them carrying an owner in the
registry. An ownerless table cannot come into existence: `create_owned_table` is the only
door and the registry column carries `CHECK (owner <> '')`, so Postgres itself rejects it.

| Table | Owner | Rows |
|---|---|---|
| `inference_calls` | `inference_domain` | 1,400 |
| `chart_hypothesize_nodes` | `chart` | 372 |
| `chart_orient_nodes` | `chart` | 39 |
| `chart_constrain_nodes` | `chart` | 37 |
| `chart_survey_nodes` | `chart` | 37 |
| `chart_decompose_nodes` | `chart` | 35 |
| `chart_triage_nodes` | `chart` | 34 |
| `chart_validate_nodes` | `chart` | 33 |
| `librarian_nodes` | `librarian` | 88 |
| `orient_corrections_nodes` | `orient` | 6 |
| `build_inspector_failures_nodes` | `build_inspector` | 4 |
| `bus_traffic` | `bus` | 2 |
| `cairn_owned` (the registry) | `db_domain` | 15 |
| two tester scratch tables | `tester` | 1 each |

Instrument: `psql -d cairn -c "\dt"`, `select * from cairn_owned`, and a per-table
`count(*)`.

The seven `chart_*` trees total **587 nodes** — the pre-build preamble's accumulated
memory of how requests of each class were oriented, bounded, surveyed, split, ranked,
predicted and accepted.

The librarian's 88 nodes by standing — this is the tenure loop, proved 2026-08-09:

| Tree | Standing | Count |
|---|---|---|
| `library` | `hypothesis` | 80 |
| `library` | `earned` | 3 |
| `library` | `refuted` | 1 |
| `founding` | `hypothesis` | 4 |

**Three nodes out of 88 have earned standing.** That is the design working, not failing: a
node minted during a query is *data* and starts as a hypothesis; standing is earned across
later, independent crossings. A store where most nodes were `earned` after two weeks would
be a store that was confirming itself.

## 6. The workflow, as journaled

Every state transition rides one chokepoint and is journaled at the component's own
address before the code moves.

| Fact | Value |
|---|---|
| `history.json` files (append-only journals) | 29 |
| Journaled crossings, all time | 324 |
| `PROVED` crossings | 62 |
| `PROVEME` crossings | 61 |
| `BUILDME` crossings | 53 |
| `WATCHME` crossings (a probe armed) | 15 |
| `LEARNME` crossings (a dissolved vocabulary) | 27 |
| `TICKETME` crossings | 7 |

Instrument: `python3` over `**/history.json`.

The clearance gate — which refuses a crossing whose authority, proof or resources do not
hold — recorded its **first cleared crossings ever on 2026-08-11**, and its first refusal
in the same hour. As of measurement the queue holds 2 grants and 1 refusal; the refusal was
real, not a fixture: the system refused its own `PROVED` crossing because the component's
source fingerprint had moved after the seal, closing the validation's horizon.

Instrument: `from cairn.devices.harbor_master.clearance import read_attempts; read_attempts()`.

## 7. What is red

Law 9: *red is the default; green is earned.* This section is not a caveat appended to a
good story — it is the same measurement pass as everything above.

**The runtime spine has never run.** This is a live trouble ticket by that name. The
heartbeat, the bus, and the diagnostic trail have no live caller. `bus_traffic` holds 2
records, both written by a fixture on 2026-07-25. No Cairn systemd unit exists on the host
(`systemctl --user list-units --all | grep -i cairn` → nothing). Everything measured above
was produced by code invoked from a session or a proof, not by a running system.

**The node/leaf separation is designed, not migrated.** `librarian_nodes` carries `tree`
and `vector` on the node row (`psql -d cairn -c "\d librarian_nodes"`). The correction
Akien made on 2026-08-05 — a NODE is the thing remembered and belongs to no tree; a LEAF is
the thing indexing it and carries the address `database.tree.leaf` — is reflected in the
design documents and **not** in the running schema. There are no per-tree leaf tables.
Calving and the shear are specified and unbuilt.

**Eleven live troubles.** Each is a measured failure with its own record, and each stays in
the session-open inbox until someone names what changed. The two the system currently
shouts about at every session open:

- `the-runtime-spine-has-never-run` (above)
- `workflow-cursor-unreadable-by-the-chokepoint` — measured 2026-07-26: of 17 staged nodes,
  only 6 could pass through the chokepoint, and one of those 6 was handed a fabricated
  path. The cursor — the field every reader turns into *"where is this boat"* — was policy
  on 11 of 17 nodes and fiction on a 12th.

**Twelve tickets stand at Akien's gate**, and 68 findings await his verdict. The
single-human bottleneck is a measured property of the system, not an incidental backlog.

**Rules still enforced by prose.** `CLAUDE.md` carries a section called *rules awaiting
physics*, which is an explicit IOU list: a rule stated there is one the kernel or the schema
does not yet enforce. That section is designed to shrink monotonically and is currently four
entries long, with four more residues.

---

## 8. How to re-measure this sheet

Everything above is reproducible from a checkout plus a live Postgres. The instruments are
named in each row. The two that give the broadest picture in one call:

```bash
cairn cairnmap                                   # help surface + completeness verdict
PYTHONPATH=$PWD python3 -m cairn.tools.orient.orient census   # per-component measured state
PYTHONPATH=$PWD python3 -m cairn.tools.orient.orient git      # heads, upstream, dirty paths
```

If a number in a press office piece disagrees with this sheet, **this sheet is not
automatically right** — it is dated, and a dated measurement expires like any other. Re-run
the instrument. The piece and the sheet both being wrong is the expected failure mode; the
fix is a fresh measurement, not an edit that makes them agree.

---

*Fact sheet, `press_office/FactSheet.md`. Cited by every piece in this folder. Measured
2026-08-11 against `cairn` at `a947955` and `CairnCommons` at `ede6509`.*

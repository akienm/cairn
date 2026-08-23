# Cairn — the fact sheet

**Cognition Apparatus for Investigation of Reasoning Networks**

**Measured 2026-08-19.** Every number below was produced by a command run that day, and
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

Cairn is 36 days old. It is not a product, it has no users other than its author, and
its runtime spine has been running for less than two weeks. What it *is* is a corpus in
which a specific method was applied to itself continuously for five weeks and left a
complete, machine-readable record of doing so. Every number below is a measurement of that
record.

Read the numbers as evidence about the **method**, not as a claim about the **artifact**.

---

## 1. The corpus

| Fact | Value | Instrument |
|---|---|---|
| First commit | 2026-07-14 | `git log --reverse --format=%cd \| head -1` |
| Latest commit at measurement | 2026-08-19 | `git log -1 --format=%cd` |
| Elapsed | 36 days | — |
| Commits, `cairn` (code) | 417 | `git log --oneline \| wc -l` |
| Commits, `CairnCommons` (knowledge) | 604 | same, in the sibling repo |
| Charters (`intention+why.json`) in the tree | 56 | `find . -name "intention+why.json" \| wc -l` |
| Charters compiled into the help surface | 56 | `cairn cairnmap` (footer) |
| Chartered components under `cairn/` | 39 | `find cairn -name "intention+why.json" \| wc -l` |
| Python, whole tree | 85,690 lines | `find cairn bin skills launchers learning -name "*.py" \| xargs wc -l` |
| Python living in `proofs/` | 43,444 lines | `find . -path "*proofs*" -name "*.py" \| xargs wc -l` |
| **Proof share of the codebase** | **50.7%** | derived from the two rows above |
| Proof files (`proofs/test_*.py`) | 131 | `find . -name "test_*.py" -path "*proofs*" \| wc -l` |
| Probe directories | 21 | `find . -name probes -type d` |

The proof share held above 50% as the codebase grew from 52K to 85K lines. More than half
of Cairn's Python is the code that tries to falsify the other half. That is not a
testing-culture flourish; it is Law 8 — *nothing enters proven-space without a proof a
hollow build couldn't pass* — showing up as a line count.

## 2. What the census says

56 charters compile into the help surface. Each chartered component co-locates its
charter (`intention+why.json`), code, compiled `state`, append-only `history`, `proofs/`,
and `validations/`. A component without a charter does not render in cairnmap and does not
pass the build inspector.

| Fact | Value |
|---|---|
| Charters measured | 56 |
| Proofs counted | 131 |
| Validation records | 110 |
| Validations green | 110 |
| Validations red | 0 |
| `cairnmap` completeness verdict | **red** — one installed skill (`cairnhelp`) has no charter |

Instrument: `cairn cairnmap` and `find . -name "test_*.py" -path "*proofs*" \| wc -l`.

**Do not read "0 red" as health.** A validation carries a horizon and expires; a green
seal means the proof passed when it was sealed against a source fingerprint that has since
been re-checked, not that the component is right. The census counts seals, not correctness.
See §7.

## 3. The knowledge repo

`CairnCommons` holds what would be lost if it were lost — decisions, questions, tickets,
troubles, ideas, and the session-continuity slates.

| Store | Count |
|---|---|
| Tickets | 172 |
| Decisions (Akien's rulings, verbatim + a checkable reading) | 62 |
| Notes | 40 |
| Slates (session-boundary continuity records) | 112 |
| Troubles (36 filed; **0 live**) | 36 |
| Ideas (captured verbatim, interpretation deferred) | 39 |
| Open questions | 16 |
| Adjudications | 4 |
| Node classes | 6 |
| Intentions in the congruency lab (compiled copy) | 69 |

Ticket cursors — where each of the 172 boats stands in its workflow:

| Cursor | Count | Meaning |
|---|---|---|
| `PROVED` | 90 | built, proved, sealed, closed |
| `TICKETME` | 47 | design wrapped, not yet cast |
| `THINKME` | 11 | born, still in design |
| `BUILDME` | 10 | cast and charted, not yet built |
| `PROVEME` | 3 | built, not yet sealed |
| *(no cursor)* | 11 | predates the workflow string |

Instrument: `python3` over `tickets/*.json`, taking the last `[BRACKETED]` token.

**52% of the tickets ever filed are closed.** Zero tickets currently stand at Akien's
gate — the single-human bottleneck that was a measured property of the system has been
cleared this cycle. 231 findings still await his verdict.

## 4. Inference compilation — the Telos 1 measurement

This is the headline number, and the reason the system exists at all. Every call to an
inference host goes through one door (`inference_domain`), which canonicalises the request
and serves a stored answer when one exists whose horizon still holds. A served answer is a
host call that did not happen.

| Fact | Value |
|---|---|
| Calls through the domain | 2,858 |
| Cache hits | 1,262 |
| Cache misses | 1,590 |
| **Hit rate** | **44.2%** |
| Tokens spent | 776,570 |
| Tokens avoided | 438,234 |
| **Share of would-be tokens avoided by structure** | **36.1%** |

Instrument: `from cairn.devices.inference_domain.domain import yield_report; yield_report()`.

The arithmetic: had every call reached the host, 1,214,804 tokens would have been spent.
438,234 of them were answered from structure instead. That fraction *is* inference
compilation, measured, over 2,858 real calls made during the system's own construction.

**The trend from the previous measurement (2026-08-11):** the hit rate climbed from 40.0%
to 44.2%, and the token avoidance from 34.3% to 36.1%, across a doubling of total calls.
The cache is paying more as the corpus deepens, not less — precisely the claim the thesis
makes, and exactly what a dumb exact-match canonicaliser should do if the workload is
genuinely self-similar.

**What this number is not.** The canonicaliser is exact-match, not semantic — the domain's
own charter says so: *"today it learns WHETHER the cache pays (the yield); it does not yet
learn WHICH questions are the same."* So 44% is the floor a dumb canonicaliser reaches, not
a ceiling anyone has approached.

## 5. The stores

Fourteen core tables in one Postgres database, every one carrying an owner in the
registry. An ownerless table cannot come into existence: `create_owned_table` is the only
door and the registry column carries `CHECK (owner <> '')`, so Postgres itself rejects it.
467 bus delivery tables are created by the bus's per-session routing.

| Table | Owner | Rows |
|---|---|---|
| `inference_calls` | `inference_domain` | 2,858 |
| `chart_hypothesize_nodes` | `chart` | 800 |
| `librarian_nodes` | `librarian` | 123 |
| `chart_orient_nodes` | `chart` | 66 |
| `chart_constrain_nodes` | `chart` | 64 |
| `chart_survey_nodes` | `chart` | 64 |
| `chart_decompose_nodes` | `chart` | 62 |
| `chart_validate_nodes` | `chart` | 62 |
| `chart_triage_nodes` | `chart` | 61 |
| `bus_traffic` | `bus` | 607 |
| `orient_corrections_nodes` | `orient` | 6 |
| `build_inspector_failures_nodes` | `build_inspector` | 4 |
| `cairn_owned` (the registry) | `db_domain` | 483 |
| `bus_traffic_delivery` | `bus` | 0 |

Instrument: `psql -d cairn -c "\dt"`, `select * from cairn_owned`, and a per-table
`count(*)`.

The seven `chart_*` trees total **1,179 nodes** — the pre-build preamble's accumulated
memory of how requests of each class were oriented, bounded, surveyed, split, ranked,
predicted and accepted. That is double the 587 nodes measured eight days ago.

The librarian's 123 nodes by standing — this is the tenure loop, proved 2026-08-09:

| Tree | Standing | Count |
|---|---|---|
| `library` | `hypothesis` | 119 |
| `library` | `earned` | 3 |
| `library` | `refuted` | 1 |

**Three nodes out of 123 have earned standing.** That is the design working, not failing: a
node minted during a query is *data* and starts as a hypothesis; standing is earned across
later, independent crossings. A store where most nodes were `earned` after five weeks would
be a store that was confirming itself.

The bus — which eight days ago held 2 fixture records — now holds **607 real records** from
over 20 distinct senders across the `personal` channel. The bus is running in anger.

## 6. The workflow, as journaled

Every state transition rides one chokepoint and is journaled at the component's own
address before the code moves.

| Fact | Value |
|---|---|
| `history.json` files (append-only journals) | 36 |
| Journaled crossings, all time | 423 |
| `PROVED` crossings | 87 |
| `PROVEME` crossings | 87 |
| `BUILDME` crossings | 79 |
| `WATCHME` crossings (a probe armed) | 37 |
| `LEARNME` crossings (a dissolved vocabulary) | 26 |
| `TICKETME` crossings | 7 |

Instrument: `python3` over `**/history.json`.

The clearance gate — which refuses a crossing whose authority, proof or resources do not
hold — has recorded 3 attempts: 2 grants and 1 refusal. The refusal was real, not a fixture:
the system refused its own `PROVED` crossing because the component's source fingerprint had
moved after the seal, closing the validation's horizon.

Instrument: `from cairn.devices.harbor_master.clearance import read_attempts; read_attempts()`.

## 7. What is red

Law 9: *red is the default; green is earned.* This section is not a caveat appended to a
good story — it is the same measurement pass as everything above.

**The runtime spine is running — for the first time.** As of 2026-08-19:

- The **ground loop** is a live process (`ps aux | grep ground_loop` — PID 309660).
- The **web server** is a running systemd unit (`systemctl --user` — `cairn-web-server.service`, active).
- The **bus** holds 607 records from over 20 senders, dated from 2026-07-25 to 2026-08-19.

This was the single biggest red in the previous fact sheet. The spine has been running for
less than two weeks, and the system's instruments over its own health are young. This is
green at the "it runs" rung and red at the "it has been observed running well" rung.

**Zero live troubles.** 36 troubles have been filed over the system's life; all 36 are now
cleared. This is the normal operating state — zero live troubles — reached for the first
time on 2026-08-19. The trouble lane has its own device (`TroubleDevice`), with 25 passing
proofs, an amend door (for correcting a false statement in a cleared_by entry without
reopening), and an emit breadcrumb on every door act. Live count is announced at every
session open; the announcement currently reads: *"no live troubles. (the normal operating
state is zero — this is it.)"*

**The node/leaf separation is designed, not migrated.** `librarian_nodes` carries `tree`
and `vector` on the node row (`psql -d cairn -c "\d librarian_nodes"`). The correction
Akien made on 2026-08-05 — a NODE is the thing remembered and belongs to no tree; a LEAF is
the thing indexing it and carries the address `database.tree.leaf` — is reflected in the
design documents and **not** in the running schema. There are no per-tree leaf tables.
Calving and the shear are specified and unbuilt.

**`cairnmap` completeness is red.** One installed skill (`cairnhelp`) has no charter. A
skill without a charter renders a `→` with no help text and reds the completeness gate.

**231 findings await Akien's verdict.** The single-human bottleneck is a measured property
of the system, not an incidental backlog. But zero tickets currently stand at his gate —
the 12 that were there at the last measurement have been cleared.

**Rules still enforced by prose.** `CLAUDE.md` carries a section called *rules awaiting
physics*, which is an explicit IOU list: a rule stated there is one the kernel or the schema
does not yet enforce. That section is designed to shrink monotonically and is currently six
entries long, with four residues.

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
2026-08-19 against `cairn` at `72ff408` and `CairnCommons` at `0dfd439`.*

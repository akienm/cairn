# Cairn

**Compiled navigation: stones stacked so the next mind doesn't re-derive the route.**

Cairn is a working system and a design method that are the same thing. The method says
that every answered question should become *structure* — a gate, a schema, a compiled
view — so that no mind, human or model, ever pays to answer it twice. The system is what
happens when you apply that rule to the process of building the system, continuously, for
five weeks, and refuse to make an exception for yourself.

The most useful thing in this repository is probably not the code. It is the **record of
the code being built** — 56 charters, 172 tickets, 62 verbatim rulings, 423 journaled state
transitions, and 112 session-boundary slates, all in git beside the thing they describe.

---

## Status: red, and specific about it

> **Law 9 — red is the default; green is earned.**

Cairn is 36 days old (first commit 2026-07-14). It has one user, who is its author. It is
**not a product and there is no supported install.** You can check it out and run pieces of
it; you cannot bring up "a Cairn" and have it do something for you, because:

- **The runtime spine is young.** The heartbeat, the message bus and the web server are
  running for the first time — the ground loop as a live process, the web server as a systemd
  unit, the bus with 607 real records from over 20 senders. This is green at the "it runs"
  rung and red at the "it has been observed running well" rung.
- **Half the design is specified and unbuilt** — and each unbuilt piece is named as unbuilt
  in the charter that owns it, not in a roadmap.
- **Zero live trouble tickets** — the normal operating state, reached for the first time on
  2026-08-19. 36 have been filed over the system's life; all 36 are cleared.

The honest measured state, with the command that produced every number, is
[`press_office/FactSheet.md`](press_office/FactSheet.md). Read it before you read anything
else here that sounds impressive.

What *does* work is listed in [Run something](#run-something) below, and every command
there was executed on 2026-08-11 before it was written down.

---

## The idea, in five minutes

Ten laws hold everywhere, in dependency order. They are in
[`CLAUDE.md`](CLAUDE.md) in full; here is the shape.

**1. The resolver is spent on the novel, not on re-deriving the settled.**
Re-deriving a settled answer is a *defect*, not an inefficiency. This is the whole thesis.
The measurable consequence: 2,858 inference calls went through Cairn's one inference door,
1,262 of them were served from stored structure, and **36.1% of the tokens that would have
been spent were not spent.** That fraction is the thesis, measured.

**2. Intent, its voyage, and its proofs share an address.**
Every component directory holds its charter (`intention+why.json`), its code, its compiled
`state`, its append-only `history`, its `proofs/`, and the `validations/` that sealed them.
To be briefed on a device you *stand in its directory*. The thing and the story of the thing
cannot drift apart, because there is nowhere for them to drift to.

**3. The filename forces the why.**
The charter is not `intention.json` with an optional `why` field somebody can leave blank.
It is `intention+why.json`. A rule that matters is enforced by structure, not by a reviewer
remembering to ask.

**4. A rule that matters is enforced by physics, not policy.**
The kernel or the schema, or it is a tracked debt. `CLAUDE.md` carries an explicit
*rules awaiting physics* section — an IOU list that is designed to shrink monotonically.
A rule living in prose is a rule that is not yet real, and the document says so about itself.

**5. Everything has exactly one owner, and the owner gates writes.**
There is one path to Postgres, one path to inference, one path to inter-device messaging,
one path to a state transition. Not by convention — by a sieve that parses every `.py` in
the tree into an import graph and reds a build that opened a second door.

**6. Nothing enters proven-space without a proof a hollow build couldn't pass.**
50.7% of the Python in this repository lives in `proofs/`. The verdict and the seal come
from a device (the tester), never from the hand that wrote the code.

---

## Requirements

| Thing | Why | Required? |
|---|---|---|
| Linux, Python ≥ 3.12 | the floor | yes |
| PostgreSQL, local, peer auth over the Unix socket | the only durable relational store | for anything that reads or writes trees |
| A sibling checkout of **CairnCommons** | the knowledge repo; tickets, rulings, questions, slates | yes — the system reads it constantly |
| [Claude Code](https://claude.com/claude-code) | the skills (`/intent`, `/sorted`, `/chart`, `/sail`) are markdown executed by a model | to use the work loop; not to read the corpus |
| An inference host | embeddings and resolution | for the graph trees only |

**About the inference host.** Cairn routes to a local Ollama box (an Apple M1 Studio, called
Hex here) as the default rung, with Ollama Cloud and Gemini as keyed failovers behind it.
The routable rungs are authored in `cairn/devices/inference_domain/stacks/` — **shareable rules
only.** Your LAN endpoints and API keys go in `~/.cairn/devices/inference_domain/0/hosts.json` and never
enter git. If you have no inference host, everything except the graph trees still runs.

The two repositories are expected to be siblings:

```
~/dev/src/
  cairn/           ← this repo: code, charters, proofs, validations
  CairnCommons/    ← knowledge: intentions, decisions, tickets, questions, slates
```

---

## Bring it up

```bash
git clone https://github.com/akienm/cairn.git         ~/dev/src/cairn
git clone https://github.com/akienm/CairnCommons.git  ~/dev/src/CairnCommons

cd ~/dev/src/cairn

# The host-seam: builds a venv at ~/.cairn/venv and installs the package into it.
# It is sourceable, it never aborts, and it reports every finding it makes.
source launchers/bootstrap.sh
cairn_bootstrap_apply      # replayable — brings the floor up
cairn_bootstrap_verify     # re-runnable — 0 means the floor is up
```

`bootstrap.sh` is a **host-seam**: its implementation lives where git cannot see it (a venv
is machine-specific compiled bytes), so it carries a replayable `apply` and a re-runnable
`verify`, and its seal expires — the host drifts with nothing in git changing. That is a
general rule here, not a quirk of this script.

Put the dispatcher on your PATH:

```bash
ln -s ~/dev/src/cairn/bin/cairn ~/.local/bin/cairn
```

The database provisions itself on first use — `db_domain.connect()` creates the `cairn`
database if it is absent, over peer auth on the Unix socket. There is no connection string
and no password to configure, by design: the box is the boundary.

---

## Run something

Every command below was run on 2026-08-11 and produced output.

```bash
cairn                     # list the verbs; the dispatcher owns no logic of what it runs
cairn cairnmap            # THE PLACE TO START — the help surface, compiled from all 56
                          # charters with zero inference, ending in a completeness verdict
cairn test <proof-path>   # run a proof under the tester and seal a validation
cairn compile             # recompile the intentions model
cairn slate               # the session-continuity record (also fired by a SessionStart hook)
cairn ruling              # the intake door for a human ruling
cairn turnscan            # the turn-shape check
cairn sudorelay           # the audited self-serve path to root
```

Measure the system with its own instruments:

```bash
export PYTHONPATH=$PWD

# per component: charter on disk, proofs, latest validation verdicts, emit call sites
python3 -m cairn.tools.orient.orient census

# where is a capability actually CALLED — AST, never a word-grep
python3 -m cairn.tools.orient.orient calls emit

# is what I said committed/pushed ACTUALLY committed/pushed?
python3 -m cairn.tools.orient.orient git

# what does this file import, and what imports it?
python3 -m cairn.tools.orient.orient imports cairn/devices/librarian/trees.py

# is inference compilation paying off?  (calls / hits / tokens spent / tokens avoided)
python3 -c "from cairn.devices.inference_domain.domain import yield_report; print(yield_report())"
```

Those four `orient` scans exist because a model working from the same data reached three
different conclusions about the same system in one morning, and every wrong conclusion had
one root: **a proxy was read instead of the thing** — a word instead of a capability, a
record instead of the world, its own narration instead of the remote. Each scan carries the
dated correction that seeded it as a required `provenance` field, and a proof refuses a scan
whose provenance names no correction.

`cairn cairnmap` is the single best entry point. It is compiled from the charters, so it
cannot describe a component that does not exist, and a confusing entry in it is a bug in
that component's charter — fixed at the source, never in the help text.

---

## The three roots

Cairn splits state three ways and never blurs the line. This is the first thing to
understand and the easiest thing to get wrong.

| Root | Holds | Rule |
|---|---|---|
| `~/dev/src/cairn/` | code, skills, charters, `state`/`history`, proofs, validations | **class-space**; git; shareable; *no runtime state, ever* |
| `~/dev/src/CairnCommons/` | intentions, decisions, tickets, questions, troubles, slates | **knowledge**; its own repo; *if losing it loses knowledge, it's commons* |
| `~/.cairn/` | logs, credentials, flags, cached state, personal data | **instance-space**; never in git |

Runtime instances live at `~/.cairn/devices/<device>/<instance>/`. A singleton is instance
`0` — not a special case.

The test that settles most arguments: **if you would need to gitignore it, it is in the
wrong root.**

---

## How to read this codebase

Do not start at the top and read down. Stand somewhere and look around.

```bash
cd cairn/devices/librarian && cairn cairnmap    # renders THIS component's whole charter
cat intention+why.json                  # what it is, why it exists, how it learns
cat state.json                          # compiled from history — never hand-edited
cat history.json                        # append-only; the voyage that got it here
ls proofs/ validations/                 # the teeth, and the seals they earned
```

Every component answers the same questions in the same order. `intention+why.json` carries
a `what`, a `why`, a `how_it_learns` (where *"it doesn't, because X"* is a valid answer and
silence is not), a `traces_to`, and an `owner`.

A component without a charter does not run — `build_inspector` reds the build.

**Read the whys, not the whats.** The `why` fields are where the measured failure that
caused each design lives. Most of them name a date and a specific thing that went wrong.

---

## What is built, and what is not

The measured version is [`press_office/FactSheet.md`](press_office/FactSheet.md). The
summary:

**Built, proved, and exercised in real work**

- The charter/state/history/proof/validation layout, on all 39 components under `cairn/`
- The tester — proofs run under network isolation, verdict and seal from a hand the builder
  did not guide, validations that carry a falsifier and a horizon and therefore expire
- `db_domain` — the single owner-gated path to Postgres; 14 core tables, every one owned
- `inference_domain` — the single path to every inference host, with a metered cache;
  2,858 calls, 44% served from structure
- `import_sieve` — the import graph and the sieves that enforce the single-door rules
- The emit chokepoint and the workflow's state machine — 423 journaled crossings
- `chart` — the pre-build preamble as seven schema-gated question nexi; 1,179 accumulated nodes
- The skills: `/idea`, `/intent`, `/design`, `/sorted`, `/chart`, `/sail`, `/saveslate`,
  `/note`, `/commit`, `/moreabout`, `/challenge`
- `cairnmap` — the help surface, compiled, completeness-gated
- `harbor_master`'s clearance gate — which recorded its first real refusal on 2026-08-11
- The librarian's graph trees and tenure loop — 123 nodes, 3 with earned standing
- The trouble device — 36 tickets filed, 0 live; amend door, 25 passing proofs
- The aider shim — transport works (n=1 drive); apprentice has 0 surviving edits

**Running**

- The ground loop — a live process; the heartbeat
- The web server — a running systemd unit; serves the panes
- The bus — 607 records from 20+ senders; the spine is alive

**Built but lightly exercised**

- `system_rackmount` — the host-predicate owner; young

**Designed, specified, and not built**

- The NODE/LEAF separation in the running schema — `librarian_nodes` still carries `tree`
  and `vector` on the node row; there are no per-tree leaf tables
- Calving along dominant attractors, and the shear that repairs the index
- Semantic canonicalisation in the inference cache (today it is exact-match)
- Everything in `CLAUDE.md`'s *rules awaiting physics* section, by definition

---

## Where the writing is

`press_office/` is where Cairn explains itself to people outside the build loop.

- **[`FactSheet.md`](press_office/FactSheet.md)** — every measured number, dated, with its
  instrument. Cited by everything else.
- **[`WorkflowDefinition.md`](press_office/WorkflowDefinition.md)** — the source of truth
  for the workflow: every step, its gate, and how a gate opens.
- **[`IntentionBasedDesignForHumans.md`](press_office/IntentionBasedDesignForHumans.md)** —
  the founding explainer of the design pattern.
- **[`GraphTreeMemoryTechnicalBrief.md`](press_office/GraphTreeMemoryTechnicalBrief.md)** —
  the memory system for an enterprise architect.
- **[`NoveltyDrivenGraphTreeExpansion.md`](press_office/NoveltyDrivenGraphTreeExpansion.md)** —
  the academic paper, whose real content is a negative result about Cairn's own design.

`MAP.md` is the transitional working map. It is being dissolved into charters and tickets,
and it froze at 2026-07-17 while 197 commits landed in the following week — which is exactly
the failure the charter-compiled help surface exists to prevent. Trust `cairn cairnmap` over
`MAP.md` where they disagree.

---

## If you want to adopt the method without the code

You do not need any of this software. The method is four moves:

1. Put the intent beside the implementation, in a file whose **name** forces the why.
2. Make every rule that matters into a **gate that refuses**, and keep an explicit list of
   the rules that are still only prose.
3. Give every store **exactly one owner** and make the owner the only door.
4. Treat a **re-derived answer as a defect** — when you catch yourself answering something
   twice, the fix is structure, not a better memory.

The rest of Cairn is those four moves applied to themselves until they had somewhere to live.

---

## Licence and contact

No licence file has been chosen yet. Both repositories are public on
[github.com/akienm](https://github.com/akienm) for reading; ask before depending on
anything here. GitHub Actions are disabled by choice — there is no CI, and there will not
be one.

Cairn is built by **Akien MacIain** with Claude. The system's rulings, and the record of
where the model's reading of them was wrong, are in `CairnCommons/decisions/` — verbatim,
beside a checkable reading of each. That folder is the most honest thing here.

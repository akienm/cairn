# Cairn — the map

*A cairn is compiled navigation: stones stacked by earlier travelers so the next
one doesn't re-derive the route. Each question, once answered, becomes structure;
the expensive resolver is spent only on the novel. Every closed proof adds a stone.*

This file is the working map for the Cairn rebuild. It is chat-fed (Akien ↔ CC)
and Opus-executed: Opus works tickets cut FROM this map; anything needing frontier
attention gets wrapped first. The map is authoritative over memory of the
conversation that produced it.

## Why Cairn exists (the founding measurement)

UnseenUniversity (the predecessor, `~/dev/src/UnseenUniversity`) rotted in a
specific, measured way:

- The inference proxy was mandated for a month; 6 live files still opened raw
  HTTP to the inference host. The io corpus and 804 RunRecords were therefore
  blind to 187–364 kernel-counted real connections — the records never recorded.
- The db proxy was used by 20 files (mostly a dead tree); 40 live files called
  `psycopg2.connect` directly.
- Dozens of components failed silently for months, producing success-shaped
  records.

Root cause: **chokepoints were rules instead of physics**, and **the map (code
map → memory palace → memory folders) was always a separate artifact from the
territory**, so it drifted on discipline — and discipline is measurably worth
nothing here. The verification debt is identical whether we fix in place or
restart; restarting changes where we stand while paying it and makes re-rot
structurally impossible. Hence Cairn.

**The old repo is a quarry, not a dependency.** Archived read-only. Nothing
crosses by bulk copy; a snippet enters only inside a ticket, with an intention,
passing a proof under the new harness.

## Naming principle

The evocative name belongs to the **system only**. Components get boring,
self-describing names (`dispatcher`, `inference_host`, `job_runner`) — the old
world needed an authoritative device-roster memory just to decode `Granny`/
`Hex`/`Scraps`, an orientation tax paid by every fresh mind, every session.
Self-naming code needs no roster.

## Intention taxonomy — four layers

Two kinds surfaced immediately (Akien): **what it will do** vs **how it will do
it**. Formalized as four layers, each tracing to the one above it:

0. **Telos** — Akien's charter: WHY Cairn exists and whose it is. Lives in
   CairnCommons. (The six below.)
1. **Laws** — system-wide invariants; how the Cairn world works. Live at the
   repo/commons root. (The eight below.)
2. **Form** — the shape every device must have; the device contract. Lives with
   the base class. (Akien's three below.)
3. **Charters** — per-device intentions; what THIS device does. One per device,
   in that device's directory. Written before the device is.

**Traceability is the scar-tissue filter:** every charter traces to Form and
Laws; every Law traces to the Telos. Anything that can't trace up doesn't cross
from the quarry.

## The Telos (Akien, 2026-07-14 — ratified)

1. **Demonstrate inference compilation.** The research thesis — and it says
   *demonstrate*, so it is falsifiable and will someday carry a proof.
2. **Allow Akien to build tools that help with writing and remember things.**
3. **Share those tools with others.**
4. **Build something that thinks the way Akien does.** (Graph trees / Q+A nexus
   — needs operational unpacking before it can gate anything.)
5. **Build something that is self-improving.**
6. **Build something that makes life suck less for everybody.** (CP4 as the
   terminal goal — the values were always the telos showing through.)

Derivations worth noting: Law 1 (resolver spent only on the novel) derives from
Telos 1. Telos 2–3 mean Cairn has a USER, not just a builder — the librarian
writing/memory tools are the first user-facing deliverable, which is why the
build spine ends where it does. Telos 6 ⊃ CP4; Telos 5 is the founding property
carried over from UU.

## The Laws (ratified 2026-07-14)

Present-tense contracts, dependency order; telos at the root:

1. **The resolver is spent on the novel, not on re-deriving the settled.** Every
   answered question becomes structure; re-deriving a settled answer is a defect.
2. **CP1–CP6 hold everywhere, including in the process that builds the system.**
   (Carried over intact from UU — the one part that was never the problem.)
3. **Nothing is known until measured.** An unmeasured claim is a hypothesis and
   is labeled as one.
4. **A rule that matters is enforced by physics, not policy** — the kernel or the
   schema. Until it is, it is a tracked debt (an IOU), not a resting state.
5. **Intent and implementation share an address.** Every component carries its
   intention and proofs beside its code; a component without an intention
   doesn't run.
6. **Everything has exactly one owner.** The owner alone gates writes to it;
   delegated access and ownership transfer happen only through the owner's gate,
   never ambiently. (The ownership model — database-granularity ownership,
   employer-grant, node-give transfer, Postgres-roles-plus-proxy enforcement —
   lives in db_domain's charter.)
7. **Errors are loud at diagnostic surfaces and permanent in records of truth.**
   A presentation surface may collapse an error into a coherent shape; a record
   of truth never may.
8. **Nothing enters proven-space without a proof a hollow build couldn't pass.**
   Entry from the quarry is by grafting, one ticket at a time.

Any rule that can't trace to one of these is probably scar tissue and stays in
the quarry.

## The Form (v0 — the device contract, Akien 2026-07-14)

1. **Each device contains and encapsulates that device. Instances are children
   of their device.** Runtime: `~/.cairn/devices/<device>/<instance>/`.
   Repo: `~/dev/src/cairn/<device>/`. No shared flat log roots, ever.
   - Ratified 2026-07-14: repo is **class-space**, home is **instance-space**.
     A singleton is just a device with one instance (e.g. instance `0`) and
     still lives under `~/.cairn/devices/<device>/0/` — one path shape, no
     special case, no state in the repo.
2. **Each device reports, in order: intention, then state, then settings, then
   other things (e.g. chat) as we build it out.** One uniform introspection
   surface — the same protocol the tester probes and the web UI renders, so
   observability is not a separate build. A running device can always be asked
   what it is FOR; reported intention vs filed intention is a drift detector.
3. **Devices share common services wherever possible; shareable services are
   spun off.** When two devices need the same thing, it becomes a service (or
   the base class), never a second copy.

## Sub-intentions under the six (v1 — RATIFIED by Akien 2026-07-14)

Structure note: the six pair into three couples — **1+4 the science** (memory,
cognition), **2+3 the product** (first user, second user), **5+6 the
character** (growth, care).

**T1 — Demonstrate inference compilation**
- 1.1 Answered questions live as structure (graph-tree store — baked above).
- 1.2 Every resolver call is metered (possible because the inference domain is
  the kernel-enforced only pipe).
- 1.3 A cache hit verifies before it answers (canonicalization gate).
- 1.4 Invalidation propagates: falsifier + horizon on every answer; upstream
  change rots downstream loudly.
- 1.5 THE DEMO: one narrow domain; resolver-calls-per-solved-task declines as
  corpus grows, quality held constant.

**T2 — Tools for Akien's writing and remembering**
- 2.1 The librarian converses (chat over commons + graph trees).
- 2.2 Capture is frictionless — thought → chartered store in seconds.
- 2.3 Recall cites its nodes: answers from Akien's corpus with provenance.
- 2.4 The librarian can go learn an area of study and file it as structure.
- 2.5 Writing tools operate on the writing corpus as graph trees (SHAPE TBD —
  needs its own intention conversation).

**T3 — Share with others**
- 3.1 Nothing personal can leak — by construction (three-root split).
- 3.2 A stranger can install and boot Cairn without Akien (horizon TBD).
- 3.3 A tool ships without the whole rack.
- 3.4 The commons explains itself — charters are the docs.

**T4 — Thinks the way Akien does** (formalizes "Telos 4 unpacked" below)
- 4.1 Question corpus = chartered store with yield tracking.
- 4.2 Challenge gate fires at every /sorted (high tempo, unsettled).
- 4.3 Oracle slots explicit + logged; compilation = their measured retreat.
- 4.4 Background loop over settled structure (slow tempo — intuition).
- 4.5 Every hunch carries reasoning provenance.
- 4.6 THE DEMO: missed angles at a measured, nonzero, improving rate.

**T5 — Self-improving**
- 5.1 Questions earn tenure by yield; losers retire.
- 5.2 The failure loop closes: trouble → diagnosis → design → structure.
- 5.3 Process artifacts (skills, charters, CLAUDE.md) are challengeable and
  versioned like code.
- 5.4 Measurement is base-level; nothing improvable is unmetered.
- 5.5 Gates come off only when the proof corpus pays.

**T6 — Make life suck less for everybody**
- 6.1 CP1–6 pinned by tests, enforced in-process.
- 6.2 Friction reduction measured on Akien FIRST (metric TBD — must be named
  before it can be measured).
- 6.3 No silent failure, no unsafe default: kernel chokepoints + trouble reflex.

**Cross-link (ratified with the set): T2 IS the demonstration domain for T1.5.**
The writing/memory workload is the narrow domain where the curve must bend:
live human silent-failure detector (6.2), daily novel questions (T4 training
data), science and product become one build.

Draft debts: 2.5 shape, 3.2 horizon, 6.2 metric.

## Telos 4 unpacked — question-driven cognition (v0, 2026-07-14)

Source: Akien's introspection + `~/.unseen_university/akien/20260714.Novelty.txt`
(quarry, MIXED provenance: Akien's five novelty questions are first-person data;
the other AI's "hidden LLM probe" layers and "~89% savings" are HYPOTHESIS-class
— plausible, unmeasured, never to be cited as fact about LLM internals. They
enter as candidate questions and earn tenure by yield, like everything else.)

- **The compilable core:** "the answers vary, but the questions do not."
  A fixed, evolving question set fired deterministically over variable content
  is compilable cognition — this is why Telos 4 and Telos 1 are one project.
- **Architecture:** deterministic scaffold + explicitly-marked ORACLE slots.
  Cross-domain similarity questions ("what would fit there?") consult the
  embeddings-over-graph-trees organ; generation consults the LLM. Every oracle
  call is logged + provenance-stamped. **Compilation = the measured migration of
  answers out of the oracle slots into structure.**
- **Intuition, operationalized:** cheap approximate cross-domain retrieval +
  expensive verification, running in the background over SETTLED structure
  (novelty questions picking over closed nodes for missed angles — a
  default-mode loop). A surfaced hunch carries its full causal chain: which
  question, which nodes, which domains, what similarity.
- **Self-aware (not sentient), buildable sense:** the device can report WHY it
  thought what it thought. Form #2's introspection surface gains a channel:
  reasoning provenance. Humans buy the "coherent moment" by overwriting the
  tape; Cairn presents coherence at interfaces and keeps the intermittent
  operations in the record (Law 7 already covers this).
- **Questions are first-class commons artifacts** with measured YIELD (how
  often did this question produce a hypothesis that survived verification?).
  Promotion/retirement by yield = Telos 5 in measurable form.
- **Reflexive:** the intention → design → tickets → build → prove workflow IS
  this cognition — the process that builds Cairn is specimen #1 of what Cairn
  demonstrates.
- **Falsifiable form (draft, answers Q5):** the device surfaces missed angles
  in settled thinking — cross-domain hypotheses neither the human nor the
  resolver had queued — at a measured, nonzero, improving rate, every one
  explainable end-to-end from its provenance chain.

## The tree(s) — three roots

| Root | Holds | Rule |
|---|---|---|
| `~/dev/src/cairn/` (repo) | code, skills, CLAUDE.md, per-device charters + proofs | class-space; git; shareable |
| `~/dev/src/CairnCommons/` (own repo — ratified 2026-07-14) | intentions (incl. the Telos), decisions, tickets, proofs, slates — grep-able JSON | *if losing it loses knowledge, it's commons*; the tester consumes from and emits to it |
| `~/.cairn/` | logs, credentials, flags, cachedstate, personal info | instance-space; never in git; composed at use-time |

**The map IS the territory:** every component directory co-locates
`intention.json` + implementation + `proofs/`. Opus gets briefed by standing in
the directory. The tester refuses to run a component with no intention, so the
map cannot rot apart from the code.

**Stores self-describe like devices (Akien, 2026-07-14):** every artifact-type
directory in CairnCommons carries a `_charter.json` co-locating:
- **intention + why** — what this type is FOR, why it exists
- **template/schema** — the current shape of a valid record, versioned

Physics, not policy: the single emit chokepoint refuses to write into a
directory that lacks a charter, and validates every record against the
co-located template. Consequences for free: (a) no hunting for schemas — the
current template is always at the address of the data it governs (UU ticketed
this, `T-memory-category-templates`, and instead accumulated ~20 scattered
schema tickets across four months — schema apart from data is the same drift
as map apart from territory); (b) artifact-proliferation resistance — a new
type cannot exist until someone writes down what it's for; (c) the tester
validates a store the same way it validates a device: charter present, records
conform, drift is red.

```
cairn/<device>/
  intention.json    ← charter: what this is FOR
  *.py              ← implementation
  proofs/           ← what a hollow build couldn't pass
```

## Repo file tree (forks ratified 2026-07-14)

Decisions: **base + devices only** (a spun-off service becomes another device —
no third category); **proof CODE beside the device, proof RECORDS in commons**;
**skills repo-canonical + symlink, but PURGED** — a skill crosses from UU only
if it serves Cairn (e.g. `autocompact` was decided-retired yet still squats in
UU's skills dir — the IMAP-banner disease; no skill crosses on inertia).

```
~/dev/src/cairn/                  # class-space; git; no state, ever
  CLAUDE.md                       # spine step 1 — stays minimal: laws + pointers, not prose
  MAP.md                          # this file (dissolves into intentions/tickets over time)
  pyproject.toml                  # `pip install -e .` green at all times; include = ["cairn*"]
  cairn/                          # the single import root (one heart — UU law carries)
    __init__.py                   # EMPTY/lazy forever (boot-order lesson: importing any
                                  # subpackage must never eager-import a DB-bound one)
    base/                         # the Form, embodied
      intention.json              # charter of the base itself
      core_values.py              # CP1–CP6 frozen contract (crosses by graft, with its pin test)
      device.py                   # BaseDevice
      shim.py                     # BaseShim + the one loop primitive
      introspect.py               # Form #2 surface: intention → state → settings → …
      store.py                    # commons access + charter enforcement primitives
      proofs/                     # proof code for the base
    devices/
      __init__.py                 # empty/lazy
      tester/                     # earliest device on the spine; owns the network
      db_domain/                  # the only path to 5432
      ground_loop/
      dispatcher/                 # (UU: Granny) — functional names, no roster
      inference_domain/           # the only path to inference
      web_server/
      librarian/
      …                           # one dir per device, ALL the same shape:
                                  #   intention.json + code + proofs/
  skills/                         # canonical; ~/.claude/skills symlinks here; purged set only
  launchers/                      # cairn launch/rescue scripts; symlinked onto PATH
```

No `devlab/` — CairnCommons replaces it entirely. No `docs/` — knowledge lives
in commons, intent lives at the address it governs. Cross-cutting proofs obey
Law 6: every proof has exactly one owner — the device that owns the seam.

Companion trees (drawn once, here, for orientation):

```
~/dev/src/CairnCommons/           # knowledge; own git repo
  intentions/  _charter.json + telos.md + …   # first charter written (Q6)
  questions/   _charter.json + …              # the question corpus, with yield
  decisions/ tickets/ proofs/ slates/ sessions/ notes/
                                  # a type dir EXISTS only once its _charter.json does

~/.cairn/                         # instance-space; never in git
  devices/<device>/<instance>/    # logs/, cachedstate/, flags (singleton ⇒ instance 0)
  vault/                          # credentials, composed at connect-time, never persisted baked
  akien/                          # personal: inboxes, notes-in-progress
```

## Database

Fresh DB. Founding law (generalizes UU's button pattern): **every table has
exactly one owner — a class, an instance, or a human — and the owner gates every
write to it** (delegated access and ownership transfer happen only through that
gate; Law 6). Tables are provisioned only through the db domain; owner is declared
in schema metadata at creation; an ownerless table cannot come into existence.
Port 5432 is kernel-closed except via the proxy path from day one, so bypass is
never possible and there is never a migration to enforce later. Old DB contents
get the quarry treatment (ticket + proof, not pg_dump).

## Two log classes + journeys — forensic-first debugging (2026-07-14)

Every major state transition and every interface boundary is logged (base
reflex, inherited). Two classes with different physics:

- **Events** (bang-and-done): state changes + crossings → per-device
  instance-space streams. Cache-class: high volume, generous rotation.
- **Journeys** (the traveling object): workflow-carried work items — a coding
  ticket, an inference request — get a `journey_id`; EVERY transaction along
  the path appends to the journey record (device, inputs, outputs, decision,
  timing). The base appends at each crossing; no device can opt out. Truth-
  class: owned table via db_domain, retention by charter horizon, never
  ad-hoc deletion.

**Complete by construction, not compliance:** journeys are captured at the
kernel-enforced chokepoints — there is no uninstrumented path (this is what
UU's 804 RunRecords lacked: six raw-HTTP files never entered the recorded
pipe).

**Why this kills the fix-here-fix-there debug loop:** oscillation happens when
each fix is made against a reconstructed guess. With the journey, cause-
finding is a READ, not a rerun — the wrong value sits in the record at the hop
that produced it, with its inputs. CP3 mechanically satisfied. Composition:
trouble tickets file carrying their `journey_id` — every machine-filed failure
arrives with its forensic tape pre-attached.

## Trouble tickets — a base-layer reflex (2026-07-14)

Failure reporting is INHERITED, never hand-wired — that's what kills the
silent-failure class (UU's dispatcher logged only to its tmux pane for weeks
because sink-wiring was per-device; anything hand-wired can be un-wired).

- **Emission is a base reflex:** error at an interface crossing → the
  diagnostic base files a trouble ticket mechanically, evidence auto-attached
  at the write path (device, instance, state snapshot, log tail, provenance
  chain). Law 7 made flesh; CP2's capture mechanism.
- **Different species from work tickets:** work tickets are cut from
  intentions; trouble tickets are machine-filed OBSERVATIONS. One becomes the
  other only through diagnosis at the workflow's front gate — or becomes a new
  question in the corpus.
- **Signature-keyed dedup** (quarry scar worth keeping: UU's watch_problems
  auto-deposit became recurring debt): same signature → increment occurrence
  count + freshen evidence on the existing ticket. A 400-count ticket and a
  1-count ticket are different beasts; the count is diagnostic data.
- **One store:** `CairnCommons/troubles/` + `_charter.json`; one emit
  chokepoint; owner: the diagnostic base.

## CLAUDE.md discipline (2026-07-14)

UU's banners (NO-IMAP, NO-SQLITE) were compensations for missing enforcement —
prose shouting where physics was absent. Cairn's CLAUDE.md rules:

- **A prose rule is an IOU for enforcement.** The file may contain only: the
  Laws, pointers to charters, and rules not YET enforceable by physics — each
  of the third class carries a ticket to become physics and leaves the file
  when it does. (SQLite: "durable state goes through db_domain / store
  primitives" lives once in db_domain's charter; the tester import-scan reds
  any `sqlite3` import; CLAUDE.md then needs zero words about it.)
- **Negative-history rules are banned as a class.** "There is no X anymore"
  serves only minds carrying contaminated context; Cairn minds never see the
  quarry. Nothing in Cairn's CLAUDE.md may reference what UU did wrong.
- **Each rule lives once, at its home layer; CLAUDE.md points, never restates.**
- CLAUDE.md has its own charter and a periodic /challenge cadence — the file
  that briefs every session is the most-challenged artifact in the system.

## The layers program + graph trees (2026-07-14)

**Layers (Akien):** sort the layers of the CC dynamic — the agentic loop plus
the internal loops that must exist in the model; each layer eventually gets an
inspectable presence on the rack; human-like reasoning sorts on top.
Calibration: the agentic-loop layers (context assembly → intention inference →
planning → tool dispatch → result integration → verification → emission) are
OBSERVABLE from transcripts — rack them directly. Claims about latent internal
loops are hypothesis-class (the model has no introspective access; its
self-reports would be confabulated coherence) — but that doesn't matter: we
build the explicit version and MEASURE it. The pipeline is not an imitation of
the model; it is the better instrument.

**Graph trees — verdict: sound as a bet; hypothesis until the tiny demo.**
For: (1) convergent evidence — intentions, tickets, and questions all
independently landed on typed nodes + dependency edges + bottom-up validation
+ cross-links; the commons is already a hand-built graph tree. (2) Q+A is the
right node unit: a question carries its own falsifier (re-ask and diff).
(3) Ancestry: memoization of reasoning (ACT-R production compilation,
chunking). Three named hard sub-problems decide the bet:
- **Invalidation** — edges carry dependency direction; answers carry
  falsifier + horizon; upstream change propagates rot. Without it: confidently
  stale memory, UU's disease at cognition scale.
- **Canonicalization** — when is a new question "the same" as a cached one?
  Cache hits need a cheap verification step; cache precision is measurable
  (confabulation-by-cache-hit is the graph-tree coherent-moment lie).
- **Composition** — the falsifiable core of Telos 1: one narrow domain, and
  the measured curve of resolver-calls-per-solved-task declining as the corpus
  grows, quality held constant. The curve bends or it doesn't.

**Storage model (baked in, 2026-07-14):** fixed node envelope; nodes and edges
each in ONE logical table (owner: the graph-tree device); **trees are
first-class ROWS** (identity, owner, charter-pointer, birth event — calving a
tree = inserting a row, no DDL). Cross-domain search and cross-tree
invalidation both require edges-between-trees to be as cheap as edges within
— which is why trees never get independent tables. Physical calving is
allowed one layer down: Postgres partitioning by tree_id when scale demands,
and freely-calved DERIVED structures (per-tree adjacency caches, materialized
closures, embedding shards) — disposable, rebuildable accelerators. Rule:
**records of truth never calve; caches may.** Exact DDL belongs to
db_domain's charter.

## Workflow v0 + starting skills (2026-07-14)

Extracted from specimen #1 — the founding conversation itself, run by hand.

```
/intent <desc> → intention conversation (unpack WHAT/HOW, trace to Telos,
                 sort sub-intentions into dependency tree)
→ /sorted      → CHALLENGE GATE: fire the question corpus at each intention
                 (assumption? missing? falsifiable? collides?); failures loop
                 back to conversation cheaply; survivors file to CairnCommons
→ design conversation → designs + architectural requirements → decisions
→ /ticket      → one ticket per intention, parents over children; every
                 ticket carries its intention pointer — no freehand tickets
→ build        → CC.0/CC.1/aider by difficulty, under the tester's network
→ prove        → tester consumes intention + proof code, emits verdicts to
                 commons; children prove before parents
→ /outcome     → green: parent may prove; red: CP2 data — back to design or
                 new questions into the corpus (kick-back is a disposition)
```

**Challenge = the intuition loop at high tempo on UNSETTLED thinking; the
background device (later) is the same mechanism at slow tempo on SETTLED
thinking. One mechanism, two tempos** — so the question corpus accumulates
yield data from the first /sorted onward, months before any intuition device
exists.

**The question nexus is the workflow's primitive (named by Akien; ratified
2026-07-14).** Every station — intent conversation, challenge gate, design,
diagnosis, ticketing — is the same machine: a fixed question set fires at a
variable artifact; answers route forward, failures route back; every firing
logs yield. Stations differ ONLY in which question set loads. Nexuses are the
living organs; graph trees are what they deposit (a trained tree = a nexus's
firings compiled into structure — Telos 1 as anatomy).

**Role-replacement staircase:** the resolver (Opus/frontier) currently
occupies several nexuses — including intention extraction AND decomposition
(decomposition inherently writes child intentions; machine drafts become spec
by ratification, per the provenance rule). Each occupancy is scaffolding: an
occupant is replaced by trained structure only when the replacement's outputs
survive challenge at the occupant's rate — measured out, never declared out
(the gate-removal staircase applied to the resolver itself). Planned order:
intention extraction first. Not yet — the trees it would train on are being
founded now.

Five feedback loops, each catching a distinct failure: challenge-at-sort (bad
intentions, pre-cost); proof-on-close (hollow builds); bottom-up parent proof
(parts green, whole hollow); question-yield tracking (the corpus improves —
Telos 5, measured); loadslate/saveslate (session continuity).

**Starting skill roster — 10, from UU's 55.** Each enters with its own charter.

| Skill | Stage | Origin |
|---|---|---|
| /loadslate | session open | rename: context-load |
| /saveslate | session close | rename: savestate |
| /intent | open intention conversation | NEW |
| /sorted | challenge gate + file to commons | graft, rebuilt |
| /challenge | fire questions at any artifact | NEW — absorbs all 12 audit-* |
| /ticket | cut tickets from intentions | graft (+ intention pointer) |
| /next | what to work on | graft: query-ticket |
| /commit | every stone | graft |
| /outcome | record result | graft |
| /note | capture without ceremony | graft |

Not crossing (for now): sprint family (returns when a dispatcher exists to
need it), day-close (folds into /saveslate when earned), audit-* (absorbed),
everything unnameable (stays in quarry).

## Build order (the spine)

CLAUDE.md → skills → launchers → commons → CP/diagnostic base →
**tester + kernel-owned network** (before the first thing it guards) →
db domain → ground loop → rack → inference domain → web server →
librarian-as-chatbot → graph trees (embeddings generator lives here).

Workflow target: intention → design → tickets → build → test → done; each stage
a question nexus with feedback. End state: CC.0 + CC.1 + aider (easy work), one
working part at a time, proved.

## Open questions

- ~~Q1: Commons its own repo?~~ **A1: yes — `CairnCommons` (Akien, 2026-07-14).**
- ~~Q2: Singleton path shape?~~ **A2: always an instance, never a special case
  (Akien, 2026-07-14).**
- Q3: What of UU's memory index crosses over? (Principles yes, scar tissue no —
  needs a one-pass triage.)
- Q4: The device introspection surface — protocol shape (bus mailbox? HTTP?
  both?) to be designed with the base class.
- ~~Q5: Telos 4 operational form?~~ **A5 (v0): see "Telos 4 unpacked" —
  falsifiable form drafted; ratification + question-schema design pending.**
- Q6: Intention schema in CairnCommons — the envelope shape ({claim, evidence,
  provenance_class, falsifier, horizon} was the UU direction). Design before
  the store grows, not after.

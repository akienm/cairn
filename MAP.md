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

## The learning loop is the primitive; artifacts precipitate (2026-07-15)

The governing stance (Akien) — foundational, not a preference to be traded away:
**there is no certainty, only the current best guess.** Every act is an
experiment. A result that matches expectation is a confirmation; one that doesn't
is a learning point (CP2); a persistent irritant is an open optimization. So
**nothing is terminal** — `validated` is not "done," it is "best guess, still
carrying its falsifier and horizon." The state machine's back-edge
(build → deconstruct) is not a special case; it is the universal shape.

**Everything has feedback to its point of creation — not just for information,
but for revision.** An upstream change must be able to reach and revise anything
downstream that depends on it. This is already physics, not aspiration:
invalidation propagates (edges carry dependency direction, answers carry
falsifier + horizon, upstream change rots downstream loudly); the five feedback
loops each close; CP2 is a disposition, not a sentiment.

**Artifacts precipitate from the loop; they are not the point.** One constantly
looping, self-improving system throws off three kinds, all of the same nature:
- **process artifacts** — skills, charters, this map (the loop tuning itself);
- **compilation artifacts** — prebuild scripts, trained trees (the loop
  compiling its own cognition — Telos 1);
- **end products** — the librarian and the tools (the loop serving the user).

None is privileged; all are revisable precipitate of the one circle. The artifact
taxonomy below is therefore a snapshot of what has fallen out so far, not a fixed
ontology.

## Naming principle

The evocative name belongs to the **system only**. Components get boring,
self-describing names (`dispatcher`, `inference_host`, `job_runner`) — the old
world needed an authoritative device-roster memory just to decode `Granny`/
`Hex`/`Scraps`, an orientation tax paid by every fresh mind, every session.
Self-naming code needs no roster.

**The name forces the content — and the naming is half the point (Akien,
2026-07-15).** Anything in the system that carries an intention carries its
**why**, where applicable, in the artifact itself: a component's charter is
`intention+why.json`, a commons store's is `_charter+why.json`. A name that omits
the why invites an artifact that omits the why — and the why is the one thing that
lets a mind *adjudicate* rather than pattern-match (CP3: there's always a why). So
the why is named into the file: CP3 as schema (Law 4), enforced by what the file
is *called*, not by anyone remembering to fill a field.

The naming does a second job, on the human/model side. **Languaging about a tool
in terms of its structure is how a good tool disappears** — and this works for
both minds in the loop, Akien's and CC's alike. Not disappears-as-forgotten (the
IMAP-banner rot: a tool persisting *unexamined*, no why in view) but
disappears-as-ready-to-hand: so woven into how we speak that it needs no separate
attention. Every time either of us says "intention+why" the discipline is
re-instantiated in that mind, for free. The why in the name is exactly what tells
the good disappearance from the bad — the same cut the whys always draw. Fixed at
n=1, on purpose: the rule that stops evocative names from spreading is the rule
that stops why-less artifacts from spreading.

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
     special case, no *runtime* state in the repo. (Build provenance — `state`,
     `history`, validations — is knowledge, not runtime, and does live beside
     the code; ruled 2026-07-22, see "What a charter is" below.)
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
| `~/dev/src/cairn/` (repo) | code, skills, CLAUDE.md, per-device charters + `state`/`history` + proofs + validations | class-space; git; shareable; no *runtime* state |
| `~/dev/src/CairnCommons/` (own repo — ratified 2026-07-14) | intentions (incl. the Telos), decisions, tickets, proofs, slates — grep-able JSON | *if losing it loses knowledge, it's commons*; the tester consumes from and emits to it |
| `~/.cairn/` | logs, credentials, flags, cachedstate, personal info | instance-space; never in git; composed at use-time |

**The map IS the territory:** every component directory co-locates
`intention+why.json` + implementation + `state` + `history` + `proofs/` and the
validations that sealed them. Opus gets briefed by standing in the directory.
The tester refuses to run a component with no intention, so the map cannot rot
apart from the code.

**What a charter is (ruled 2026-07-22):** a component hosts *many* intentions and
tickets over its life, so the charter is not one intention — it is their
**summary**. Two cadences that separate by provenance:

- `intention+why.json` = the **summarized design**. Authored at the design level
  (our chats); the settled why + role; changes only when the design genuinely
  shifts.
- `state` = **compiled** from the component's tickets at the operational level;
  changes every resolution; never hand-edited.
- `history` = the append-only voyage. When a ticket proves out its voyage
  *freezes* here (Law 7) and its result *folds into* the charter.
- validations sit beside the `proofs/` they seal — not in `db_domain`.

These are the beside-code faces of the two levels that don't conflict (design
above, operational below). The projector move — compile a bounded view over an
append-only source — recurs at three scales: ticket (`history` → `state`),
component (intentions + tickets → the charter summary), system (charters →
the `intentions/` index). Open, deliberately: whether the middle row stays
hand-authored or is eventually compiled too.

**Stores self-describe like devices (Akien, 2026-07-14):** every artifact-type
directory in CairnCommons carries a `_charter+why.json` co-locating:
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
  intention+why.json  ← charter: what this is FOR **and why** (name forces the why)
                        — the SUMMARIZED DESIGN; authored, not compiled
  state               ← compiled from this component's tickets (never hand-edited)
  history             ← append-only; the frozen voyages of proved tickets
  *.py                ← implementation
  proofs/             ← what a hollow build couldn't pass, + the validations
                        that sealed them
```

## Repo file tree (forks ratified 2026-07-14)

Decisions: **base + devices only** (a spun-off service becomes another device —
no third category); **proof code AND proof records both beside the device**
(the records were commons-side until the 2026-07-22 placement ruling);
**skills repo-canonical + symlink, but PURGED** — a skill crosses from UU only
if it serves Cairn (e.g. `autocompact` was decided-retired yet still squats in
UU's skills dir — the IMAP-banner disease; no skill crosses on inertia).

```
~/dev/src/cairn/                  # class-space; git; no *runtime* state, ever
  CLAUDE.md                       # spine step 1 — stays minimal: laws + pointers, not prose
  MAP.md                          # this file (dissolves into intentions/tickets over time)
  pyproject.toml                  # `pip install -e .` green at all times; include = ["cairn*"]
  cairn/                          # the single import root (one heart — UU law carries)
    __init__.py                   # EMPTY/lazy forever (boot-order lesson: importing any
                                  # subpackage must never eager-import a DB-bound one)
    base/                         # the Form, embodied
      intention+why.json          # charter of the base itself (name forces the why)
      core_values.py              # CP1–CP6 frozen contract (crosses by graft, with its pin test)
      device.py                   # BaseDevice
      shim.py                     # BaseShim + the one loop primitive
      introspect.py               # Form #2 surface: intention → state → settings → …
      store.py                    # commons access + charter enforcement primitives
      proofs/                     # proof code for the base
                                  # devices sit directly under cairn/ — there is no
                                  # devices/ layer (corrected 2026-07-22 against disk)
    tester/                       # earliest device on the spine; owns the network
    db_domain/                    # the only path to 5432
    ground_loop/                  # the heartbeat, nothing else
    bus/                          # the other runtime substrate
    system_rackmount/             # the system device (host-resource predicates)
    inference_domain/             # the only path to inference
    charter/                      # the projector: state compiled from history
    sudo_relay/
    web_server/                   # cast, not yet built
    librarian/                    # not yet built
    …                             # one dir per device, ALL the same shape:
                                  #   intention+why.json + code + state + history
                                  #   + proofs/ (+ the validations beside them)
  skills/                         # canonical; ~/.claude/skills symlinks here; purged set only
  launchers/                      # cairn launch/rescue scripts; symlinked onto PATH
```

No `devlab/` — CairnCommons replaces it entirely. No `docs/` — knowledge lives
in commons, intent lives at the address it governs. Cross-cutting proofs obey
Law 6: every proof has exactly one owner — the device that owns the seam.

Companion trees (drawn once, here, for orientation):

```
~/dev/src/CairnCommons/           # knowledge; own git repo
  intentions/  _charter+why.json + telos.md + …   # first charter written (Q6)
  questions/   _charter+why.json + …              # the question corpus, with yield
  decisions/ tickets/ proofs/ slates/ sessions/ notes/
                                  # a type dir EXISTS only once its _charter+why.json does

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
- **One store:** `CairnCommons/troubles/` + `_charter+why.json`; one emit
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

## Two build layers — workflow and pre-build packet (2026-07-15)

A build request to an LLM fires a set of *pre-build* steps before any code is
emitted — orient, constrain, deconstruct, plan — that the model runs as internal
cognition and externalizes as a "build packet" (the plan plus its supporting
structure, assembled through tool calls). Both Delta Dental's Copilot work and UU
moved those pre-build steps out of the model into **deterministic code** — which
is inference compilation (Telos 1) turned on the build itself.

So the build has two layers, both graph-tree-destined:

- **Workflow (macro, external):** intention → ticket → design → **prebuild
  scripts** → build → prove. The lifecycle a work item travels; a build/sprint
  driver walks it, and the node's state machine forbids skipping (Law 4 —
  physics, not a disciplined skill).
- **Pre-build packet (micro, internal):** the orient/constrain/deconstruct/plan
  cognition that *produces* the prebuild scripts. Today an oracle slot the
  resolver occupies; compiling it into deterministic scripts is the
  role-replacement staircase applied to the pre-build nexus. Built to **mirror
  the resolver's own internal steps — one module per step** (orientation,
  constraints, deconstruction, plan) — so each is independently inspectable and
  improvable as the compilation proceeds (Form #2's introspection surface,
  Telos 5).

They meet at one station: the workflow's *design → prebuild* step is where the
packet is produced. When the internal steps compile to deterministic scripts,
that station stops calling the oracle and runs structure — specimen #1 compiling
its own pre-build cognition. These pre-build steps get **ticketed once tickets
are sorted**; they are pre-build work, not lifecycle states of the intention.

## Artifacts — the converged set (2026-07-15)

Distilled from the "which artifacts do we actually need?" conversation.
Supersedes the provisional type-dir sketch above: `decisions/` and any separate
ticket layer collapse into the node.

**One carrier — the intention/ticket node.** A single fixed envelope (the storage
model already baked: *fixed node envelope, trees are first-class rows*),
recursive: **any node may have children.** There is no structural top or leaf and
no level-based type — a multi-month epic and a one-line fix are the same node
kind; either can spawn children. "Intention" vs "ticket" is a **fill-state, not a
level and not a second artifact**: casting an intention into a ticket = sorting
its fields and answering *deconstruct further, or build?* That question is
answerable at ANY time, including mid-build — building can reveal hidden children
(a small UI change spawning framework fixes), which get filed as child nodes the
parent then waits on (bottom-up proof; CP2 as structure — "this looked like a
leaf; it wasn't").

**The ticket is workflow-neutral (2026-07-15).** Because workflow rides on the
node-class, not on the node's identity, "ticket" carries no domain: an inference
ticket, a concept ticket, a review ticket, a writing ticket are the *same node*,
differing only by class. **Everybody has tickets** — Telos/CP4's "everybody"
reaching into the core primitive. This is why `/ticket` needn't be a skill and why
`decisions/` folds in: both were only ever separate because "ticket" smelled like
code. The node is the primitive; "ticket" is just its common name once cast.

Riding on every node as fields (not separate artifacts):
- the **intention proper** — claim, why, falsifier, horizon, provenance, trace-up edge
- **design, at this node's level** — scope = height; a system-wide decision rides
  on a high node, an implementation choice on a low one (so `decisions/` needs no store)
- **state** — lifecycle position
- a **pointer to its proof**
- **[nodes that will build] a prebuild packet** — a subtree, one node per
  cognitive step (orientation / constraints / deconstruction / plan), each
  independently inspectable and improvable

**Separate species (cannot ride on the node):**
- **proof** — one species, two faces: the **artifact** a hollow build couldn't
  pass (proof code, beside the device) and its **VALIDATION** — the verdict
  record, which since 2026-07-22 also lives beside the `proofs/` it seals.
  Owned by the seam's device; the node points at it. The
  VALIDATION generalizes past the build tree — see the stone below.
- **question** — the open dual of an intention; own corpus with yield. An
  answered question that becomes a commitment turns into an intention node.
- **trouble** — machine-filed failure observation (already its own species).

**Continuity records (a different axis — not the build tree):**
- **session** — the conversation as an immutable journey (truth-class).
- **slate** — the day's cache over recent sessions (derived, rebuildable).

Wildcard: `notes/` (frictionless capture) — keep or fold later.

**Format:** every artifact type is JSON — grep-able, one record per node/row,
validated against its store's co-located `_charter+why.json` template. Physics, not
policy: the single emit chokepoint refuses a write that doesn't conform (the
"stores self-describe" rule above, applied to all seven types).

## VALIDATIONS — the tester's greppable record of what's proved (2026-07-15)

The second face of the `proof` species, elevated to a first-class store and
handed to the tester. **The tester stays a top-level device, and emitting
VALIDATIONS is part of its remit.** It is the system's **notary** as well as its
**mechanism for the work**: it does the proving (runs the proof, gates the build)
*and* attests the result (stamps the VALIDATION into the record). The verdict and
the seal come from the same hand. Every time it proves anything it writes one
greppable JSON row: `claim, caller, date, method, verdict, evidence, falsifier,
horizon`. falsifier + horizon ride along because a VALIDATION is still a
best-guess-with-an-expiry (Law 3) — the record carries how you'd know it went
stale, so "I validated abc on the 14th" can itself expire.

**Generalized past the build tree.** A VALIDATION is not only for
intention/ticket nodes; it covers *any measured claim*, including environmental
facts — "the inference host answered at 09:14 with these models loaded." A
build-node proof is one kind of VALIDATION, not the whole of it.

**Two access patterns, both Law 1:**
- **produced** automatically — the tester emits on every prove; the resolver's
  work becomes structure instead of being re-derived.
- **consumed** on a hint — a mind that suspects "this is already validated" greps
  the validation records instead of proving it again. Not an automatic gate; a
  cache you consult on a hunch ("I think that's been validated" → go look).

**Where they live (ruled 2026-07-22).** A VALIDATION sits beside the `proofs/`
it seals, in the directory of the device that owns the seam — not in a
`db_domain` table and not in a single flat store. Greppability comes from the
tree, not from centralization. *Open debt:* the projector's own green
VALIDATION (`test_projector.py passes under python3`, 2026-07-21T15:50:30) is
still in the `validations` table and is the first record slated to move.

**Measured motive.** Absent this store, a failed *reach* gets reported as a
*verdict* — "the inference box is down" — with nowhere to check its actual
last-known state. VALIDATIONS fixes the *nowhere-to-look* half: a durable record
of "it answered at 09:14" to consult before concluding anything. The other half —
not mislabeling "I couldn't reach it" (measured) as "it's down" (unmeasured) — is
CP1 discipline on the inference seam, tracked separately.

## Workflow + starting skills (first cast 2026-07-14, converged 2026-07-15)

First cast from specimen #1 — the founding conversation itself, run by hand.

```
/intent <desc>  → birth a node (a new track or an aside); unpack WHAT/HOW,
                  trace to Telos
  /challenge    → any time before /sorted: adversarial pass on the design /
                  conclusions — better approach? prior art? do we back up?
→ /sorted       → assert "all points wrapped" → inward completeness check
                  (assumption? missing? falsifiable? collides?) → cast the node
                  (type it → bind its class's gates) → spawn children to
                  deconstruct, and/or reach an escalation when stuck; survivors
                  file to CairnCommons (filing is the consequence, not /sorted)
→ build         → CC.0/CC.1/aider by difficulty, under the tester's network
→ prove         → the class's prove-gate: tester VALIDATION for code, quorum
                  signature for a concept piece; children prove before parents.
                  green → parent may prove; red → CP2 data, kick back to design
                  or new questions into the corpus (kick-back is a disposition)
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

**Starting skill roster — converged (2026-07-15).** The ten-skill sketch, run
against the gates + per-node-class model, distilled to a smaller set on three axes.
Each surviving skill enters with its own charter. (Supersedes the earlier 10.)

**Skills are links into the repo, not copies.** One source of truth per skill —
wherever a skill is installed, it points back at the file in `cairn/`. Nothing to
sync, nothing to drift: the same no-copy reflex as cairnmap and co-located charters.

| Axis | Skill | Role |
|---|---|---|
| **Work loop** | `/intent` | birth a new track or aside (a node opens in intention fill-state) |
| | `/challenge` | adversarial pass on the design / conclusions, **before** `/sorted` — harden the thinking while it forms; also runs on any artifact on cadence (e.g. CLAUDE.md) |
| | `/sorted` | resolution pivot: assert "all points wrapped" → fire the inward completeness check → spawn children (deconstruct) and/or reach an escalation → resolve. Casting lives here; filing is a *consequence*, not the meaning |
| **Utilities** | `/note` | frictionless capture |
| | `/commit` | interim checkpoint (durability-of-stones is a *gate*, not this skill) |
| | `/loadslate` | session open |
| | `/saveslate` | session close |

**One pose, three placements** — why `/challenge`, `/sorted`'s check, and the
advisor don't collide: `/challenge` is adversarial on the design *before* the claim;
`/sorted`'s check verifies *coverage* at the claim; the advisor is adversarial *when
stuck*. Same pose, different whys.

**Escalations — reached when stuck; a ladder, not a roster skill.** Cheapest first:
back up and re-question · **`/advisor`** (built-in, Opus, adversarial — zero build) ·
**bounded Fable subagent** (independent *because* its context is limited — the
working Fable path; Fable-as-configured-advisor errors on every call) · review the
field / state-of-the-art · **ask Akien** (the signature-gate escalation). CP1 with
teeth: stuck → escalate, don't confabulate; CP2 right behind it.

**Folded into the ones above, from the ten:** `/ticket` → not a skill (casting +
child-spawn live in `/sorted`); `/outcome` → the tester's VALIDATION (or a `/note`);
`/next` → not in the starting set; it arrives once the graph is worth querying.
Disambiguation: the **challenge gate** (the inward check `/sorted` fires — §4.2 above)
is a different thing from the **`/challenge` skill** (the pre-sorted adversarial pass).

Not crossing (for now): sprint family (returns when a dispatcher needs it), day-close
(folds into `/saveslate`), audit-* (absorbed into `/challenge`), everything unnameable
(stays in quarry).

## Gates, not supervisors — the workflow is gated transitions on the node (2026-07-15)

The tester's prove-gate and cairnmap's recompile-gate are one pattern: a **gate**
is a *mandatory post-condition on a state transition, enforced by physics* (Law 4)
— not a person who remembers to check. A node cannot advance past a gate until the
gate's condition holds.

**This is the cooperative-peer model made structural (Akien's build style;
ratified 2026-07-15).** A supervisor is policy — someone trusted to ensure a step
happened. A gate is physics — the transition refuses until it did. Coordination
comes not from an authority above the peers but from the shared state machine they
all pass through: peers perform transforms, gates validate the handoffs, nothing
supervises anything. ("Supervisor / manager" vocabulary imported a hierarchy Cairn
does not build with — deleted.)

**The pipeline is not an object; it is the shape of a node's required gates.**
- *pipeline definition* — which gates, in what order, for a node-class — is a
  charter, owned like any charter. One record.
- *pipeline instance* — where THIS node is — is the node's `state` field, owned by
  whoever owns the node. Nothing new to own.
So *"the state of the tickets is the state of all things, always"* (Akien): no
orchestrator holds a second copy of position to drift from the truth. The global
"what's in which phase, consumed by which next" view is a **zero-inference query
over node states** — the cairnmap move — derived on demand, never stored.

**Ownership stays put; the baton of action passes (Law 6).** A node keeps its one
owner (who gates writes). What moves phase-to-phase is *which peer is invited to
act next* — and that invitation runs through the owner's gate (Law 6: delegation
only through the owner's gate, never ambient). Next hand, same owner — not a
transfer of ownership. This is what stops a cooperative hand-off from decaying
into ambient write-access.

**Every wall is a gate; gates differ only in check-type — none is a person with
authority:**
- **proof gate** — the tester: a hollow build couldn't pass (build → done).
- **derivation gate** — cairnmap recompiles and its completeness proof is green
  (skill → done): a skill does not ship until the help that indexes it is current.
- **signature gate** — a named owner/ratifier signed (Akien on a map stone;
  `/sorted`'s surviving intentions). Judgment, still physics — the transition
  refuses without the signature.

Three check-types, one shape, zero supervisors: even human judgment enters as a
required signature on a transition, not a manager standing over the work. And the
"rules awaiting physics" in CLAUDE.md are exactly gates whose enforcement is still
an IOU — including durability ("every stone committed + pushed"), which belongs on
the emit chokepoint as a gate, not on a `/commit` skill someone fires. A skill
invented to *force a behavior* is policy standing in for a missing gate. (That does
not retire `/commit` — a commit is also an interim artifact, a non-terminal
checkpoint in the fluid middle; the *skill* keeps that role, the *gate* takes the
durability-of-stones role. They collide only under an exclusive-and-terminal
reading, which the keystone forbids.)

**Workflow is per-node-class, bound when the node is cast (2026-07-15).** Because a
pipeline is just the gate-set on a node-class, different *kinds* of node carry
different workflows — selected when `/sorted` casts the intention (casting is a step
inside `/sorted`: type the node → bind its gate-set; there is no separate `/ticket`). Invariant across every class: it gets *proved* and it
*feeds back to origin on failure* (Laws 3 + 8, the keystone). Variable per class:
which gate, which check-type. A **concept piece** won't yield code — it is proved by
a **quorum signature gate** (N humans review + sign), a variant of the signature
check-type, and it kicks back on rejection exactly like a red build. This needs
*zero new artifact types*: it is a different value in the node-class field, and the
VALIDATION schema already records it (`method = "review by N experts"`, `caller = the
reviewers`). Consequences:
- for human-proved nodes the **verdict** (reviewers) and the **seal** (notary) are
  *different hands* — so "verdict and seal from the same hand" is a code-proof
  property, not universal; the tester stays notary-for-all but mechanism-for-code-only.
- **two-walls reconciles:** Wall 1 (challenge-at-intent) is universal and identical;
  Wall 2 (prove-at-close) is universal in existence, per-class in check-type; a class
  may hang extra gates between them (a skill node adds the cairnmap recompile-gate).
- **node-class definitions are themselves owned charters** — a grep-able library
  (`code-seam`, `concept-piece`, `skill`…); a class cannot exist without writing down
  what it is for. Discovered as tickets demand them, not pre-seeded.

## cairnmap — the help surface, compiled from charters (2026-07-15)

The system's reference: the main source of help, the answer to *"what can I do here,
and how."* Others will use it; the query-commands built later (list open tickets, …)
list themselves here too. Three rulings (Akien, 2026-07-15) fix what it is — **a view,
contextual, reference-only.**

**Compiled, not authored — zero inference.** cairnmap is a deterministic projection
`render(charters, context) → surface`, no model in the loop. Law 5 already makes every
command co-locate its charter (what it is for, why, how to invoke, state); cairnmap
renders those. It cannot drift, because it is derived: regenerate → current. A
hand-written help page is the exact schema-apart-from-data rot that killed the quarry's
docs. This is also Telos 1 on the surface people most reflexively hand to an LLM —
"explain what I can do," with the inference compiled out.

- **A view, not a device (ruling).** Emitted by the same presentation surface the web
  UI and tester render through ("the same protocol the tester probes and the web UI
  renders", above). Inherits that seam; nothing new to own (Law 6).
- **Contextual — v0 scopes by *where*, not *who* (ruling).** It renders what is
  available *here* — surface / location / state — the runtime twin of Cairn's founding
  move: a mind is briefed by standing in a directory and reading its `intention+why.json`;
  a caller is briefed by standing in a context and asking cairnmap. The next scope-key
  axis is *who* (the asker's ownership, Law 6 — you see only what you may invoke):
  designed-in, and lands when the "others" arrive. v0 is single-user.
- **Reference only (ruling).** A pure presentation surface (Law 7): it describes
  commands, it does not run them. Invocation stays with the commands. The web UI may
  add navigation later without changing what cairnmap *is*.
- **One source, many surfaces.** Chat command *here* (v0); a key web-UI concept
  *there* (design-only until the web server lands on the spine). Same charter truth,
  different renders.

**Its proof is the derivation gate — completeness both ways.** Falsifier: every
charter'd command appears, and nothing without a charter appears. An undocumented
command is *impossible* — a command with no charter can't run (the tester refuses it)
and can't render (cairnmap won't show it). So a `skill` node does not reach `done`
until cairnmap recompiles green; that recompile-gate is the `skill` node-class's extra
gate (per the gates stone). cairnmap is thus not a doc you trust but a live check that
the command-set and the help-set are the same set.

**The charter is the help.** Zero inference means cairnmap can only show what the
charter already says plainly — so a confusing help entry is a bug *in the charter*,
fixed at source. The learning loop closes on the help surface: help quality ≡ charter
quality, by construction, feedback landing at the point of creation.

**Relation to MAP.md.** As this map dissolves into intentions + tickets, cairnmap is
the rendered projection of those same records — the reader-side destination of that
dissolution. The name kinship is deliberate.

## The node state-machine — states as summons (2026-07-17)

The `state` field (above, 'Gates, not supervisors': state IS the pipeline instance)
gets a vocabulary. A node's state is not a past-tense label of where it has *been*;
it is an **imperative that summons the peer who acts next** — the cooperative-peer
model made literal. A peer watches a state; a node entering it wakes the peer
(currently the resolver, occupying each socket by hand — the role-replacement
staircase; later a trained agent, measured out at the resolver's rate). So the state
machine *is* the dispatcher — the get-Akien-out intention becoming architecture.

**The grammar carries the semantics** (naming stone: the name forces the content):
- **`-ME` = a summons** (a demand for a peer): `THINKME` · `TICKETME` (decompose me
  into children) · `BUILDME` · `PROVEME` · `LEARNME` (learn *from* me — I am
  material, harvest me into the trees) · `REVIEWME` (concept-piece quorum).
- **no `-ME` = the node's own condition** (settled or active): `PROVED` (passed its
  gate, resting, still carrying falsifier+horizon — grazed by the background loop)
  and `LEARNING` (a standing driver, actively collecting/transforming). Off-path
  dispositions carry their why: `DROPPED` (no trace-up at intent), `SUPERSEDED`,
  `RETIRED` (question lost tenure).

**Two rests, both inside the one loop, neither terminal:** `PROVED` = learned-FROM
(object, passive); `LEARNING` = learning (subject, active). There is no `RUNNING` —
Cairn has no uninstrumented execution (journeys at every chokepoint, every driver
carries its why, VALIDATIONS on every measured claim), so anything running is
emitting evidence, so anything running is *learning*. "Just running" would be the UU
silent-failure disease. Low-yield running is low-yield LEARNING — a yield measure
(T5.1), not a separate state.

**`TICKETME` vs `BUILDME` is /sorted's deconstruct-or-build fork** named as states:
TICKETME spawns children (a parent); BUILDME is a leaf. "Waiting on children" is
*derived* (a parent whose children aren't all PROVED), not stored — the
zero-inference move. Back-edges need no special state: a kick-back re-enters an
earlier `-ME` (severity = how far back; very-wrong trips the ask-Akien escalation),
with a trouble/question attached and the loop recorded in the journey.

**The workflow is a versioned, mutable, greppable string** with the cursor in
brackets: `code-seam@v1: THINKME → TICKETME → BUILDME → PROVEME → LEARNME →
[PROVED]`. Stored on the node — the strongest form of 'state IS the pipeline
instance' (self-contained; no external orchestrator possible). Consequences:
- **migration by find-and-replace.** Many workflows — and many *versions* of one —
  run in flight; changing a workflow asks "revise those carrying it? sometimes yes,
  sometimes no," and the answer is a string edit. Versions are immutable and
  version-stamped, so divergence-from-current is a *named, chosen, journaled*
  un-migration, not silent rot — a stronger anti-drift property than pure-derive,
  which would *force* every change onto all in-flight nodes silently. Free when the
  edit is downstream of the cursor (blind replace); a judgment call when it
  touches/precedes the cursor (where does the cursor land?). Every edit is
  owner-gated, chokepoint-validated against a known workflow, and journaled.
- **class is not frozen at cast** — it *is* the current workflow string. A code
  ticket becomes a driver by editing its terminal (`… → LEARNING`); the node that
  *built* a sensor becomes the node that *runs* it. Identity lives in the journey,
  not the workflow-of-the-moment.

**Peers wake to a poke, not a mode.** (RESHAPED 2026-07-18 — the "two modes" +
trigger-enum framing below was superseded; authoritative model:
`CairnCommons/intentions/I-heartbeat-callbacks-and-bus.md`.) A peer is woken by a
CALLBACK firing — "call X when this trigger is true", where a trigger is *anything
that evaluates to true* (not the closed `interval/date/quantity/a-state` enum, which
was a reification). Reactive (wake on state entry: builder ⟵ BUILDME) and scheduled
(wake on an elapsed interval / an accumulated queue / a resource line) are just
different predicates, one firing path. Firing lives in the SHIM on the heartbeat
pulse (`ground_loop` is ONLY the beat); the poke crosses the **bus**. The "sleep"
consolidation is the same — a callback the PROVED graze sets.

**The operational-driver primitive (a node-class).** A standing node whose whole
body is `(trigger, method-pointer, why, sources/targets)`, resting in LEARNING — the
declarative-data idea survives, but as the CALLBACK species now (immutable worker),
distinct from the mutable TICKET. NB the falsified hypothesis: "the `ground_loop` is
that generic executor" was a GOOF — the ground_loop is only the heartbeat; a device
resolves its own method internally and its shim fires it (see the design doc). The
method-registry (proven-space, Law 8) was retired with the executor and RETURNS with
the emit-chokepoint. Guards unchanged: a method resolves to proven-space (Law 8),
writes route through each target's owner's gate (Law 6).

Detail + implementation node: `CairnCommons/tickets/state-machine-physics.json`
(waits on the emit-chokepoint = base-class spine step). Ratified by Akien 2026-07-17,
reshaped with him 2026-07-18. Ownership resolved 2026-07-21 (harbor_master /sorted):
the chokepoint factors — **rules** stay base-class here, **authority** (clearance,
delegable) + **truth** (the fleet register) belong to `harbor_master`; the record's
local half is each workflow's own `history` (charter-state-history-split).

## Build order (the spine)

CLAUDE.md → skills → launchers → commons → CP/diagnostic base →
**tester + kernel-owned network** (before the first thing it guards) →
db domain → **[done: the heartbeat (ground_loop) + the bus + the base's
callback/shim + the system device (system_rackmount) + inference domain (the
compile-once path to the host — an inference request IS a ticket, 2026-07-21)]** →
web server → **harbor_master** (the workflow harbor — grants clearance for a
transition + keeps the fleet register; 'where we query open tickets'; unblocks the
web server's journey pane; waits on the charter-split + the base-class emit-chokepoint)
→ librarian-as-chatbot → graph trees (embeddings generator lives here).

Cast alongside 2026-07-21 (`CairnCommons/tickets/`): **charter-state-history-split**
— a Form change: a charter factors into a bounded `state` (cursor + window) and an
append-only `history`, a *projector* bounds the window on append (Law 1 at charter
scale; feeds harbor_master's aggregate). And **harbor-master** — the device above.
The emit-chokepoint's ownership resolved into a trichotomy (rules → base-class /
authority → harbor_master's clearance gate, delegable / truth → local `history` +
harbor register); `state-machine-physics.json` is cross-referenced, not overwritten.

(The "rack" step is subsumed: the chassis = the bus + the shims, both built
2026-07-18; there is no separate rack device. The two runtime substrates are the
heartbeat and the bus — `CairnCommons/intentions/I-heartbeat-callbacks-and-bus.md`.)

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

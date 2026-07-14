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

## The Laws (v0 — under discussion)

Present-tense contracts, dependency order; telos at the root:

1. **The resolver is spent only on the novel.** Every answered question becomes
   structure; re-deriving a settled answer is a defect.
2. **CP1–CP6 hold everywhere, including in the process that builds the system.**
   (Carried over intact from UU — the one part that was never the problem.)
3. **Nothing is known until measured.** An unmeasured claim is a hypothesis and
   is labeled as one.
4. **Every chokepoint is physics, not policy.** If a rule matters, the kernel or
   the schema enforces it; a rule living only in prose is a bug report waiting
   to be measured.
5. **Intent and implementation share an address.** Every component carries its
   intention and proofs beside its code; a component without an intention
   doesn't run.
6. **Everything has exactly one owner.** One writer per file, per table, per
   record of truth.
7. **Errors are loud at interfaces and permanent in records.** An error may
   collapse into a success shape at an interface, never in a record of truth.
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
exactly one owner — a class, an instance, or a human — and the owner is the only
writer.** Tables are provisioned only through the db domain; owner is declared
in schema metadata at creation; an ownerless table cannot come into existence.
Port 5432 is kernel-closed except via the proxy path from day one, so bypass is
never possible and there is never a migration to enforce later. Old DB contents
get the quarry treatment (ticket + proof, not pg_dump).

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

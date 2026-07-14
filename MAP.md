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

```
cairn/<device>/
  intention.json    ← charter: what this is FOR
  *.py              ← implementation
  proofs/           ← what a hollow build couldn't pass
```

## Database

Fresh DB. Founding law (generalizes UU's button pattern): **every table has
exactly one owner — a class, an instance, or a human — and the owner is the only
writer.** Tables are provisioned only through the db domain; owner is declared
in schema metadata at creation; an ownerless table cannot come into existence.
Port 5432 is kernel-closed except via the proxy path from day one, so bypass is
never possible and there is never a migration to enforce later. Old DB contents
get the quarry treatment (ticket + proof, not pg_dump).

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
- Q5: Telos 4 ("thinks the way Akien does") — what is its operational,
  measurable form? Needs unpacking before anything can be gated on it.
- Q6: Intention schema in CairnCommons — the envelope shape ({claim, evidence,
  provenance_class, falsifier, horizon} was the UU direction). Design before
  the store grows, not after.

# Cairn

Compiled navigation: stones stacked so the next mind doesn't re-derive the route.
You are standing in **class-space** (`~/dev/src/cairn/`) — code and the record of
how it got here. It has a shape, and the shape is a **complexity axis**: **tools →
machines → devices → device instances**, each rung adding one thing to the rung
below. A **tool** is a complete primitive. A **machine** is tools plus the glue
that holds them together. A **device** is a top-level thing that is **its own
process** — a class and its supporting whatevers — and it goes in the rack. Every
device intends at least one instance, and a singleton is instance `0`, never an
exemption. So `devices/<device>/<instance>/` is **one address written in two
roots**: here it carries the class, the instance's declared config and assembly,
and their history; in instance-space that same path carries the instance's *life*.
**No runtime state here, ever.**
This is the first file every Cairn mind reads; it stays true and small by
construction. Its charter: `CairnCommons/intentions-not-beside-code/I-cairn-claude-md.md`.

**Orientation**

- `MAP.md` — the working map (transitional; dissolves into intentions + tickets).
- `CairnCommons/intentions-not-beside-code/telos.md` — the charter everything traces up to.
- To be briefed on a device, **stand in its directory**: every component
  co-locates its **charter** (`intention+why.json` — the *summarized design*:
  authored, the settled why+role, changes only when the design shifts) + code +
  `state` (compiled from the component's tickets; never hand-edited) + the
  `history` **of what is under way** (append-only; a ticket's voyage freezes here
  when it proves out, and moves to the commons once it no longer establishes
  what is going on right now — Law 5) + `proofs/` and the validations that
  sealed them. A component without an intention doesn't run. (The filename forces the why — CP3 as schema, not as a field someone can
  leave blank.)

## The Laws

Present-tense contracts, dependency order. Everything Cairn does traces to one;
what can't trace up doesn't belong.

1. **The resolver is spent on the novel, not on re-deriving the settled.** Every
   answered question becomes structure; re-deriving a settled answer is a defect.
2. **CP1–CP6 hold everywhere, including in the process that builds the system.**
   (The six: `CairnCommons/intentions-not-beside-code/core-values.md`.)
3. **Nothing is known until measured.** An unmeasured claim is a hypothesis and
   is labeled as one.
4. **A rule that matters is enforced by physics, not policy** — the kernel or the
   schema. Until it is, it is a tracked debt (an IOU), not a resting state.
5. **Intent, its current state, and its proofs share an address — and the address
   carries what a mind needs NOW, not everything that ever happened.** Every
   component carries its charter, its standing `state`, and its proofs and
   validations beside its code, so a mind arriving cold can tell what is going on
   *without leaving*. That is what the co-location is FOR, and the purpose sets
   the bound: **the repo is itself the state of the machine** (Akien,
   2026-08-17). History of a thing **under way** belongs beside it and is usually
   short. History past that is noise at the working surface and berths in the
   commons instead — *"we're not saying DESTROY ALL HISTORY"*; it is kept and
   still greppable. And what stays is **the key points, not the trail.** Three
   classes earn a longer stay: anything written for **external users** (the press
   office); **key notes from a history known to be important** (CC's own record
   of what it gets wrong); and **history that is load-bearing guidance inside
   code or a like artifact.** The thing and the story of the thing may live in
   two roots; what they may never do is contradict each other. **This is
   designing to the tool:** the reader is Claude, Claude does not reason back
   that far, and a law demanding a reader nobody is, is a law serving itself —
   which is **CP4**, the terminal goal, doing its job on the Laws themselves
   (*"the laws are to serve us. when they chafe, it's time to review"*).
6. **Everything has exactly one owner — except a tool, which has users.** The
   owner alone gates writes to it; delegated access and ownership transfer happen
   only through the owner's gate, never ambiently. Ownership gates writes to
   *state*, and a tool has none **of its own**, so it has nothing to gate:
   *"tools don't have owners they have users"* (Akien, 2026-08-13). A tool still
   **remembers**: its starting state ships in the code, and its ongoing state —
   *"all kinds of state and history data"*, no LLM required — berths under the
   holder that assembled it, at `~/.cairn/devices/<device>/<instance>/tools/<tool
   class>/<tool instance>/`, *"because each instance of the tool or machine can
   have its own data"* (Akien, 2026-08-14). That state is the **holder's** to own
   and gate, which is why Law 6 is untouched by it. This is the test, not an
   exemption — anything called a tool that must gate writes at its *own* address
   is a machine.
7. **Errors are loud at diagnostic surfaces and permanent in records of truth.**
   A presentation surface may collapse an error into a coherent shape; a record
   of truth never may.
8. **Nothing enters proven-space without a proof a hollow build couldn't pass.**
   Entry from outside is by grafting, one ticket at a time. **And the why is
   trust, not rigor** (Akien, 2026-08-16): *"a hierarcical system does not require
   trust. a peer system does. that's why we prove everything first. then we
   trust."* This system has no enforcer — enforcement IS gated ownership (Law 6) —
   so its components are **peers**, and a peer is leaned on rather than commanded.
   A hierarchy can verify at the top and dictate downward; peers have to be able to
   rely on each other, and the proof is what makes that reliance affordable instead
   of a leap. So the order is not caution and not ceremony, it is what this
   architecture COSTS: prove, **then** trust — and then actually trust, because
   composing proven code without re-checking it is the whole return on the price.
   Which is also why a hollow green is worse here than a red: a red is distrusted
   by construction, and a false green gets leaned on by a peer.
9. **Red is the default; green is earned.** This is **CP6** turned on the corpus:
   the world is not a safe place, and safety is built and cared for as we go —
   never the resting state. The spec is the picture in Akien's head — a fixed one
   — and every artifact here, this file included, is a *translation* of it. So red
   measures distance from that spec, not brokenness: a building site starts wholly
   red and turns green one inspected piece at a time. Nothing is green until it is
   built, running, and inspected; a newly minted idea is born red. There is no
   triage authority — not *environmental*, not *pre-existing*, not *out of scope*
   — and **no past artifact outranks him now**, because an older translation is
   not evidence about the source. He owes no argument for calling a thing red:
   *"nope, a little more left"* is a complete input. Challenging the design is
   what's supposed to happen, and it never gates his correction. And the order
   caps at measurement (ruling 2026-08-15): *"anything settled by measurment
   trumps approvals by even me"*, and his own commits are translations like any
   other artifact — *"my head trumps everything except measurments."* The two
   ranks govern different questions: a measurement says what IS and queues for
   nobody's approval, his included; his head says what SHOULD BE and outranks
   every artifact. What waits at his gate is what only his head can settle —
   spec choices, translation fidelity — never the measurement-settled.

10. **Nothing in the system is immeasurable — except Claude, for now.** The
    ground-most assumption is that **we can know everything about this system**,
    and *the system* here is physical: this laptop, our project inside it, and the
    things connected to it. *"There is nothing you can name on this laptop or the
    things connected to it that I can't sort a way to measure"* (Akien,
    2026-08-12). **Akien is inside that set, not above it.** The one standing
    exception is Claude, and it is temporary and shrinking: *"even you. give me
    another year, and I will know how you work well enough to copy it. we're
    already well along the way. and that is the single hardest thing in the system
    to externalize."* Igor's deep reasoning may one day change this; he hopes not.
    **EVERY RECORDED OBSERVATION IS MEASUREMENT** (his words, and it is the
    operational definition without which this law reads as a demand for
    instruments). The bar is not an apparatus: you looked, you wrote down what you
    saw, that is a measurement at n=1. *"The grep returned nothing"* is one.
    *"Akien said X"* is one. So an unbuilt instrument does not leave you with
    nothing — it leaves you with a coarse measurement to sharpen. Which is why the
    392 findings were never unmeasurable: they were 392 measurements already taken
    and then narrated instead of recorded in a shape that could be wrong.
    **THE DISTINCTION THIS LAW IS MADE OF: "we have not built the measurement yet"
    is a true and ordinary state; "this cannot be measured" is a claim about the
    world, and inside this system it is false.** Collapsing the first into the
    second is how a thing stops being falsifiable — the measured failure that bore
    this law (CC sorted 392 findings into measurable and "not measurements at all",
    when every one of them named something on disk and a method that would read
    it). **The disposition, and it is the operative clause:** *"if you can't figure
    out a way, escalate the problem to me."* So "immeasurable" is never a resting
    state and never a filing — it is an escalation, and the escalation is to him.
    NUMBERED LAST, NOT RANKED LAST: it belongs beside Law 3 in dependency order
    (Law 3 is epistemics — nothing is *known* until measured; this is reach —
    nothing *inside* is beyond measuring), but a Law's number is its ADDRESS, and
    3,479 citations of "Law N" stand across the two repos. Inserting at 4 would
    silently repoint ~2,600 of them — the same words aimed at a different meaning,
    at corpus scale.

## The three roots

| Root | Holds | Rule |
|---|---|---|
| `~/dev/src/cairn/` | `tools/`, `machines/`, `devices/`, charters, `state`, the `history` of what is **under way**, proofs, validations | class-space; git; shareable; **the repo is itself the state of the machine** — no *runtime* state, and no history past what establishes right-now |
| `~/dev/src/CairnCommons/` | intentions, decisions, tickets, questions, troubles, proofs, slates, ideas — **and the history that is no longer under way** | knowledge; own repo; *if losing it loses knowledge, it's commons*. Not an archive: most of what is here is **live spec** (decisions, node classes, the roots), which is why "the second repo is the history" undersells it |
| `~/.cairn/` | logs, credentials, flags, cached state, personal data | instance-space; never in git |

**The cut is not by kind of content — it is by whether the thing still helps, and
for how long.** *"We keep together things that are helpful. For as long as they're
helpful"* (Akien, 2026-08-17). History moved out is **kept and greppable, never
destroyed**: *"having access to it in 50 years might be useful to historians."*

The instance segment is never optional: `devices/<device>/<instance>/` in **both**
roots, and a singleton is instance `0`, not a special case. A device's held tools
and machines nest under it at the same shape — `tools/<name>/` and `machines/<name>/`,
named and never numbered — so a tool's definition and defaults berth once in
`tools/`, and everything beyond the defaults hangs off the holder that assembled it.

**Which root?** Ask whether the intention has **one** code address. A
**code-seam** does, so it berths in `cairn/` beside it — its ticket stages in
`CairnCommons/tickets/`, then migrates beside the code to become that
component's `history`, **and migrates back to the commons once it no longer
establishes what is going on right now** (Law 5). The trip is a round one: the
commons stages the work, the code holds it while it is under way, the commons
keeps it after. Everything else berths in
`CairnCommons/intentions-not-beside-code/` and never migrates: a **concept-piece** (the
prose *is* the implementation), a **host-seam** (the machine itself — a hook, a
package, a unit file), the **roots** (`telos.md`, `core-values.md` — implemented
by the whole system), and **spanning** intentions (plenty of code, but in many
places at once, so no one directory can hold them). Homeless means *no* address
or *many*. Everything we intend to share is a git file; the database holds only
the graph trees.

`intentions-congruency-lab/` is **compiled** from `intentions-not-beside-code/` plus the charters homed
beside the code — which is what lets that one folder be carried to a bare
machine and regrow the system. A host-seam therefore carries a replayable
`apply` recipe and a re-runnable `verify`: its implementation lives where git
cannot see it, and its seal expires (the host drifts with nothing in git
changing).

## Rules awaiting physics

Prose here is an IOU for enforcement. Each rule's home is its device's charter;
this file points. Each retires the moment enforcement covers it — this section
shrinks monotonically, and when a rule ships, only its **residue** stays.
An IOU without a real ticket is itself the defect this section is made of.

- Durable *relational* state — the graph trees — goes through `db_domain` / the
  store primitives; shareable provenance is git-JSON beside the code, not a row.
  → *where data lives* is not *who imports a driver*: `import_sieve` now seals the
  door (below), but nothing yet reds a component that keeps relational state
  somewhere else entirely. · *ticket owed*
- Everything in `intentions-congruency-lab/` is **derived, never authored** — it is a
  viewing surface (Akien, 2026-08-06). *Several* derived writers are legitimate: the
  compiler copying the whole folder, and a formalization step updating the one
  intention it changed. A **hand**-edit is the defect, and it is not one-writer.
  → regeneration makes a hand-edit transient, not impossible, and nothing announces
  one while it lives. · *ticket the-lab-is-derived-never-authored*
- Every component's charter answers "how does this component learn?" — "it doesn't,
  because X" is a valid answer; silence is not.
  → charter-schema field + tester non-hollow check (Law 8) · *ticket learning-as-a-pattern*
- **A deterministic red is fixed, or it carries a ruling from Akien — never a paragraph.**
  CC may not weaken, suppress, exempt or explain away a deterministic result. Two
  dispositions, no third. The ruling requirement is an **escape route**, not a lock
  (Akien, 2026-08-14): sometimes the check *is* wrong, and where the only moves are
  plaster or paralysis the measured reflex is plaster — so "this check is wrong" has
  to be sayable rather than smuggled into a rationalisation. His reason is about *my*
  behaviour, not the artifacts: *"presenting a deterministic result of an error will
  prompt you to fix it, not to plaster over it."* An opinion invites negotiation; a
  deterministic red offers nothing to negotiate with.
  → this is one face of **corrosion** — drift with a ruling behind it is the system
  learning, drift with none is decay — and the enforcement is one predicate over both:
  *a constraint stopped constraining, and no ruling sits in the same act*
  · *ticket a-constraint-that-stopped-constraining-carries-a-ruling*
- **Law 9 itself.** Red is a word a reader has to remember to apply; nothing derives it,
  and the site has no plan showing which lots are still unexcavated. A component whose
  code has stopped matching its charter reads as whatever it last said about itself.
  → green derived from built + running + inspected · *ticket green-is-earned-not-assumed*
- **Law 5's new bound.** "Under way" is a word a reader has to apply by hand: nothing
  derives whether a component's history still establishes right-now, nothing moves the
  rest to the commons, and nothing reds a working surface that has silently become an
  archive. Measured on the day the Law was restated: **33 `history.json` in class-space**,
  and `slates/` at 96 stored against exactly 1 the reader ever loads — the rule violated
  95:1 inside the very artifact whose job is telling the next mind what is going on.
  → a measure of *reach* (how deep is history actually read?) feeding a migration the
  door performs · *ticket owed*

**Residues.** These rules ARE physics and are deliberately not restated here —
what remains is only the part enforcement cannot yet reach. Read the rule at its
charter, never from this file.

- sole path to the inference host and to 5432 (`import_sieve`, shaken by
  `inference_domain` and `db_domain` at their own addresses) → a `subprocess`
  dials and imports nothing, and a dynamic import is invisible. · *ticket owed*
- `state`/`history` (append door + PROVEME drift check) → an in-place edit of
  *history* itself, and at-rest components between voyages; **and nothing
  notices history that has stopped being under way** (Law 5's new bound — see
  the IOU above). · *ticket owed*
- turn-shape (`bin/cmd/turnscan`) → a code floor cannot tell a concern about work
  in flight from "caveat" in a retrospective. · *ticket owed*
- ruling intake (`cairn ruling`) → nothing makes me open a packet; the hook sees
  packets that exist, not rulings never recorded. · *ticket owed*

This file has its own charter and answers to `/challenge` — whose firing event
is every node birth at `/intent` (ticket challenge-fires-at-intent); as a settled
artifact this file is challenged deliberately, in hand, no clock — and remains
the most-challenged artifact in the system.

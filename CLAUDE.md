# Cairn

Compiled navigation: stones stacked so the next mind doesn't re-derive the route.
You are standing in **class-space** (`~/dev/src/cairn/`) — code and the record of
how it got here; no *runtime* state, ever (that lives in instance-space).
This is the first file every Cairn mind reads; it stays true and small by
construction. Its charter: `CairnCommons/intentions-not-beside-code/I-cairn-claude-md.md`.

**Orientation**

- `MAP.md` — the working map (transitional; dissolves into intentions + tickets).
- `CairnCommons/intentions-not-beside-code/telos.md` — the charter everything traces up to.
- To be briefed on a device, **stand in its directory**: every component
  co-locates its **charter** (`intention+why.json` — the *summarized design*:
  authored, the settled why+role, changes only when the design shifts) + code +
  `state` (compiled from the component's tickets; never hand-edited) + `history`
  (append-only; a ticket's voyage freezes here when it proves out) + `proofs/`
  and the validations that sealed them. A component without an intention doesn't
  run. (The filename forces the why — CP3 as schema, not as a field someone can
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
5. **Intent, its voyage, and its proofs share an address.** Every component
   carries its charter, its `state` + `history`, and its proofs and validations
   beside its code. The thing and the story of the thing cannot drift apart.
6. **Everything has exactly one owner.** The owner alone gates writes to it;
   delegated access and ownership transfer happen only through the owner's gate,
   never ambiently.
7. **Errors are loud at diagnostic surfaces and permanent in records of truth.**
   A presentation surface may collapse an error into a coherent shape; a record
   of truth never may.
8. **Nothing enters proven-space without a proof a hollow build couldn't pass.**
   Entry from outside is by grafting, one ticket at a time.
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
   what's supposed to happen, and it never gates his correction.

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
| `~/dev/src/cairn/` | code, skills, charters, `state`/`history`, proofs, validations | class-space; git; shareable; no *runtime* state |
| `~/dev/src/CairnCommons/` | intentions, decisions, tickets, questions, troubles, proofs, slates | knowledge; own repo; *if losing it loses knowledge, it's commons* |
| `~/.cairn/` | logs, credentials, flags, cached state, personal data | instance-space; never in git |

Runtime instances live at `~/.cairn/devices/<device>/<instance>/`; a singleton
is instance `0`, not a special case.

**Which root?** Ask whether the intention has **one** code address. A
**code-seam** does, so it berths in `cairn/` beside it — its ticket stages in
`CairnCommons/tickets/`, then migrates beside the code to become that
component's `history`. Everything else berths in
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
- **Law 9 itself.** Red is a word a reader has to remember to apply; nothing derives it,
  and the site has no plan showing which lots are still unexcavated. A component whose
  code has stopped matching its charter reads as whatever it last said about itself.
  → green derived from built + running + inspected · *ticket green-is-earned-not-assumed*

**Residues.** These rules ARE physics and are deliberately not restated here —
what remains is only the part enforcement cannot yet reach. Read the rule at its
charter, never from this file.

- sole path to the inference host and to 5432 (`import_sieve`, shaken by
  `inference_domain` and `db_domain` at their own addresses) → a `subprocess`
  dials and imports nothing, and a dynamic import is invisible. · *ticket owed*
- `state`/`history` (append door + PROVEME drift check) → an in-place edit of
  *history* itself, and at-rest components between voyages. · *ticket owed*
- turn-shape (`bin/cmd/turnscan`) → a code floor cannot tell a concern about work
  in flight from "caveat" in a retrospective. · *ticket owed*
- ruling intake (`cairn ruling`) → nothing makes me open a packet; the hook sees
  packets that exist, not rulings never recorded. · *ticket owed*

This file has its own charter and answers to `/challenge` — whose firing event
is every node birth at `/intent` (ticket challenge-fires-at-intent); as a settled
artifact this file is challenged deliberately, in hand, no clock — and remains
the most-challenged artifact in the system.

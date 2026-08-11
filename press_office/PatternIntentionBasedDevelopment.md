# Pattern — Intention-based development

### Put the *why* in the artifact's name, and the map cannot drift from the territory

> **The move.** Every component directory holds a file called `intention+why.json`. Not
> `intention.json` with an optional `why` field — the plus sign is the enforcement. Beside it
> live the code, a compiled `state`, an append-only `history`, the proofs, and the seals those
> proofs earned. There is no separate documentation tree, so there is nothing to fall out of
> date.

---

## 1. The measured failure

Cairn's predecessor kept its architecture in a design folder and its behaviour in a source
tree. Both were maintained. Neither was wrong on the day it was written.

By the time anyone measured, an inference proxy had been mandated for a month while six live
files still opened raw HTTP to the host, and a database proxy was used by twenty files while
**forty live files called `psycopg2.connect` directly.** Dozens of components had been failing
silently for months, producing success-shaped records the whole time.

The design folder said none of this. It could not — it was a separate artifact, and it drifted
on discipline. Discipline degrades quietly and produces no signal while it does.

The root cause, stated at the time and unchanged since:

> **The map was always a separate artifact from the territory.**

There is a second, smaller measurement behind the specific file *name*. A schema with an
optional `why` field gets a `why` field filled in for the first three components and left blank
for the next thirty. Naming the file `intention+why` means an author cannot produce the
artifact without producing the reason — the requirement is in the filename, not in a reviewer's
memory. This was caught at n=1, before there were thirty components to go back and fix.

---

## 2. The pattern

A component is a directory. Standing in it briefs you completely:

```
cairn/librarian/
  intention+why.json     the charter — the summarized design
  trees.py  loop.py …    the code
  state.json             COMPILED from history; a cursor plus a bounded window
  history.json           append-only; the ticket's voyage, frozen when it proved out
  proofs/                proofs a hollow build could not pass
  validations/           the seals those proofs earned — each with falsifier and horizon
  probes/                the watches this component carries, if any
```

The charter is the **summarized design**, not a changelog and not a README. It is authored, it
carries the settled why and role, and **it changes only when the design shifts.** Its fields:

- **what** — the component, described as built.
- **why** — the reason it exists, in terms of a lived symptom. Most `why` fields in Cairn name a
  date and a specific thing that went wrong.
- **how_it_learns** — the required question (see §2.3).
- **owner** — who gates writes, per Law 6.
- **falsifier** — what would make this component red.
- **traces_to** — the axioms it answers to. **If nothing traces, it does not belong.**
- **gates** — which gates this component is bound to.

### 2.1 `state` is a pure function of `history`

`state.json` is regenerated from `history.json` on every append and never hand-edited. It cannot
drift from the log because it is *derived from* the log.

This came from a measurement rather than a preference. `state` had grown into the largest and
most mutable field in the charter — 17–24% of the file every new reader opens first — so the
file bloated without bound and the most-read artifact in the system was mostly stale status.
Splitting them and compiling the window makes the bound structural.

### 2.2 The charter is what makes a component a component

Not a `setup.py`, not a `__init__.py`, not being importable. **A component without a charter
does not run** — a build sieve called `charter_on_disk` reds it.

That sieve exists because the orientation instrument flagged *its own* missing charter on
2026-07-27. The measurement seeded the rule.

### 2.3 "How does this component learn?"

Every charter must answer it, and **silence is not an answer.** *"It doesn't, because X"* is
valid and common. The answers in the corpus are genuinely various:

- `db_domain` — *it doesn't;* "it is the fixed floor others build on."
- `import_sieve` — *it doesn't, and the reason is the point:* "this is a mesh, and a mesh that
  adapts is not a measurement." What learns is the mesh's *precision*, by firing wrongly once
  and being narrowed, with the correction written into the code as a permanent tooth.
- `build_inspector` — *that is the whole point:* "we find a new thing, we add a sieve."
- `ground_loop` — the heartbeat does not learn; the probes hung on it do.

The question's real value is second-order. Because it is asked of every component, a component
that has quietly stopped being what it says it is has **one specific field where the lie must be
maintained** — and maintaining it turns out to be harder than correcting it. On 2026-08-10 the
harbor master's `how_it_learns` read *"the precondition is met (an honest, non-drifting record
of every cleared move)."* Measurement found that **zero crossings had ever been cleared.** The
field was rewritten to say so, in the same breath, and the falsifier section was amended to
record that the component's own stated test was being failed.

### 2.4 Three roots, so "which artifact goes where" is answered once

| Root | Holds | Rule |
|---|---|---|
| `cairn/` | code, charters, `state`/`history`, proofs, validations | class-space; git; shareable; *no runtime state, ever* |
| `CairnCommons/` | intentions, decisions, tickets, questions, troubles | knowledge; own repo; *if losing it loses knowledge, it's commons* |
| `~/.cairn/` | logs, credentials, flags, cached state | instance-space; never in git |

The heuristic that settles arguments: **if you would need to gitignore it, it is in the wrong
root.** That test caught a repo-local virtualenv — machine-specific compiled bytes, therefore
runtime state by any reading. It moved to instance-space.

Which root does an intention berth in? Ask whether it has *one* code address. If it does, it
berths beside that code. If it has none — the prose *is* the implementation — or if it has
*many*, it is **homeless** and berths in the commons. Homeless means *no* address or *many*, and
both are legitimate.

---

## 3. How it is enforced

**Physics today:**

| Rule | Mechanism |
|---|---|
| A component has a charter | `build_inspector`'s `charter_on_disk` sieve reds the build |
| A component has proofs | `proofs_exist` sieve (Law 8) |
| `state` equals `project(history)` | `state_is_projection` sieve — a hand-edited `state.json` reds |
| `history` is append-only | writes ride a projector door; there is no in-place edit path |
| An intention traces up | the `/intent` door refuses a birth whose `traces_to` is empty, and requires the exit `routed_out` to be *recorded* rather than reasoned to |
| Every charter has a copy in one portable folder | `intentions_model_compiler` regenerates `intentions-congruency-lab/` whole; a copy must be byte-identical to its source, and a deleted source takes its copy with it |

**Still prose (tracked as debt, per Law 4):**

- **A charter that has stopped matching its code reads as whatever it last said about itself.**
  Nothing derives green from *built + running + inspected*. This is the pattern's open flank and
  is filed as ticket `green-is-earned-not-assumed`.
- An in-place edit of *history* itself, and at-rest components between voyages, are outside the
  append-door's reach.
- The `how_it_learns` field is required by convention; the charter schema does not yet refuse a
  charter that omits it (ticket `learning-as-a-pattern`).

That list is published, in the repository's front file, under a heading that says these are
IOUs. The section is designed to shrink monotonically. **An IOU without a real ticket is itself
the defect the section is made of.**

---

## 4. What it costs

**Charters are long.** The largest run several thousand words. That is deliberate — the charter
is the summarized *design*, and the alternative to a long charter is a design that lives in
someone's head. But it means a component is not cheap to create, and creating one before you
know what it is will produce a charter you rewrite.

**Every design shift is two writes.** Change the code, change the charter. Cairn additionally
requires that any charter write poke the model compiler in the same act, so the portable folder
stays current. This is real friction and it is the price of the co-location.

**Supersession is verbose.** Because a charter is a record, corrections append rather than
replace: the harbor master's `how_it_learns` now carries the false claim, the measurement that
killed it, and the later measurement that partly restored it, separated by `||`. Readable, but
the file grows.

**It does not survive a lazy author.** Nothing in the mechanism forces a *good* why. It forces a
*present* why. A charter full of plausible-sounding reasons that nobody measured passes every
gate described here.

---

## 5. What would falsify this

- **A charter and its code disagree while everything stays green.** This is the whole bet, and
  the system currently cannot detect it. Until the green-is-earned ticket lands, treat this as
  an open flank rather than a solved problem.
- **The `why` fields become generic.** If a random sample of charters stops naming dates,
  measurements and specific failures, the field has decayed into a formality and the pattern is
  costing more than it returns.
- **`how_it_learns` becomes uniformly "it doesn't."** The variety is the evidence that the
  question is being answered rather than dispatched.
- **A second documentation tree appears.** The moment a `docs/` folder describes components, the
  drift the pattern exists to prevent has a new home.

---

## 6. What is built, and what is red

**Built.** 39 charters on disk, all 39 compiled into the help surface, with a **green**
completeness verdict — every command, skill and component traces to a charter, and nothing
renders without one. 29 append-only histories carrying 324 journaled crossings. 69 validation
records. The three sieves that make the charter mandatory, the proof mandatory, and `state`
non-authorable.

**Red.**

- No derivation of green from *built + running + inspected*. A component between voyages reads
  as its last self-description.
- The `how_it_learns` requirement is convention, not schema.
- `intentions-congruency-lab/` is derived-never-authored, but regeneration only makes a
  hand-edit *transient*, not impossible, and nothing announces one while it lives.
- The corpus is 28 days old and has one author. Whether the discipline survives a second person
  is untested and currently untestable.

---

*Pattern document, `press_office/PatternIntentionBasedDevelopment.md`. Part of the Cairn
pattern series; the spine is [`CairnArchitecture.md`](CairnArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*

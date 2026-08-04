# The Cairn Workflow

*Every step, every start, every end, every gate — and how a gate opens.*

**This file is the source of truth for the workflow.** If the workflow changes, the
change lands here first and everything else follows from it. A skill, a charter, a
ticket or a device that disagrees with this document is wrong, and the disagreement
is a defect to fix rather than a difference to reconcile.

That is a narrow claim, and the narrowness matters. This document owns **which steps
exist, in what order, what fires each one, what ends it, and which gate stands at
it.** It does not own the *field list* of any particular door — those compile live
from the door's own charter, because a component's contract lives beside its code
(Law 5), and restating it here would create two places for one fact. So the gate
column below **cites** what a door requires; it never re-authors it.

---

## 1. The workflow

| step | trigger skill | completes skill | gate requires |
|---|---|---|---|
| **capture** | `/idea [prose]` — *not built* | — (we move on) | prose exists; interpretation deferred |
| **intend** | `/intent [idea]` | fire intent | 8 fields, compiled live |
| **design** | `/design [intention]` — *not built* | `/sorted` | 12 fields, compiled live |
| **chart** | `/chart` | 7 chart doors | unreadable — schemas in code |
| **build** | `/sail` | `/sail` | not declared |
| **test** | probe watching `VALIDATEME` | `persist_validation` | 8 VALIDATION fields |
| **watchme** | probe on validation complete | — (the probe is created) | — |
| **learn** | — (feedback arrives) | the creating intention | — (a slope; see §4) |

Eight steps. Not a fixed pipeline that every piece of work marches down — **a
catalog**, from which a workflow is composed per ticket. Which brings us to the two
facts that shape everything else.

### The trigger column has exactly two values

Look down it. Either **a person types a command**, or **a probe fires**. There is no
third kind of arrow in the system.

That is not a stylistic observation. `watchme` *creates* a probe; `test` *is fired
by* one. Probes appear at both ends of the catalog, doing the same job in opposite
directions — which means a probe is not a special artifact belonging to one step. It
is the general mechanism by which one step reaches the next.

### So a workflow is a set of edges, composed per ticket

A workflow is composed at ticketing time, by the ticketer, according to the needs of
the ticket. Put beside the fact above, that means: **the ticketer does not stamp a
state machine onto a ticket. It stamps a set of probes** — each one watching for a
state and firing the next step.

This is why workflow *versions* are meaningless at the class level. There is no
class-level machine to version. There are only instance-level edges, and a probe is
an edge: it attaches itself to a sender and a receiver, is held by its two endpoints,
and is enumerable by walking from either one. Nothing holds a global list of probes,
and nothing needs to.

---

## 2. How a step is defined

Every step in the catalog answers the same eight questions. **A step is a process.**
An artifact is not a step — an artifact is how a step *completes*.

| field | what it answers |
|---|---|
| **name** | what we call it |
| **trigger** | the event that fires it — a command, or a probe |
| **consumes** | what it takes in |
| **emits** | what it produces |
| **completes** | the predicate that makes it done |
| **gate** | the door that stands at its end |
| **owner** | the single component that gates writes (Law 6) |
| **exits** | every way out, including the kills and the branches |

For every step but one, *emits* and *completes* are the same question. The exception
is `learn`, and the exception is a fact about learning rather than a hole in the
rule — see §4.

---

## 3. The steps

### capture — an idea is written down
- **trigger:** Akien has an idea and says so. The only step whose input is outside
  the system; nothing upstream can fire it.
- **consumes:** nothing in-system · **emits:** an idea record, in prose
- **completes:** one and done — *"its end state is just when you and I move on to
  the next thing."* The only completion predicate in the catalog with no artifact
  and no observer: it is true by abandonment.
- **gate:** captured text that can be interpreted later. This is a real gate, not an
  empty one — the predicate is *non-empty prose at a known address*. What is
  deferred is **interpretation**, not admission, and deferring interpretation is the
  entire point of the step.

### intend — an idea becomes a traced intention
- **trigger:** reaching for an idea *is* the event. Ideas sit in a queue; the door is
  the filter. · **consumes:** an idea record
- **emits:** one berth per firing — a node in intention fill-state, traced and
  challenged. One idea may yield many intentions, but by many firings, not by one
  firing emitting many: the door's fields are singular per node, so a fan-out from a
  single firing would have to collapse five answers into one.
- **completes:** the berth path is printed by the door.
- **gate:** `skill:intent` — **built**. Requires 8 fields, compiled live from
  `skills/intent/intention+why.json`. A refusal names *every* lack in one pass and
  is itself recorded.
- **exits:** routed forward · **routed out** — the kill, which is forced to carry
  bullets and an adversarial pass. A node killed here with no record of why teaches
  nobody.

### design — an intention is worked until it can be cast
- **trigger:** `/design [intention]`. A berth exists and is not yet cast, which is a
  predicate on a berth — something a shim can fire on, not something to remember.
- **consumes:** a berth · **emits:** cast tickets, typed, with gates bound
- **completes:** the cast packet passes `/sorted`.
- **gate:** `skill:sorted` — **built**. 12 fields, the largest contract in the
  system, including the completeness question answered *in substance*: a one-word
  pass is the hollow check the door exists to stop.
- **note:** the only step with a different skill at each end. `/design` opens the
  joint work; `/sorted` closes it.

### chart — a cast ticket becomes a build packet
- **trigger:** `/chart`. Downstream refuses without a chart chain, so the refusal is
  the trigger. · **consumes:** a cast ticket
- **emits:** a build packet — seven nexus stages, per-field provenance
- **completes:** all seven stages pass their schema gates.
- **gate:** seven doors, which refuse complete-in-one-pass and accumulate before
  they raise.

### build — code is proposed
- **trigger:** `/sail`, on a completed chart chain · **consumes:** a build packet
- **emits:** *proposed* code · **completes:** code exists — **not** that it is right.
- **owner:** the component being built, in its own directory.
- **note:** "proposed" is load-bearing. This step's completion predicate is
  deliberately weak, because the next step is what makes it true. Law 9 lives in
  that word.

### test — the proposal is sealed
- **trigger:** a probe watching for `VALIDATEME` · **consumes:** proposed code
- **emits:** a VALIDATION — the ratified eight fields
- **completes:** the seal is written through the validation door.
- **owner:** the tester.
- **exits:** a green seal · **a red seal — which is a completion of the step, not a
  failure of it.**

### watchme — feedback is arranged for
- **trigger:** validation complete · **consumes:** the validation and the
  intention's falsifier
- **emits:** a probe, addressed to wherever feedback has to come from — a gateway, a
  time, a future event
- **completes:** **the probe is created.** The state does not wait for what the
  probe finds. Creating the probe *is* the work of this step.

### learn — feedback lands, and is judged
- **trigger:** feedback arrives from a probe · **consumes:** the feedback
- **emits:** nothing further — **terminal**
- **judge:** *the creating intention, or a similar component.* That is the probe's
  **other end** — the sender side of the edge the probe already is. The judge was
  never a missing component; it is whatever the probe is attached to at the far
  side, and the component that owns it is the owner (Law 6).
- **completes:** once feedback is **headed in the right direction.**

---

## 4. Why `learn` is the one exception

Every other completion predicate can be satisfied by an artifact: a file exists, a
packet passed, a seal was written. *"Headed in the right direction"* cannot. It is
neither "the feedback arrived" nor "the thing is correct" — it is a **derivative**, a
trend across arrivals rather than a value at one.

Only something that persists across arrivals can see a slope. A single artifact
cannot satisfy this predicate no matter how good it is, which is why `learn` is the
one step where *emits* and *completes* come apart.

Where that series of arrivals lives is the open question of this document.

---

## 5. How a gate opens

A gate is not a place where a door checks its own rules. **A gate opens because an
inspector submitted a finding for it.** The door owns *admission*; the inspector owns
*judgement*; neither may do the other's job. That is Law 6 drawn one level finer than
usual, and it is what makes every gate in this catalog the same piece of code — *is
there a live passing finding bound to me?* — with all the difference between them
living in data.

### The inspector

The metaphor is an **electrical code inspector**, and it is meant literally:

1. **An inspector cites a code they did not write.** Not "this looks unsafe" —
   "this violates 210.8(A)(7)." Their authority comes from the code. An inspector
   who invents a rule is out of line. This is the load-bearing one: it is the whole
   difference between *a model thinks this is smelly* and *this violates the
   charter-beside-code rule*.
2. **Red-tag is block, not fix.** Work stops until corrected. The inspector never
   touches the work, and therefore never needs a write.
3. **Findings are dated observations** — what I saw, on this date, against this
   code. Closable, and **expiring**.
4. **Re-inspection is owner-initiated.** The owner corrects and calls the inspector
   back. The inspector does not lurk.
5. **Right of entry, not ownership.** Broad read scope; the only write is to its own
   findings.

Where the metaphor strains: a real inspector is third-party by law, and that
independence is what makes them trustworthy. Ours run inside the system they
inspect. The externality has to come from somewhere, and it comes from (1) — the
*rule* is external to the inspector even when the inspector is not external to the
system.

### Deterministic, filter-stack based

An inspector is built from a **filter stack**. A filter is selection, not compliance:
it narrows candidates — which rules apply to this artifact, at this gate, right now.
Filters emit nothing durable and must stay cheap; a stack of dozens is normal.

New filters arrive by accretion: *we find a new thing, we add a new filter.*

### A stack resolves; a filter never has an opinion

A filter is never asked whether it knows. It narrows, or it doesn't. What carries a
verdict is **the stack**, and a stack always returns a **typed outcome** — never a
bare nothing.

That distinction is the load-bearing one, and it is borrowed rather than invented:
the same shape is worked out in an inference router, where a request is narrowed by
four stacks in sequence and the resolver returns a decision whose `kind` is the
single thing any caller may switch on. Three properties come with it:

- **Every dimension has a sole home.** Reachability lives on one stack, capability on
  another, cost on a third; the engine holds no rule literals at all. For an
  inspector, that means each class of rule has one address, and the base class knows
  none of them.
- **The no-result kinds are distinguished, and collapsing them is the bug.** In the
  router, "nothing capable exists" and "something capable exists but nothing is
  serving it" once both came back as nothing, so the caller had to guess — it
  re-read a ceiling as an outage, retried a doomed path, and halted with a message
  that was false. An inspector has the same three: *no rule applies*, *rules
  conflict*, *evidence insufficient*. They are not one outcome, and the moment they
  collapse, the gate starts guessing.
- **A person is a typed outcome, not a failure.** The router's ladder resolves at the
  top to a human terminal — strictly above every model rung, returned as its own
  kind rather than as an absence. An inspector's genuinely undecidable case resolves
  the same way: to a person, named as such.

And the resolver **raises no alarm of its own**. A no-path is silent data that flows
up to the single owner, which alarms once at its terminal. Three components each
alarming about the same failure is a bug with three mouths (Law 7 at a diagnostic
surface, Law 6 about whose failure it is).

*Pattern borrowed and cited, not code grafted — the source system is a failed path,
and bytes crossing into proven-space would need a ticket and a proof of their own.*

### Scripted plus inference — where the answer comes from

An inspector may call inference. It may not get its **answer** from inference.

- **The answer comes from the script.** The verdict is deterministic, always.
- **The LLM call adjudicates or summarizes ambiguity, if any exists** — and only
  then. No ambiguity, no call, no cost.
- The output of that call resolves an ambiguity or renders it readable. It never
  *becomes* the verdict.

This keeps the three strata intact: the **code floor** decides, the ceiling
clarifies. A gate that opened because a model was persuaded is policy wearing the
costume of physics (Law 4).

The provenance mechanism for this already exists and is enforced. Every bullet on a
finding carries a **stratum** — `code`, `tree`, or `hex` — and a `hex` bullet
*cannot be claimed by hand*: it exists only via the injected inference seam, because
a hand-authored `hex` would be invented provenance. So the rule "the verdict is
`code`, and `hex` may only ride along" is already a type, not a convention.

### The inspector learns from the upstream

An inspector never learns from its own findings — that would be an inspector writing
its own code, and rule (1) would be dead within a week. It learns **upstream**, and
in two ways:

- **At inspection time**, it can walk up the chain — build packet to ticket to
  intention to charter — to reach the **why**. This is what makes adjudication
  possible rather than guessing: an inference call asked to resolve an ambiguity
  with no access to the intention behind the rule is just a model with an opinion.
- **Over time**, new rules come *down* from upstream, where they are authored. The
  inspector acquires rules; it never mints them.

That also answers the question every Cairn charter must answer — *how does this
component learn?* — for the whole inspector class, in one line: **from the upstream,
never from itself.**

### One base class

Every inspector in the system shares a common base class, and everything above
lives in it: the filter stack, the finding shape, the three-valued verdict, the
ambiguity escalation, and the upstream walk. An individual inspector supplies only
its **rules** — which are data — and inherits the machinery.

This is shared *implementation*, and shared implementation is not shared
*ownership*. The base class supplies the default assembly; each inspector runs it
against its own rules, at its own gate, and owns its own findings alone. There is no
central thing holding inspectors, and none is needed: an inspector is bound to a
gate, and the gate asks only *is there a live passing finding bound to me?* Nothing
in the system ever needs to enumerate every inspector at once.

What the base class must make impossible, not merely discourage:

- **Minting a rule.** Rules arrive from upstream. An inspector that can author its
  own citation has repealed rule (1).
- **Acting.** The only write is to its own findings.
- **Reaching inference directly.** The inference seam is injected, exactly as the
  `hex` provenance seam already is — so a hand-authored `hex` bullet remains
  impossible by construction rather than by review.
- **A verdict that isn't `code`.** The script decides; the ceiling clarifies.

### What an inspector is not

Two neighbouring primitives exist, and the three are separated by **authority**,
which is the only axis Law 6 cares about:

- A **filter** decides nothing outside its own call.
- An **inspector** may *stop* work, but may never *change* it.
- A **janitor** may change things, but only inside a space nobody else owns. It
  processes findings, resolves the ones in its own commons, checks them off, and
  raises everything else to the owner.

Collapsing any two of them re-creates a supervisor — the thing Cairn has no room
for, because enforcement here *is* gated ownership, and there is no enforcer.

---

## 6. What is built, and what is red — measured 2026-08-04

Red is the default here; green is earned. What follows is the state of the doors,
measured rather than asserted, on the date given.

**Built:**

- Findings already fire at doors, at both exits. A berth carries its `finding_id`;
  a refusal is a datum, not a lost moment.
- A deterministic filter-stack inspector exists — `cairn/build_inspector` — with
  founding filters for *code with no charter*, *code with no proofs*, and *a device
  that never speaks*.
- **Its findings already cite their rule.** Each carries `filter`, `component`,
  `finding`, `evidence`, and `why_it_matters`. Rule (1) is satisfied in the one
  place an inspector actually runs.
- The externality is already physics at two doors: `intend`'s and `design`'s
  contracts compile live from the *charter*, not from the door's code. The door
  cites a rule it did not write.

**Red:**

- **The finding that cites is not the finding that fires.** Two shapes exist. The
  inspector's finding carries a citation but is wired to no gate. The door's
  finding fires at every gate but carries only text and a stratum — no citation
  field. Neither is the whole thing.
- **No stack has a typed outcome.** Today a filter returns findings-or-empty, and
  empty means pass — so *nothing applied*, *the rules disagreed* and *there was not
  enough evidence* are all indistinguishable from *this is fine*. That is the same
  collapse the inference router had to undo, and it is what leaves
  scripted-plus-inference with no trigger: there is no outcome kind for the
  inference call to fire on. The fix is not a third value on a filter — a filter is
  never asked. It is a resolved outcome on the stack.
- **There is no base class, and the two existing inspectors have already
  diverged — including on what "filter" means.** `build_inspector` keeps a
  module-level dict of filters and a module-level `inspect()`; its filters are
  `(row, dir) -> list[findings]`, which makes them *judges*, not filters.
  `diagnostic_inspector` is already a class, and its filters are
  `(record) -> bool` — genuine selection, which is what the word is supposed to
  mean. One word, two primitives, and the one that took the wrong meaning is the
  one that gates builds. A common base class cannot be written over both, which is
  why the base class is not tidying-up: it is what forces the vocabulary to become
  physics.
- **The only built inspector cannot move.** `build_inspector` rests in a dissolved
  state with no door out. The gate model for the whole workflow depends on the one
  inspector that exists, and it is stuck.
- **The fan-out has no edge.** None of `intend`'s 8 fields records which idea the
  intention came from; the trace points *up* to a Law, never *back*. The moment one
  idea becomes three intentions, the three cannot say they are siblings, and none
  can point at the prose that bore them.
- **Two named doors do not exist.** No `/idea`, no `/design`, and no ideas queue for
  `capture` to write to. Every *built* door is in the middle of the workflow; both
  missing ones are at the ends — which is exactly where a person and the system work
  together.
- **`chart`'s gate is unreadable from here.** Its seven doors are schemas in code
  and its charter declares no contract, so the most-gated step in the workflow is
  the one this document can see least of.
- **`build`'s gate is not declared at all** — its real requirements live only in
  code and prose. And the one inspector we have is the *post-build* inspector, which
  means the single inspector and the single undeclared gate it belongs to have never
  been connected.
- **No probe has ever fired anything.** The runtime spine has not run. Everything in
  §1 about probes is design, not observation.

Count: eight gates, two with contracts compiled from a charter; two inspectors, no
base class between them, and zero of them bound to a gate.

---

## 7. How this document changes

In place, and first. This is not a signed stone that learns by supersession like the
other pieces in this folder — it is a **living definition**, and drift between it and
the workflow is the defect it exists to prevent. A change to the workflow is a change
to this file; everything downstream follows from it.

What it must never do is quietly go green. Every claim in §6 carries a date and was
measured, and a claim that cannot be measured says so.

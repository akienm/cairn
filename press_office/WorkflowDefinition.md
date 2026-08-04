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
| **capture** | `/idea [prose]` | — (we move on) | 3 fields, compiled live |
| **intend** | `/intent [idea]` | fire intent | 9 fields, compiled live |
| **design** | `/design [intention]` | `/sorted` | 5 fields at the opening, 12 at the close — both compiled live |
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

### A probe is never deployed alone

A probe is always part of a triple, and all three roles are named when it is created:

- **the probed** — what is watched. One endpoint.
- **the probe** — the edge itself: who to call, what to tell them, when, and whether
  it persists.
- **the responder** (or learner) — where the feedback lands and something happens.
  The other endpoint.

Never two of the three. **A probe with no responder is not a probe** — it is a
watcher reporting into nowhere, which is precisely the silent-failure shape this
system exists to prevent. Naming the responder is part of creating the probe, not a
lookup performed later when feedback shows up.

And the responder does not have to be a machine. **In the debugging case the
responder is CC** — a person or an agent is a legitimate, named responder, the same
way a router's ladder resolves at the top to a human terminal rather than to an
absence. That matters for sequencing: probes are useful before any automated learner
exists, because a named human responder is a complete triple.

Two consequences worth stating plainly:

- **`learn` has an address by construction.** Its judge is the probe's other end, and
  that end was named at creation. Nothing has to be resolved when feedback arrives.
- **`watchme`'s completion predicate gets teeth.** "The probe is created" means *all
  three roles are bound* — which is checkable, where "a probe object exists" was not.
  A probe missing an endpoint should never come into being, so there are no dangling
  ends to sweep up afterward.

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
- **gate:** `skill:idea` — **built 2026-08-04**. Captured text that can be interpreted
  later: a real gate, not an empty one — the predicate is *non-empty prose at a known
  address*. 3 fields, compiled live from `skills/idea/intention+why.json`, the
  smallest contract in the system on purpose. What is deferred is **interpretation**,
  not admission, and deferring interpretation is the entire point of the step.
- **the known address:** `CairnCommons/ideas/` — knowledge, so it is git, not
  instance-space. The berth the firing leaves is the receipt; the commons record is
  the work, and an unwritable commons is a loss rather than a hiccup.
- **note:** the door asks nothing beyond the three fields, and the prose is stored
  byte-identical. Capture is the one moment in the workflow where translation loss is
  zero; a door that tidied, summarised or interrogated would spend it.

### intend — an idea becomes a traced intention
- **trigger:** reaching for an idea *is* the event. Ideas sit in a queue; the door is
  the filter. · **consumes:** an idea record
- **emits:** one berth per firing — a node in intention fill-state, traced and
  challenged. One idea may yield many intentions, but by many firings, not by one
  firing emitting many: the door's fields are singular per node, so a fan-out from a
  single firing would have to collapse five answers into one. **Each firing names the
  idea it came from** (`from_idea`), so the three say they are siblings by pointing at
  one record rather than by anyone remembering.
- **completes:** the berth path is printed by the door.
- **gate:** `skill:intent` — **built**. Requires 9 fields, compiled live from
  `skills/intent/intention+why.json`. A refusal names *every* lack in one pass and
  is itself recorded. Two of the nine are judged rather than merely present
  (`skills/intent/door.py`, 2026-08-04): `from_idea` must **resolve** to a record
  under `CairnCommons/ideas/` or carry a reason with a referent something can open,
  and `challenge` must carry **all five** answers — the charter had declared that
  floor in prose while a one-key object satisfied the door.
- **exits:** routed forward · **routed out** — the kill, which is forced to carry
  bullets and an adversarial pass. A node killed here with no record of why teaches
  nobody.

### design — an intention is worked until it can be cast
- **trigger:** `/design [intention]`. A berth exists and is not yet cast, which is a
  predicate on a berth — something a shim can fire on, not something to remember.
- **consumes:** a berth · **emits:** cast tickets, typed, with gates bound
- **completes:** the cast packet passes `/sorted`.
- **gate, at the opening:** `skill:design` — **built 2026-08-04**. 5 fields, compiled
  live from `skills/design/intention+why.json`. The berth must resolve, must have come
  from `/intent`, and must not have exited `routed_out` — designing on a node the
  cheapest gate in the system already killed is the waste Law 1 names, and a corpse
  reads as a perfectly well-formed berth to anything that only checks presence.
- **gate, at the close:** `skill:sorted` — **built**. 12 fields, the largest contract
  in the system, including the completeness question answered *in substance*: a
  one-word pass is the hollow check the door exists to stop.
- **note:** the only step with a different skill at each end. `/design` opens the
  joint work; `/sorted` closes it. The opening door records **no exit** — every exit
  of this step is `/sorted`'s to record, and two components recording one outcome is
  how they come to disagree about it.
- **the back edge is countable.** `/design`'s `entering_from` is either `intent` or
  `sorted:<berth>`, so a second pass is distinguishable from a first. That count is
  the only signal there is about which of `/intent`'s questions are letting things
  through — prose in the field would erase it.

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

### Two kinds of stack

A filter is a **pass/fail rule over one candidate**. It emits nothing durable, holds
no opinion about consequences, and cannot rank — a selector needs the whole surviving
set to compare, and a filter only ever sees one thing. Alone it is nearly useless.
Filters are used in stacks.

There are two ways to stack them, and they are the same primitive applied along
opposite axes:

|  | **selecting stack** | **reporting stack** |
|---|---|---|
| what varies | the **candidates** — one rule set, run over many | the **rules** — one subject, many questions |
| output | **one** answer, the best possible | **a list**: rule name → pass/fail |
| what it keeps | the survivors; failures drop out silently | the **results**; the failures are the point |
| durability | nothing — dozens per call is normal, must stay cheap | a **finding**, which is a record |
| example | routing a request to a model | *here are the build rules and how each measured* |

The transpose is the whole distinction. A selecting stack holds the questions still
and moves candidates past them. A reporting stack holds the subject still and moves
questions past it.

An **inspector is a reporting stack.** A code-smell inspector hands back a list of
named rules with their verdicts and its evidence, and that is where its job ends.
**Someone else is responsible for what happens to that information** — that is not a
gap in the design, it is the cooperative system working. The inspector may stop work
but never change it; a janitor may change things, but only inside a commons nobody
else owns; a gate may admit or refuse. None of them is the inspector, and the
inspector is none of them.

Which is why a reporting stack's output must carry evidence and the *why it matters*
alongside the verdict: its reader is a different component, deciding without the
ability to re-derive.

**The typed outcome lives at different levels in the two.** A selecting stack can
fail to resolve at all, so the outcome belongs to the *stack* — *no candidate is
capable*, *a capable one exists but nothing is serving it*, *this resolves to a
person*. A reporting stack always returns one result per rule, so it has no stack-level
no-result; its outcomes are **per rule**: pass, fail, or *this rule could not be
evaluated here*. And rules in a reporting stack cannot conflict — they are
independent observations of one subject. Conflict is a selecting-stack problem.

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
- The externality is already physics at four doors: `capture`'s, `intend`'s and
  `design`'s two contracts compile live from the *charter*, not from the door's code.
  The door cites a rule it did not write.
- **Both end doors now exist** — `/idea` and `/design`, built 2026-08-04, with an
  ideas store at `CairnCommons/ideas/` for `capture` to write to. Proofs beside each
  (26 and 30 teeth), run twice.
- **The fan-out has an edge.** `intend`'s `from_idea` must resolve to a real record
  or carry a reason with an openable referent, so a claim of common origin is
  checkable rather than remembered.
- **The challenge floor is physics.** All five adversarial answers are required at
  the door, at both exits. It was declared in the charter and enforced by nothing;
  a partial pass is the pass not having run.
- **Skill usage is countable** — `bin/cmd/skilldial`, built 2026-08-04 on the trace
  the doors already write. Firings, refusals, findings, match rate, last fired, per
  skill, re-derived on every read. No registry: the roster *is* the `skills/`
  directory, so nothing can enrol and nothing can fall out of sync.

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
- **There is no base class, and the two existing inspectors have diverged.**
  `build_inspector` keeps a module-level dict of rules and a module-level
  `inspect()`; `diagnostic_inspector` is already a class with `(record) -> bool`
  predicates. Their filters look incompatible — but they are the two *subtypes*
  above, not two different primitives: `build_inspector` is a reporting stack and
  `diagnostic_inspector` uses a selecting stack to narrow a log. The real defect is
  narrower and shared: **neither carries a typed per-rule result.**
  `build_inspector` encodes pass as an empty list, so *this rule could not be
  evaluated* is indistinguishable from *this rule passed*.
- **The only built inspector cannot move.** `build_inspector` rests in a dissolved
  state with no door out. The gate model for the whole workflow depends on the one
  inspector that exists, and it is stuck.
- **Most of the doors cannot be counted at all.** Measured 2026-08-04: 11 skills on
  disk, **5 countable** (`design`, `idea`, `intent`, `saveslate`, `sorted`) and **6
  not** (`challenge`, `chart`, `commit`, `moreabout`, `note`, `sail`). A skill that
  declares no `input_contract` fires no door, so it leaves no trace, so its usage is
  not zero — it is **no measurement**, and `skilldial` prints it that way rather than
  as a 0. This is the live limit on the disuse clause: `/note` is one of the six, so
  *"could wind up being excised through disuse"* is a rule that cannot yet be
  evaluated on the skill it was said about.
- **Neither new door has ever been fired in anger.** `design` and `idea` count 0 —
  which is a real zero, not an absence, and it is what it says: built, proven,
  unused. Law 9 applies to them exactly as written.
- **And neither has a voyage behind it.** They were built out-of-band, on a direct
  instruction, so no ticket bore them and there is nothing to compile: `skills/idea/`
  and `skills/design/` carry a charter, code, proofs and a seal, but no `state` and no
  `history`. That is the honest condition and it is not repaired by writing one —
  state compiles from tickets and is never hand-edited. Two doors that gate the
  workflow have not been through it.
- **`chart`'s gate is unreadable from here.** Its seven doors are schemas in code
  and its charter declares no contract, so the most-gated step in the workflow is
  the one this document can see least of.
- **`build`'s gate is not declared at all** — its real requirements live only in
  code and prose. And the one inspector we have is the *post-build* inspector, which
  means the single inspector and the single undeclared gate it belongs to have never
  been connected.
- **No probe has ever fired anything.** The runtime spine has not run. Everything in
  §1 about probes is design, not observation.

Count: eight gates, **four** with contracts compiled from a charter; two inspectors,
no base class between them, and zero of them bound to a gate.

### Measuring the doors — ruled 2026-08-04

*"we have to be measuring each skills usage as we go. not just efficacy, but how many
times. metrics."*

Two numbers, not one. **Efficacy** was already there — the trace records a verdict
against every finding, so a door's match rate is derivable. **Count** was not, and
count is what the disuse clause runs on: a door is excised because nobody uses it,
which is a claim about frequency.

`bin/cmd/skilldial` reports both, and its own falsifier is the distinction it must
never collapse: **unmeasured is not zero.** A door nobody wired and a door nobody uses
look identical in an uncounted system, and excising the second by mistake removes a
door that was never tried. So the roster prints `—` and *not countable* where it has
no measurement, and reserves `0` for a real one. That is Law 7 at a diagnostic
surface: the surface may not collapse the error into a coherent shape.

The number that follows from it: **six of eleven skills are currently invisible**, and
the only fix is the one the seam was built for — a skill becomes countable by
declaring `input_contract` in its charter, which is a charter edit, not a code edit.

### The refit

Existing filters were written before this definition existed, and they have to be
refitted to it. Reusing and simplifying what is already here beats building beside
it — an answered question should become structure, not a second structure.

Measured 2026-08-04, the surface is smaller than "everywhere":

| site | what it is today | what it becomes |
|---|---|---|
| `build_inspector` | 8 rules in a module-level dict; pass encoded as an empty list | a reporting stack with a typed per-rule result |
| `diagnostic_inspector` | a class with `(record) -> bool` predicates and a rule registry | a selecting stack, already close |
| `chart` — seven doors | schema gates per stage, described as "pre-installed judges"; declares no contract | the largest site, and the least filter-shaped today |
| `librarian` — the walk | over-fetches to hold a region at *k* after narrowing | a small selecting stack |

Everything else that says "filter" says it in a comment or a ticket name. Three real
sites and one small one — and the largest, `chart`, is also the one whose gates this
document currently cannot read.

---

## 7. How this document changes

In place, and first. This is not a signed stone that learns by supersession like the
other pieces in this folder — it is a **living definition**, and drift between it and
the workflow is the defect it exists to prevent. A change to the workflow is a change
to this file; everything downstream follows from it.

What it must never do is quietly go green. Every claim in §6 carries a date and was
measured, and a claim that cannot be measured says so.

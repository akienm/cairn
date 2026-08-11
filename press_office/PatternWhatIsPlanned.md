# Pattern — What is planned, and why it is not built yet

### The whole system is a learning block whose inspector and whose memory are still a human brain

> **The move.** Publish the roadmap the same way you publish the code: as claims with falsifiers,
> marked red until built, running, and inspected. A plan is an *artifact*, and an artifact that
> has never been measured is a hypothesis. This document is the least reliable one in the series
> **by construction**, and saying so is the point.

---

## 1. The measured failure

**A plan that was documented, believed, built against, and wrong.**

Over 2026-08-01 and 2026-08-02 a design settled for a "learning block" — the reusable unit the
whole system was to be made of. It was written up. A component was built under it. It appeared in
a technical brief. Everything conformed.

On 2026-08-05 the author read that section and said, verbatim:

> *"i have no idea where that came from, but that's garbage"* … *"you've conflated inspectors and
> learning blocks"* … *"an inspector is a kind of learning block, a subclass."*

The error: the **inspector's** parts — a finding, a human verdict, a delegation dial — had been
promoted into the **parent**. A line about the inspector learning as it goes had been read as an
identity claim instead of a statement about a subtype. Every block was then required to have
organs only an inspector needs.

Here is the part worth the whole story. **The safeguard was in place and it worked.** The
original note carried a literal key reading *"below here is CC's read, not Akien's words,"* and
the wrong anatomy sat below that line — correctly labelled, for four days.

> **The discipline worked and nobody read the label.**

What it cost: nothing in code — the engine conformed anyway and the organs are real machinery
that still does its job. **Everything in what may be claimed.** And one campaign that would have
migrated nine skills onto the wrong model was stopped before it ran, on the rule *do not migrate
onto a model just found wrong.*

That is the failure this document exists under: **the plan is the artifact most likely to be
wrong, and the least likely to be measured.**

---

## 2. The pattern

### 2.1 The system, viewed at the top, is one learning block

A learning block's inner loop is small and data-driven: **input → a candidates loop → an
evaluation loop → decide or escalate → output**, instantiated from a spec that carries all the
block's difference. The engine is branchless about blocks, and *a block-specific branch in engine
code falsifies the design.*

The candidates loop **generates**; the evaluation loop **kills against the constraining
questions** and leaves survivors. Two distinct loops, and the distinction is load-bearing.

An **inspector is a subclass** of that, adding a finding, a human verdict on it, and a dial that
measures agreement. A block that is not an inspector emits no finding.

The author's own framing of the whole system, verbatim, 2026-08-01:

> *"the whole system is a learning block. the problem with it at the moment is my poor ADD brain
> is the inspector and the memory."*

So the roadmap has a single direction, and it is not "add learning to things":

> **Move the inspector and the memory out of his head and into the system's own organs.**

Findings emitted by per-step inspectors rather than noticed by a human. A dial *read* rather than
remembered. Delegation happening by his explicit act, when the measured agreement rate earns it —
**nothing is delegated on day one, by design.**

### 2.2 The corpus is the resolver for design details — not the author

Between a six-line charter and every component's trace field sits a corpus of the questions the
system is trying to answer. Until it was written down, every trace pointed at the six-line
charter as a proxy, because it was the only thing on disk that could receive one.

The rule it ships with:

> **When a design detail is open, the question is "how does this need to be for the corpus?",
> never "which does the author want?"**

He gets bounds changes, sequencing, and rulings that change the spec. Everything else derives.
Two details had been wrongly escalated to him and were resolved from the corpus instead — one by
noticing the corpus wants *stackable bricks*, so a brick whose output is not stably comparable is
not a brick yet; one by noticing that tickets carry an antiproof, so an absence you cannot re-run
is a note rather than a measurement.

**Escalating a resolvable detail to the one human bottleneck is itself the defect** this rule
removes.

### 2.3 The standing rule for everything not yet built

> *"everything we build from here on out should be that shape or have a good reason not to."*

Half-built. The named-exemption mechanism exists as physics — a `"none, because <why>"` passes
while a blank refuses **as an exemption** rather than as a bad path — but the charter schema does
not yet demand the answer, so it remains a prose debt with a ticket.

---

## 3. What is planned, in dependency order

Each of these is **red**: designed, not built, not measured.

### 3.1 The runtime spine actually running

The heartbeat runs, the bus exists, the components exist — **and no real fleet has ever beaten.**
This is a live trouble in the system's own inbox, and it gates most of what follows, because
every forward-pointing edge in the workflow is unfired for exactly this reason.

The ruled sequence is *everything below is working fine, measured per rung*: heartbeat →
chassis → the assistant's own shim → the author's shim → the web server → the librarian's shim →
the conversation. Two of those shims do not exist.

### 3.2 The storage migration

Splitting node from embedding from leaf, per-tree leaf tables, bounded neighbour lists, calving
along dominant attractors, and the shear. Designed in detail, prerequisite for scale, **and the
running store is still one table where all three layers are one row.**

The falsifier is stated and unmet: it must be measured at the scale where the previous build
died — on the order of 2.5 million nodes — and it must hold *two-sided*, with access not
degrading as the graph grows **and** write cost not growing with the corpus. The largest live
measurement today is 88 nodes. See [`PatternTreeArchitecture.md`](PatternTreeArchitecture.md).

### 3.3 Semantic canonicalisation, and active invalidation

The inference cache learns *whether* it pays — 40.0% hits, 34.3% of tokens avoided. It does not
learn **which questions are the same**, and it does not learn **when a stored answer has gone
wrong** even though every answer carries a falsifier for exactly that purpose.

Both are deliberately unbuilt: collapsing two questions that are not the same is worse than
missing the cache, and no shape has been committed without an adversarial pass. See
[`PatternInferenceProxy.md`](PatternInferenceProxy.md).

### 3.4 The probe corpus

Questions the system *asks* — reusable, fired at nexuses, each carrying a measured yield —
against questions the system *has*. The first lane holds **zero records**. The consequence is
concrete: **a probe living inside a skill file is asked but never measured**, so no probe has ever
earned tenure and none has ever been retired for uselessness. The promotion machinery has no
substrate.

### 3.5 Green derived rather than asserted

The system's ninth law says red is the default and green is earned — built, running, *and*
inspected. **Nothing derives that.** Red is a word a reader has to remember to apply, and a
component whose code has stopped matching its charter reads as whatever it last said about
itself. There is no site plan showing which lots are still unexcavated.

This is the most important unbuilt thing in the list, because until it exists **every other
red in this series is maintained by hand.**

### 3.6 The desk

A workspace holding an assignment's topic, what has been folded in so far, open threads, and a
resume event — what a multi-day research face needs in order to be a research face rather than a
sequence of unrelated conversations. Filed, named, unbuilt until that face pulls it.

### 3.7 Stackable bricks that do part of the build without the large model

The pre-build preamble already runs as seven schema-gated bricks with a deterministic floor
beneath each — measured at roughly an 89% cut in build tokens before caching. The plan is to keep
going: enough bricks to perform *some of the build itself* outside the expensive model.

The hypothesis behind it, stated as a hypothesis: **that the inside of a coding agent — models
and agentic loop together — can be decomposed into stackable learning blocks.**

### 3.8 The parallel inspectable clone

The distant endpoint, and it is the one that makes the rest a research programme rather than a
tidy-up.

After the librarian, a complete parallel agent **shadow-learns every call and response** on a
dedicated inference machine. The measure is stated in advance and it is unusually sharp:
**green-rate parity on the same work.** Not "seems comparable" — the same tasks, the same gates,
the same pass rate. On imitation failure, the response is to **decompose into learning blocks and
retry**, which is the same move as §3.7 arriving from the other direction.

### 3.9 The interview-driven builder

A builder that interviews a person and then builds what they asked for. Everything above is
scaffolding for this, and it is the aim against which *"does it survive a second person?"* becomes
the real test.

---

## 4. What it costs to publish a roadmap this way

**It reads as failure.** A document whose honest summary is "most of this is not built" is worse
marketing than one that describes the design in the present tense. That trade is taken
deliberately, and the alternative is the thing this whole system is a reaction to.

**Red is currently maintained by hand.** Every claim in this series about what is unbuilt was
written by reading charters and running instruments on one day. Until §3.5 exists, this document
begins going stale the moment it is published, and nothing announces it.

**Sequencing is a human's call and a bottleneck.** The corpus resolves design details; it does
not resolve *what to do next*. That stays with one person, and the queue at his gate — 12 tickets
and 68 findings — is a measured property of the design rather than a backlog that will drain.

---

## 5. What would falsify this

- **The plan gets built without being re-derived.** If the storage migration, the probe corpus, or
  the parallel clone lands *exactly* as described here, that is mildly suspicious — every previous
  design in this system changed on contact with measurement, and the ones that did not change were
  usually the ones nobody measured.
- **A section here stops matching the charters.** These are compiled from component charters and
  from the corpus by hand. The moment they disagree, this document is the wrong one.
- **The inspector stays in his head.** If, a quarter from now, findings are still noticed by a
  human rather than emitted by per-step inspectors, then the campaign direction in §2.1 is a
  statement of preference rather than a plan.
- **Delegation never happens.** Nothing is delegated until a measured agreement rate earns it. If
  no dial ever crosses a threshold, either the inspectors do not work or the threshold is not real.
- **The parallel clone reaches parity by being given the answers.** Shadow-learning that is
  actually supervision on the same task set would produce parity that means nothing. The measure
  has to be *the same work, independently*.
- **The whole method fails if it does not survive a second person.** Every pattern in this series
  was built by one human and one model on one machine. That is the standing falsifier over all of
  it.

---

## 6. What is built, and what is red

**Built.** The learning-block engine, branchless about blocks and instantiated from data-only
specs, with every run writing its full state log — input, candidates, the constraint that killed
each loser, why the winner won, what escalated and where. The shared gate machinery: declarable
input contracts, consumer-typed traces, findings with tagged provenance, verdicts captured with
the author's words verbatim, and a dial that is a pure projection computing agreement on read and
storing nothing. A command-line door so the gate's owner fires the gate **from his own shell** —
which exists because the very first live verdict revealed he had no way to record one without
going through the model, the exact indirection a verbatim rule exists to prevent.

**Red — everything in §3**, plus:

- **No skill declares a contract yet.** The door has machinery and no tenants.
- **The delegation path is deliberately unbuilt.** It lands when the first dial crosses a
  threshold the author sets.
- **The engine decides but does not actuate.** In its first live runs the decision and the act
  agreed — and that agreement was *observed, not wired*. Wiring a decision into a block's own door
  arrives per block, by its own ticket, never ambiently.
- **The corpus has no state per question.** Exactly one is marked — *"a tool for me to learn
  (succeeded already)"*. The rest are left unstated rather than guessed, and nothing yet points
  the system's intentions at the corpus instead of at the six-line charter above it.

---

*Pattern document, `press_office/PatternWhatIsPlanned.md`. The last in the Cairn pattern series;
the spine is [`CairnArchitecture.md`](CairnArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11. **This document ages faster than the others**
— check it against the component charters before citing it.*

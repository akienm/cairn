# Pattern — The workflow and its artifacts

### The backward edge is the one that works

> **The move.** Work moves through named steps. Every step emits a durable, schema-gated
> artifact at an address, and every step *admits* work only from a packet that can name where it
> came from. The record of truth moves before the code does. Nothing has to be awake for any of
> this to hold.

---

## 1. The measured failure

**A workflow cursor that most work could not pass.** Cairn journals a workflow string on each
piece of work — the steps it must cross and where it currently stands. On 2026-07-26 the
chokepoint that makes that cursor real was measured against the staged corpus. Of **17 staged
nodes, only 6 could pass through it** — and one of those six was handed a fabricated path.

So the cursor, *the field every reader turns into "where is this boat,"* was **policy on 11 of
17 nodes and fiction on a twelfth.** It is a live trouble, still open, still in the session
inbox.

**A build that ran from the conversation.** The pre-build preamble — orient, constrain, survey,
decompose — was a discipline. On 2026-07-28 that discipline visibly collapsed under proximity to
a plausible answer: bounds-checking started and never ran to completion, and the build proceeded
from what was in the conversation rather than from anything settled. Nothing detected it. The
author did.

**A summons filled with the wrong thing.** The workflow carried a mandatory `LEARNME` crossing.
It was ungated, so it filled up with close-bookkeeping — depositing this voyage's artifacts —
rather than with any evidence about whether the intention had *worked*. A mandatory step with no
gate becomes a step whose meaning drifts to whatever is convenient at the moment it is crossed.

---

## 2. The pattern

### 2.1 Eight steps, and they are a catalog rather than a pipeline

| Step | Trigger | Completed by | What the gate requires |
|---|---|---|---|
| **capture** | `/idea [prose]` | — (we move on) | 3 fields, compiled live |
| **intend** | `/intent [idea]` | the intent door | 9 fields, compiled live |
| **design** | `/design [intention]` | `/sorted` | 5 at the opening, 12 at the close |
| **chart** | `/chart` | 7 chart doors | schemas in code |
| **build** | `/sail` | `/sail` | not declared |
| **test** | the `PROVEME` crossing gate | `persist_validation` | the ratified 8 validation fields |
| **watch** | probe on validation complete | — (the probe is created) | — |
| **learn** | feedback arrives | the creating intention | — (a slope) |

A workflow is **composed per ticket** from this catalog, not marched down by every piece of
work. A node's class declares its string:

```
code-seam@v2: THINKME -> TICKETME -> BUILDME -> WATCHME(<object>) -> PROVEME -> [PROVED]
```

The bracketed token is the cursor. `WATCHME(<object>)` is a **free summons** — zero or more
times, any position — and it is in the string only if the ticket's author put it there.
**Optional to carry, mandatory to satisfy once carried:** it is not in the skippable set, so the
chokepoint's forward walk cannot step over it.

### 2.2 One chokepoint, six seats

Every state transition rides `emit` at the component's own address, and the crossing is
journaled to an append-only `history.json` **before the code moves.**

The chokepoint carries six distinct judgments:

1. **Rules** — is this transition legal for this class? A forward skip past a gate summons, an
   off-vocabulary target, an unknown class or version, a no-op self-loop, or a path that does not
   conform to the version it claims: each refused loudly. Base-class physics, inherited,
   un-delegable.
2. **The entry gate** (`buildme_rides_the_chart`, 2026-07-29) — a cast ticket may not begin
   building unless a berthed `validate` packet claims it. *Building from the conversation is a
   build error the door itself throws.*
3. **The promotion sweep** — the sieve stack, judging the build against its charter.
4. **The exit gate** (`proved_answers_the_chart`, 2026-07-29) — a claimed ticket may not close
   unless a verdict artifact answers **every** criterion of the claiming `validate` berth with a
   passing run verdict, and dispositions **every** hypothesis confirmed-or-killed with the
   deciding observation. *Unclaimed is green* — the deliberate inversion of the entry check.
5. **The watch-emission gate** — reads the crossing's ticket, finds the spec for the watched
   object, and refuses an unarmed probe.
6. **The clearance gate** (2026-08-10) — refuses a forward crossing into a rest state that
   carries no `cleared_by` and names no exemption, and re-reads the witness against the world.

**Entry gates the door, promotion judges the middle, exit measures the close.** Done is verified
by instrument at every mouth of the one chokepoint.

### 2.3 A transition factors into three rungs, and they stay separate

- **Rules** — is it legal for this class? Base-class physics.
- **Authority** — who may invoke it? Owner-gated, delegable *per operation*, never ambient. And
  the owner whose gate that is belongs to **the node**, not to the machinery operating the gate
  on its behalf. A 2026-08-10 ruling made this explicit: *"the gate is the refuser but it's doing
  so on behalf of the ticket. so the ticket owns the refusal."*
- **Truth** — the record of what happened. Local in each node's own history, indexed centrally,
  append-only, permanent.

**Decision local, record central, execution never in the index.** The register that answers
"what is open" is compiled from two vantages already on disk and invents no truth a node does not
already hold — it is an index, never a rival record.

### 2.4 The preamble is compiled, not remembered

The pre-build stage runs as seven schema-gated bricks — orient, constrain, survey, decompose,
triage, hypothesize, validate — each of which:

- runs a **deterministic floor** first (what exists: charters, verified paths, census rows);
- **walks its own graph tree** for what past requests of this class produced;
- runs a **bounded reasoning loop** on top, emitting a typed JSON packet with **per-field
  provenance** (`floor` | `tree` | `claude`) and confidence as a number rather than hedging
  prose;
- **template-fills the next stage's prompt from its own validated file.**

That last property is the enforcement. Because stage *n+1* is filled from stage *n*'s berthed
artifact rather than from the conversation, **a skipped stage is a build error, not a lapse.**
The chain is re-read whole at every link, so a broken link anywhere refuses.

Each stage's judges are deliberately unforgiving about specific past failures: `constrain`
refuses an empty *out* list (the founding failure was bounds-checking that never ran to
completion); `survey` refuses an absence with no measure attached (*an absence is a claim*);
`decompose` refuses a compose-piece that uses a holding the survey never found and a build-piece
that fills no measured absence (build-minimal as physics); `triage` uses **position as rank** so
no numeric priority field can drift against the list.

### 2.5 The measured asymmetry — and the reason for it

Two kinds of connection exist between steps:

- A **probe** *initiates*: a step fires the next one. Forward-pointing.
- A **citation** *admits*: a berth reference carried on the next packet and judged at the door
  that receives it. It fires nothing; it refuses work that cannot name where it came from.
  Backward-pointing.

Measured 2026-08-04: **every edge in the first half of the catalog is a citation, and all six of
them run. Every edge in the second half is a probe, and not one has ever fired.**

This document previously ended that paragraph with *"there is no third kind of arrow in the
system."* That was measured and found false. The correction stands in the record.

And the asymmetry is not a coincidence — it follows directly from having no daemons:

> **A backward edge needs nobody awake.** It is checked by a door that was going to run anyway,
> at the moment work arrives, and it costs nothing while nothing is happening. A forward edge
> needs something watching.

**The arrows that work are the ones pointing back.** For anyone adopting one idea from this
document, that is the one.

### 2.6 The claim rides every link

On a claimed chain, the ticket claim rides **every** packet. It may enter mid-chain; it may never
silently vanish. A door that receives a packet whose upstream berth claims a ticket refuses a
claimless packet, naming the one-field fix.

The ruling behind it, 2026-08-03, is worth quoting because it kills the two obvious softer
designs at once: **no warns** — nothing reads or answers a warning — and **no auto-inherit**,
because *a door-copied claim can never disagree with the berth it was copied from,* so the check
goes vacuous and a spliced chain sails with a door-minted claim.

---

## 3. How it is enforced

**Physics today:** the chokepoint's six seats, all raising named exceptions. The chart doors'
schema gates plus the chain re-read at every depth. The claim-rides-every-link check at every
follower door. Append-only journaling through a projector door, with `state` compiled from
`history` and a sieve that reds a hand-edited `state.json`. `/sorted`'s cast door refusing an
unresolvable node class, a one-word completeness answer, or a watch whose reason names no
resolvable referent.

**Still prose (tracked as debt):**

- The **build** and **test** steps declare no admission citation of their own beyond the BUILDME
  crossing's three.
- The **watch** and **learn** steps have no declared gate at all — they are the half of the
  catalog whose edges have never fired.
- An in-place edit of `history` itself is outside the append door's reach.
- A code floor cannot tell a concern about work in flight from the word "caveat" in a
  retrospective, so the turn-shape check stays heuristic.

---

## 4. What it costs

**Seven stages before a line of code.** The chart chain is genuinely expensive in wall-clock and
in author attention. It is justified by a work-measured claim — pre-answering the preamble in
deterministic code cut build tokens by roughly 89% before caching was counted — but that claim
comes from one corpus and should be re-measured elsewhere.

**Gates that fire on you are gates that cost you.** On 2026-08-11 a ticket whose whole purpose
was *"a refused clearance must leave a durable record"* was refused at its own `PROVED`
crossing, because retiring an unrelated prose IOU had edited a file after its proof was sealed,
moving the source fingerprint and closing the validation's horizon. Correct, and it cost a
re-seal.

**Artifacts accumulate.** 324 journaled crossings across 29 histories in 28 days, plus a berth
per chart stage per ticket in instance-space. The berths are runtime state and are allowed to
die with the box; the histories are records of truth and are not.

**A schema-gated handoff is brittle by design.** A field the reasoning loop repeatedly cannot
fill honestly is *a schema defect, not a discipline defect* — but telling the two apart takes a
human, and the failure mode meanwhile is a stuck chain.

---

## 5. What would falsify this

- **A stage output fails the template-fill test** — the next stage needed a model to re-read
  upstream prose. The interface was shortened, not compiled.
- **A packet field appears without provenance,** or confidence turns back into hedging prose.
- **The gates never bite.** A door that has refused nothing in a month is either perfect or
  decorative, and the base rate says which.
- **Forward edges keep not firing.** The catalog's second half is currently theory. If the spine
  runs and the probes still do not fire, the probe-as-initiator model is wrong, not merely
  unbuilt.
- **The cursor stays unreadable.** The 2026-07-26 trouble is open. If the chokepoint still
  cannot pass most staged work when it is next measured, the workflow string is a description
  rather than a mechanism.

---

## 6. What is built, and what is red

**Built.** All six chokepoint seats. All seven chart bricks with pre-installed judges — each
brick's judges were proved *before* its module existed, so a packet the door passes is a packet
the promotion gate passes. 324 journaled crossings: 62 into `PROVED`, 61 `PROVEME`, 53
`BUILDME`, 15 `WATCHME`, 27 into the now-dissolved `LEARNME`, 7 `TICKETME`. 587 nodes of
accumulated chart-stage memory across the seven trees.

**Red.**

- **The runtime spine has never run.** Every forward edge in the catalog is unfired.
- **The cursor trouble is open**, measured 2026-07-26 and not remeasured.
- **The clearance gate has n=3.** Two grants and one refusal, all by one hand. A gate that agrees
  with whoever calls it is indistinguishable from a gate that works at this sample size; a probe
  is armed and will clear only when 20 post-era crossings have all cleared or been exempted *and*
  clearance has refused at least once independently.
- Build, test, watch and learn declare no admission gate of their own.

---

*Pattern document, `press_office/PatternWorkflowAndArtifacts.md`. The step catalog's source of
truth is [`WorkflowDefinition.md`](WorkflowDefinition.md), which this document cites and never
re-authors. Part of the Cairn pattern series; the spine is
[`CairnArchitecture.md`](CairnArchitecture.md). All numbers from [`FactSheet.md`](FactSheet.md),
measured 2026-08-11.*

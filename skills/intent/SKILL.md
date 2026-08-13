---
name: intent
description: Birth a node — a new track or an aside. Unpack WHAT/HOW and trace it to the Telos, then stand the /challenge pass (required at every birth — the door refuses a packet without its answers) before /sorted. ONE OF THREE entry points (IDEA, INTENT, TICKET). A bug does not come here — it goes straight to TICKET.
---

# /intent — birth a node

You are firing the **intent nexus**: a fixed question set aimed at a fresh piece
of work. Answers route it forward; failure to trace routes it out. An intention
that shouldn't exist dies here, before any cost is spent on it (Law 1).

**One of three entry points** (ruling 2026-08-02): **IDEA** — pre-intention design,
where a thing is still being imagined; **INTENT** — this, where a piece of work is
born and traced; **TICKET** — where a *bug* enters, directly. IDEA became a real door
on 2026-08-04 (`/idea`, writing to `CairnCommons/ideas/`), and this skill now cites it
in `from_idea`; TICKET is still not a skill. Do not route a bug through here: if editing lines of code fixes it, it
is a ticket. Only if new information breaks the harmony of the system — an
intention implemented contrary to the actual intention — is it **structural**, and
structural is reconciled with Akien, not filed around.

The charter for this skill lives beside it in `intention+why.json`. This file is the
live question set; the charter is its compiled face.

## First: refresh + consult the model (Law 1 — the cheapest gate)

Before firing the questions, read the compiled intentions model — **fresh**. The
model is a ~0.2s compile of its sources; an out-of-band source write (a hand-edited
charter, one written outside a skill step) may have landed since the last compile.
So the reader **pokes the gate to refresh, then consults** — the read is the event
that refreshes it; no daemon watches on your behalf:

    $HOME/dev/src/cairn/cairn/tools/intentions_model_compiler/recompile_gate.sh

Then read `CairnCommons/intentions-congruency-lab/` — it holds a COPY of every
intention+why in the system, one file each — and ask: is anything already here
**like** this intent, or in **conflict** with it? Judge over the *whys* those files
carry, not surface strings — a real collision is exclusive-and-terminal; otherwise
it is a distinction to record. A hit here kills or reshapes the intent before any
cost is spent on it: re-deriving a settled intention is the defect this gate stops.
(This freshness step lives in the skill, not in the operator's memory — Law 4.)

## Fire these questions, in order

0. **Origin** — Which captured idea bore this? Answer with an id under
   `CairnCommons/ideas/`, a path to one, or `"none, because <X>"` where X names
   something checkable. It rides the packet as `from_idea`. Asked *before* the five
   because it is provenance, not a birth answer: without it, one idea that bears
   three intentions leaves the three unable to say they are siblings, and none of
   them able to point at the prose that bore them. Never captured? `/idea` first —
   it costs one command.
1. **WHAT** — In one sentence, what is the intent? (Not the approach — the aim.)
2. **HOW** — What's the approach, roughly? (First-cut only; `/sorted` deconstructs.)
3. **Trace** — What does this trace up to — which Telos aim, which Law?
   - If it traces: name the link, carry it on the node.
   - **If nothing traces: it doesn't belong.** Say so plainly and stop. Don't file
     it. (This is the routes-back edge — CLAUDE.md: "what can't trace up doesn't
     belong.")
4. **Shape** — Is this a **new track** or an **aside** to the track in hand? Name
   which, so the tree stays honest.
5. **Falsifier** — What would tell us this is done, or tell us it was the wrong
   intent? (A first-cut horizon; refined at `/sorted`.)

## Then CHALLENGE the newborn — required at every birth; the door enforces it

The adversarial pass runs on the five answers BEFORE the packet fires. This is
/challenge's firing event (ticket challenge-fires-at-intent): a node being born
is the event that already fires, so the pass rides it — never a clock, and never
an optional route (which fired zero times while one measured session stumbled
three times onto already-solved work). Answer the five challenge
questions against the newborn intent:

- **better_approach** — a cleaner, simpler, smaller way to the same aim? Name
  it, or say honestly that you looked and this is it.
- **prior_art** — solved already? The model-consult above feeds this (a
  congruency-lab hit IS prior art); check in-house first, then the field. A hit
  kills or reshapes the intent NOW, while changing it is cheap (Law 1).
- **hidden_assumption** — what is this taking for granted that could be false?
- **real_collision** — does it conflict with an intention, Law, or decision —
  *really*? The why of each side; exclusive-and-terminal, or it is a
  distinction to record.
- **back_up** — proceed, revise, or abandon: name the disposition.

The answers ride the packet's `challenge` field, and the door REFUSES a birth
without them — required-ness is the contract, not this paragraph, and softening
it back to optional reds the seam's own proofs. A kill here is a win (CP2): fire
with `exit: routed_out` and the pass's finding in the bullets. The honesty
floor: "considered, none found" with nothing actually consulted is the hollow
answer the ticket's horizon watches for — the trace records the answers
verbatim, and they stand at Akien's gate.

## Then FIRE THE DOOR — the firing is the answer, not a note about it

The five answers above are not held in the conversation. They are a packet, and
the packet goes through a gate that refuses an incomplete one. Write it to your
scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.machines.skill_block fire intent <scratchpad>/intent_packet.json
```

**One command, and it is this one.** `skills/intent/door.py` still runs and judges
identically — since 2026-08-05 the seam resolves this skill's `judge_packet` from its
own address, so the two entrances cannot differ in strictness. Before that they did:
the same packet was accepted by the seam and refused by the door, and the looser one
was the generic command anyone could reach.

The packet is a JSON object carrying, exactly:

- **from_idea** — the captured idea this came from: an id under `CairnCommons/ideas/`,
  a path to one, or `"none, because <X>"` where X carries something checkable. The
  door reads it — an origin that cannot be opened is refused, because the whole point
  of the field is that siblings born of one idea can find each other and the prose
  that bore them. If the idea was never captured, capture it first with **`/idea`**;
  it costs one command.
- **what** — question 1, one sentence, the aim.
- **how** — question 2, first-cut.
- **traces_to** — question 3. Name the Telos aim or Law. If *nothing* traces, say
  so **in this field** ("nothing — <why>") and set `exit` to `routed_out`. The
  routes-back edge is a recorded exit, not a silence.
- **shape** — `new track` or `aside`.
- **falsifier** — question 5, first-cut horizon.
- **challenge** — the adversarial pass, an object carrying the five answers
  (`better_approach`, `prior_art`, `hidden_assumption`, `real_collision`,
  `back_up`). Required at BOTH exits — a kill that never stood the pass is an
  unexamined kill.
- **exit** — `routed_forward` or `routed_out`. The kill is the exit that has been
  vanishing into conversation; an unnamed exit is how it goes on vanishing.
- **bullets** — a list of `{"text": ..., "stratum": "code"|"tree"}`: what this
  firing learned that Akien should see. **Forced at BOTH exits** — a node killed
  at /intent with no record of why teaches nobody. It stands at his gate until
  `cairn recordverdict` names it.

The contract is read from this skill's own charter (`intention+why.json`,
`input_contract`), not from code — run `python3 -m cairn.machines.skill_block contract
intent` to see the live fields and the why of each. A refusal names **every**
lack in one pass, and is itself recorded: the refusals are the denominator the
`intent-door-refusals` watch reads, so a refused firing is data, not a mistake to
hide. Fix the packet and fire again.

## What you produce

A **berth path** — printed by the firing, under
`~/.cairn/devices/skill_block/0/berths/intent/` — plus the node it records: a
node in intention fill-state, WHAT/HOW unpacked, traced, shaped, with a
first-cut falsifier. Nothing is cast yet; typing the node and binding its
gate-set happens inside `/sorted`, not here.

**Carry the berth path forward.** When `/sorted` casts this node, the ticket's
`intent_berth` field takes that path — and since 2026-08-01 (Akien's ruling) the
emit chokepoint refuses a cast ticket's BUILDME crossing when that field is
missing (`buildme_rides_the_intent`). So the berth is not a receipt: it is what
opens the build door later. A cast with no /intent firing behind it can still be
made honest — `"none, because <why>"` is the one other legal value — but the
judgeable reason is the price, and silence is not on the menu.

The natural next move:

- **`/sorted`** — when the points feel wrapped and you're ready for the resolution
  pivot. (`/challenge` has already fired — it is a step of this skill, not a route
  out of it; the adversarial escalation for a genuinely stuck design is `/advisor`.)

## Stay honest

- CP1: if you can't articulate the WHAT, say "I don't know yet" — don't confabulate
  an intent to have something to file. A firing you cannot fill is a firing that
  should be refused, and the door will refuse it; don't invent a field to get past it.
- Don't cast, don't file to commons, don't spawn children here. Those are `/sorted`'s
  job. `/intent` only births and traces.
- **The kill gets fired too.** The temptation is to reason your way to "this doesn't
  trace" and simply stop — no packet, no berth, nothing recorded. That is the exit
  this migration exists to catch: fire with `exit: routed_out`, bullets and all, and
  *then* stop.

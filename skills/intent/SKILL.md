---
name: intent
description: Birth a node — a new track or an aside. Unpack WHAT/HOW and trace it to the Telos. ONE OF THREE entry points (IDEA, INTENT, TICKET); run before /challenge and /sorted. A bug does not come here — it goes straight to TICKET.
---

# /intent — birth a node

You are firing the **intent nexus**: a fixed question set aimed at a fresh piece
of work. Answers route it forward; failure to trace routes it out. An intention
that shouldn't exist dies here, before any cost is spent on it (Law 1).

**One of three entry points** (ruling 2026-08-02): **IDEA** — pre-intention design,
where a thing is still being imagined; **INTENT** — this, where a piece of work is
born and traced; **TICKET** — where a *bug* enters, directly. Not all three are
skills yet. Do not route a bug through here: if editing lines of code fixes it, it
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

    $HOME/dev/src/cairn/cairn/intentions_model_compiler/recompile_gate.sh

Then read `CairnCommons/intentions-congruency-lab/` — it holds a COPY of every
intention+why in the system, one file each — and ask: is anything already here
**like** this intent, or in **conflict** with it? Judge over the *whys* those files
carry, not surface strings — a real collision is exclusive-and-terminal; otherwise
it is a distinction to record. A hit here kills or reshapes the intent before any
cost is spent on it: re-deriving a settled intention is the defect this gate stops.
(This freshness step lives in the skill, not in the operator's memory — Law 4.)

## Fire these questions, in order

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

## Then FIRE THE DOOR — the firing is the answer, not a note about it

The five answers above are not held in the conversation. They are a packet, and
the packet goes through a gate that refuses an incomplete one. Write it to your
scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.skill_block fire intent <scratchpad>/intent_packet.json
```

The packet is a JSON object carrying, exactly:

- **what** — question 1, one sentence, the aim.
- **how** — question 2, first-cut.
- **traces_to** — question 3. Name the Telos aim or Law. If *nothing* traces, say
  so **in this field** ("nothing — <why>") and set `exit` to `routed_out`. The
  routes-back edge is a recorded exit, not a silence.
- **shape** — `new track` or `aside`.
- **falsifier** — question 5, first-cut horizon.
- **exit** — `routed_forward` or `routed_out`. The kill is the exit that has been
  vanishing into conversation; an unnamed exit is how it goes on vanishing.
- **bullets** — a list of `{"text": ..., "stratum": "code"|"tree"}`: what this
  firing learned that Akien should see. **Forced at BOTH exits** — a node killed
  at /intent with no record of why teaches nobody. It stands at his gate until
  `cairn recordverdict` names it.

The contract is read from this skill's own charter (`intention+why.json`,
`input_contract`), not from code — run `python3 -m cairn.skill_block contract
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

The natural next moves:

- **`/challenge`** — if the design wants an adversarial pass before you commit to it.
- **`/sorted`** — when the points feel wrapped and you're ready for the resolution pivot.

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

---
name: intent
description: Birth a node — a new track or an aside. Unpack WHAT/HOW and trace it to the Telos. The work loop's entry point; run before /challenge and /sorted.
---

# /intent — birth a node

You are firing the **intent nexus**: a fixed question set aimed at a fresh piece
of work. Answers route it forward; failure to trace routes it out. This is the
cheapest gate in the system — an intention that shouldn't exist dies here, before
any cost is spent on it (Law 1).

The charter for this skill lives beside it in `intention+why.json`. This file is the
live question set; the charter is its compiled face.

## First: refresh + consult the model (Law 1 — the cheapest gate)

Before firing the questions, read the compiled intentions model — **fresh**. The
model is a ~0.2s compile of its sources; an out-of-band source write (a hand-edited
charter, one written outside a skill step) may have landed since the last compile.
So the reader **pokes the gate to refresh, then consults** — the read is the event
that refreshes it; no daemon watches on your behalf:

    $HOME/dev/src/cairn/cairn/intentions_model_compiler/recompile_gate.sh

Then read `CairnCommons/intentions/_model.json` and ask: is anything already here
**like** this intent, or in **conflict** with it? Judge over the *whys* the model
carries, not surface strings — a real collision is exclusive-and-terminal; otherwise
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

## What you produce

A **node in intention fill-state**: WHAT/HOW unpacked, traced, shaped, with a
first-cut falsifier. Nothing is cast yet — typing the node and binding its
gate-set happens inside `/sorted`, not here.

Hold it in the conversation (or `/note` it if it's an aside you're not chasing
now). The natural next moves:

- **`/challenge`** — if the design wants an adversarial pass before you commit to it.
- **`/sorted`** — when the points feel wrapped and you're ready for the resolution pivot.

## Stay honest

- CP1: if you can't articulate the WHAT, say "I don't know yet" — don't confabulate
  an intent to have something to file.
- Don't cast, don't file to commons, don't spawn children here. Those are `/sorted`'s
  job. `/intent` only births and traces.

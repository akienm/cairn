# /design — open the work on a born intention

The workflow's **third step** (`press_office/WorkflowDefinition.md`, step `design`) and
the only one with a **different skill at each end**: `/design` opens the joint work,
`/sorted` closes it.

Everything between a berth being born and a ticket being cast happens in conversation
today, and conversation leaves no artifact. This door does not try to capture the
thinking — `/sorted`'s twelve fields are where the thinking has to stand up. It captures
the **arrival**: which intention, from where, what has to be resolved, and what would
make it castable.

The charter lives beside this file in `intention+why.json`.

## First: read the berth, and read around it

You are opening on a node somebody already birthed. Before firing:

- **Read the intent berth.** Its `answers` carry the WHAT, the HOW, the trace, the
  shape, the falsifier and the challenge pass. Everything asked at birth is answered
  there; asking again is the defect Law 1 names.
- **Refresh and consult the model**, exactly as `/intent` does — the compile is ~0.2s
  and an out-of-band charter write may have landed since:

  ```bash
  $HOME/dev/src/cairn/cairn/tools/intentions_model_compiler/recompile_gate.sh
  ```

  Then read `CairnCommons/intentions-congruency-lab/`. The birth already ran a
  prior-art pass; this is the second look, against a design that now has shape. A hit
  here is cheaper than a hit at the cast.

Whatever those two reads surface is what the `bullets` are for. **A design session that
opens having noticed nothing usually has not read anything.**

## Fire the door

Write the packet to your scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/design/door.py <scratchpad>/design_packet.json
```

Five fields:

- **intent_berth** — the `/intent` berth path this designs on. The door reads it: it
  must exist, it must be an `intent` berth, and it must have exited `routed_forward`.
  Designing on a node the trace question killed is refused, and the refusal says why.
  The one other legal value is `"none, because <X>"` where X carries something
  checkable — a path, a cast ticket id, a `bin/cmd/<name>`.
- **entering_from** — `"intent"` for a first pass, or `"sorted:<berth path>"` when
  `/sorted` routed this node back on a completeness red. **Say which honestly.** This
  is the field that makes a return trip countable, and a second pass recorded as a
  first one erases the only signal we have about which of `/intent`'s questions are
  letting things through.
- **open_questions** — a **list** of what must be resolved before this can be cast.
  The design step's work list, item by item, each one strikeable.
- **ready_when** — the predicate that ends this step: what would make this castable.
  Not the intention's falsifier (that asks whether the *work* is done or wrongly
  aimed); this asks whether the *thinking* is finished enough to bind gates to.
- **bullets** — `{"text": ..., "stratum": "code"|"tree"}`, what the two reads above
  surfaced.

The live contract is `python3 -m cairn.machines.skill_block contract design`. A refusal names
every lack in one pass and is itself recorded.

## Then do the work

Work the `open_questions` down. That is the step. There is no ceremony between here and
`/sorted` — no intermediate firings, no progress records. When `ready_when` is true, go
to `/sorted`.

If the work reveals that the intention was wrong, **that is a real outcome and it is not
recorded here**: take it to `/sorted` and route out with a `disposition`. This door has
no `exit` field on purpose — the step's exits are `/sorted`'s to record, and two
components recording one outcome is how they come to disagree about it.

## What you produce

A **berth path** under `~/.cairn/devices/skill_block/0/berths/design/`, recording that a
design session opened on a named intention with a named work list.

The natural next move:

- **`/sorted`** — when `ready_when` is true. It runs the completeness check, casts the
  node, binds its gates, and files it.

## Stay honest

- CP1: if the `open_questions` list is empty because you cannot see any, the node is
  probably ready to cast already — go to `/sorted`. Do not invent questions to fill the
  field. An invented work list is worse than none, because it makes a node that was
  ready look like one that needed a pass.
- Don't re-ask the birth's questions. WHAT, HOW, trace, shape, falsifier and the
  challenge pass are answered on the berth. If one of them is *wrong*, that is a
  finding in the bullets and a question in the list — not a re-run of `/intent`.

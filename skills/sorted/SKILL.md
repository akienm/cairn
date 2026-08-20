---
name: sorted
description: The resolution pivot — assert the points are wrapped, run the inward completeness check, cast the node THROUGH THE DOOR (typed, gates bound, watch answered — a packet a gate refuses incomplete), spawn children and/or escalate, then resolve. Casting lives here; there is no separate /ticket.
---

# /sorted — the resolution pivot

You are firing the **sorted nexus**: the moment a piece of thinking stops being
open and gets resolved into structure. This is where a node is **cast** — typed and
bound to the gates its type requires. There is no separate `/ticket`; casting is a
step *inside* `/sorted`. Filing to the commons is a *consequence* of resolving, not
the meaning of it.

**The cast rides a door** (since 2026-08-03, ticket `sorted-becomes-a-learning-block`
— tenant #2 of the skill_block seam): the completeness answers, the class, the bound
gates and the watch are a PACKET, fired through a gate that refuses an incomplete one
with every lack named in one pass. A refused or berthed packet survives on disk, so a
cast interrupted mid-thought is a file to resume, not a conversation to re-derive.

The charter lives beside this file in `intention+why.json` — its `input_contract`
is the packet's live field list (`python3 -m cairn.machines.skill_block contract sorted`).

## The sequence

### 1. Assert — "all points wrapped"
You (or the human) claim the design/conclusion is complete. This is a claim, and a
claim gets checked — by the door, as fields, not as a feeling.

### 2. Inward completeness check (the challenge GATE)
Answer the coverage questions — this is the *at-the-claim* check, distinct from the
`/challenge` skill's *before-the-claim* pass. Each answer is a packet field, IN
SUBSTANCE (a one-word pass is the hollow check the door refuses):
- **assumption_check** — any unstated assumption still load-bearing?
- **missing_check** — any point asserted-wrapped that actually isn't?
- **falsifier_check** — the stated falsifier and horizon. (No falsifier → not
  ready to cast.)
- **collision_check** — collides with an existing intention/Law/decision — *really*
  (why of each side, exclusive-and-terminal), or a distinction to record?

**Red on any of these → the firing exits `routed_out`, `disposition:
"not-ready"`.** Casting an incomplete node is the defect this gate exists to
stop — and the kill gets fired too: a red that lives only in conversation teaches
nobody.

### 3. Assemble the cast — the packet's remaining fields
- **node_class** — name it (`skill`, `concept-piece`, `code-seam`, …). The class is
  a charter in `CairnCommons/node_classes/`; the door refuses one that does not
  resolve — an absent class needed is a demand to write it FIRST.
- **workflow** — the full string with its cursor at the cast
  (`code-seam@v2: THINKME -> [TICKETME] -> …`). The door runs the chokepoint's own
  parser and conformance check, so a drifted string costs one fix here instead of a
  dead voyage at its first crossing.
- **gates_bound** — the class's gate-set transcribed onto this node. Invariant for
  every class: it gets **proved** and it **feeds back to origin on failure** (Laws
  3 + 8). Variable per class: which gate, which check-type.
- **watchme** — **BY DEFAULT, CAST ONE.** How will we know this intention actually
  *worked*? Either the full spec the emission gate reads (matching the
  `WATCHME(<object>)` in the workflow string — the door fires the gate's own
  `watchme_spec_error`, so passing the door is passing the gate):

      "watchme": {"object": "<the same object named in the string>",
                  "trigger":  "when does it fire",
                  "enough":   "when has it learned enough to stop",
                  "carrier":  "what rides back (default: a verdict artifact
                               against THIS ticket's falsifier)",
                  "nexus":    "which tree/target it teaches",
                  "consumer": "who reads it",
                  "probe":    "<berth path — where the probe module will live;
                               the gate resolves ARMED from this path>"}

  or `"none, because <X>"` — and the reason must carry a **resolvable referent**
  (a path on disk, a cast ticket id, a roster command): a plausible sentence
  pointing at nothing checkable is the hollow pass the door was built against.
  UNSPECIFIABLE is a RED (route back — the falsifier is unwritable); specifiable
  but-not-yet **drops a ticket and cites it in the reason**. The probe berths
  **with what it watches**, and carries **no authority** (Law 6).
- **children** — the deconstruction, if any (`/sorted` fires again per child;
  children prove before parents), or `"none, because <X>"`.
- **exit / disposition** — `routed_forward` + `"cast"`; or `routed_out` +
  `"not-ready"` / `"escalated:<rung>"`. The escalation ladder, cheapest
  first: back up and re-question · `/advisor` · a bounded subagent · review the
  field · **ask Akien**. Stuck → escalate, don't confabulate (CP1).
- **bullets** — what this firing learned that Akien should see, `{text, stratum}`,
  stratum `code|tree`. Forced at BOTH exits.

### 4. FIRE THE DOOR — the firing is the cast, not a note about it

Write the packet to your scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/sorted/door.py <scratchpad>/sorted_packet.json
```

A refusal names **every** lack — flat and semantic — in one pass; fix the packet
and fire again (the door re-judges the whole packet, so one fix cannot earn a new
first-pass refusal for something already named). The refusal is traced: it is the
denominator the `sorted-door-refusals` watch reads, data rather than a mistake to
hide. **The firing prints a berth path — carry it.**

### 5. Resolve
Survivors **file to CairnCommons** — the cast node to `tickets/`, kicked-back
questions to the question corpus. Filing is the consequence of resolving, not a
separate act. **The ticket carries the berth**: put the printed path in the
ticket's `"sorted_berth"` field — the emit chokepoint's BUILDME entry gate demands
it (`buildme_rides_the_sorted`), alongside the chart claim and `intent_berth`. A
cast that predates the door, or genuinely cannot fire it, records
`"sorted_berth": "none, because <X>"` with a resolvable referent — silence reds at
the crossing.

**Write-through the model.** If what you filed is a *model source* — a homeless
intention in `intentions-not-beside-code/`, or a beside-code `intention+why.json` charter —
poke the compiled model's sole write-door in the **same act**, so the next
"I intend X" dup/conflict check reads a current model (Law 1):
`$HOME/dev/src/cairn/cairn/tools/intentions_model_compiler/recompile_gate.sh`.
A cast that only files a `tickets/` entry is *not* a model source yet — it becomes
one when its charter is written beside the code, and that write pokes the door then.

### 6. Close the boundary — /saveslate, then /compact

A resolution pivot is a compaction-safe boundary by construction: the cast node,
its berth, its gates, and its filings are all on disk. Fire **/saveslate** (the
in-commons continuity record), then tell Akien the boundary is compact-safe and
invite `/compact` — the context above the pivot is scaffolding now. /compact is a
client command you cannot fire; making the boundary loud is the step.
(Ruling 2026-07-28: the same close ends /sail, the build skill.)

## Routing

- Completeness red → `routed_out` / `not-ready`, fired and berthed. The node stays
  in hand; re-question the gap or escalate.
- Can't resolve → `routed_out` / `escalated:<rung>` (not a dead end).
- Resolved → the node is cast through the door, filed with its berth, and its
  gate-set is now live; build proceeds under the bound gates, prove closes it (or
  kicks it back — a disposition, CP2).

## Stay honest

- Don't cast to feel progress. An un-wrapped node fires `routed_out`; respect the
  red — the door records it either way, which is the point.
- "Verdict and seal from the same hand" holds only for code (the tester). For a
  human-proved class the reviewers are the verdict and the notary is the seal —
  different hands. Don't collapse them. (Owed physics: none yet — a human-proved
  cast is rare; the door's `gates_bound` field is where it would land.)

## Finally, when all else done

/compact

---
name: sorted
description: The resolution pivot — assert the points are wrapped, run the inward completeness check, cast the node (type it + bind its gates), spawn children and/or escalate, then resolve. Casting lives here; there is no separate /ticket.
---

# /sorted — the resolution pivot

You are firing the **sorted nexus**: the moment a piece of thinking stops being
open and gets resolved into structure. This is where a node is **cast** — typed and
bound to the gates its type requires. There is no separate `/ticket`; casting is a
step *inside* `/sorted`. Filing to the commons is a *consequence* of resolving, not
the meaning of it.

The charter lives beside this file in `intention+why.json`.

## The sequence

### 1. Assert — "all points wrapped"
You (or the human) claim the design/conclusion is complete. This is a claim, and a
claim gets checked.

### 2. Inward completeness check (the challenge GATE)
Fire the coverage questions — this is the *at-the-claim* check, distinct from the
`/challenge` skill's *before-the-claim* pass:
- **Assumption?** — any unstated assumption still load-bearing?
- **Missing?** — any point asserted-wrapped that actually isn't?
- **Falsifiable?** — is there a stated falsifier and horizon? (No falsifier → not
  ready to cast.)
- **Collides?** — with an existing intention/Law/decision — *really* (why of each
  side, exclusive-and-terminal), or a distinction to record?

**Red on any of these → route back to design.** Casting an incomplete node is the
defect this gate exists to stop.

### 3. Cast the node
- **Type it** — name its node-class (`skill`, `concept-piece`, `code-seam`, …).
  The class is a charter in `CairnCommons/node_classes/`; if the class you need
  doesn't exist yet, that's a demand to write it (a class cannot exist without
  writing down what it's for).
- **Bind its gates** — the class's gate-set becomes this node's required
  transitions. Invariant for every class: it gets **proved** and it **feeds back to
  origin on failure** (Laws 3 + 8). Variable per class: which gate, which check-type
  (proof gate for code; quorum signature gate for a concept-piece; a skill node also
  hangs the cairnmap recompile gate).

A cast node is a **ticket** — the universal work unit. Its `state` field *is* the
pipeline instance; nothing else holds a second copy of where it stands.

### 4. Deconstruct and/or escalate
- **Spawn children** to break the node down; children prove before parents.
- **Escalate when stuck** (a ladder, cheapest first): back up and re-question ·
  `/advisor` (built-in, Opus, adversarial) · a bounded Fable subagent (independent
  *because* its context is limited) · review the field · **ask Akien** (the
  signature-gate escalation). Stuck → escalate, don't confabulate (CP1).

### 5. Resolve
Survivors **file to CairnCommons** — the cast node to `tickets/`, kicked-back
questions to the question corpus. Filing is the consequence of resolving, not a
separate act.

**Write-through the model.** If what you filed is a *model source* — a homeless
intention in `intentions-other/`, or a beside-code `intention+why.json` charter —
poke the compiled model's sole write-door in the **same act**, so the next
"I intend X" dup/conflict check reads a current model (Law 1):
`$HOME/dev/src/cairn/cairn/intentions_model_compiler/recompile_gate.sh`.
A cast that only files a `tickets/` entry is *not* a model source yet — it becomes
one when its charter is written beside the code, and that write pokes the door then.
Full recompile is ~0.2s; and the `/intent` read-refresh backstops anything authored
outside a skill step (the reader pokes the gate before consulting — the read is the
event, no daemon; see the intentions_model_compiler charter's host_seam).

## Routing

- Completeness red → back to design.
- Can't resolve → an escalation (not a dead end).
- Resolved → the node is cast, filed, and its gate-set is now live; build proceeds
  under the bound gates, prove closes it (or kicks it back — a disposition, CP2).

## Stay honest

- Don't cast to feel progress. An un-wrapped node casts to a red completeness check;
  respect the red.
- "Verdict and seal from the same hand" holds only for code (the tester). For a
  human-proved class the reviewers are the verdict and the notary is the seal —
  different hands. Don't collapse them.

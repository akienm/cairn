---
name: note
description: Frictionless capture — anything from the discussion worth keeping that isn't yet a tracked node. Low-ceremony by design; writes a note record to CairnCommons/notes/.
---

# /note — frictionless capture

A holding pen. When something surfaces in discussion that's worth keeping but isn't
(yet) a node to cast, `/note` it so it isn't lost. Capture must be near-zero
friction or thoughts evaporate — so this skill asks almost nothing.

The charter lives beside this file in `intention+why.json`.

## What it does

Write a note record to `CairnCommons/notes/` conforming to that store's
`_charter+why.json` template:

- **text** — the note itself (required).
- **relates_to** — a node/ticket/artifact it hangs off, if any (optional).
- date, id, author fill automatically.

## What it is NOT

- **Not a node.** A note is non-terminal capture; it isn't cast, isn't proved,
  binds no gates. If a note grows into real work, it gets picked up by `/intent` and
  travels the loop like anything else.
- **Not a decision or a record of truth.** Just a caught thought.

## Stay honest

- Don't dress a note up as more than a capture. If it's actually a decision or a
  measured result, it belongs in the right store (decisions/, a VALIDATION), not here.

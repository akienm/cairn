---
name: loadslate
description: Session open — restore continuity by reading the latest slate from CairnCommons/slates/, so a new session resumes without re-deriving where the last one left off.
---

# /loadslate — session open

Restore the working context at the start of a session. Read the most recent slate
from `CairnCommons/slates/` and reconstitute: what was in flight, the next
direction, the open threads.

The charter lives beside this file in `intention+why.json`.

## What it does

1. Find the latest slate in `CairnCommons/slates/` (or a named one, if asked for).
2. Read it and restate, briefly, the resumption point: in-flight work, next
   direction, open threads.
3. Cross-check against the working map (`MAP.md`) and CC's memory index — the slate
   is authoritative for *session continuity*; the map is authoritative over memory
   of the conversation. Name any drift rather than silently reconciling it.

## Stay honest

- A slate is a **best-guess snapshot at a boundary**, not ground truth about the
  code. Verify a claim against the territory before acting on it (Law 3 — nothing
  known until measured; a slate that names a file/flag is a pointer, not a proof).
- If no slate exists, say so and open cold from the map — don't invent a continuity.

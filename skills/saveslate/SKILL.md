---
name: saveslate
description: Session close — write a slate to CairnCommons/slates/ capturing the state of work at the boundary (in-flight, next direction, open threads) so the next session resumes cleanly.
---

# /saveslate — session close

Precipitate the session's continuity into a durable artifact. Write a slate to
`CairnCommons/slates/` capturing where things stand, so the next session (`/loadslate`)
resumes without re-deriving.

The charter lives beside this file in `intention+why.json`.

## What it does

Write a slate record conforming to `CairnCommons/slates/_charter+why.json`:

- **in_flight** — what's actively being worked, and its state.
- **next_direction** — the intended next move.
- **open_threads** — unresolved questions, IOUs, things to verify.
- date, id, session, author fill in.

Keep it honest and specific: name files/tickets/gates, flag what is *my read* vs
*ratified*, convert relative dates to absolute.

## Relation to CC's memory

CC's `~/.claude` memory is a personal cross-session store; a **slate is the
in-commons, shareable continuity record** — knowledge that would be lost to the
system, not just to CC, if the session vanished. They can agree; when they differ,
say so.

## Stay honest

- A slate records the *current best guess* at the boundary, carrying its open
  threads — not a claim that anything is finished.
- Don't overstate completion. "Drafted, not yet ratified" is a truer slate line than
  "done."

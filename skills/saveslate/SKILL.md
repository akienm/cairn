---
name: saveslate
description: Session close — write a slate to CairnCommons/slates/ capturing the state of work at the boundary (at-sea, next direction, open threads) so the next session resumes cleanly.
---

# /saveslate — session close

Precipitate the session's continuity into a durable artifact. Write a slate to
`CairnCommons/slates/` capturing where things stand, so the next session resumes
without re-deriving.

**You are now writing for a program, not for a skill.** Since 2026-07-31 the read
half is `bin/cmd/slate`, fired by a SessionStart hook — the newest slate's
`at_sea`, `next_direction` and `open_threads` are injected into the next session
whether anyone asks for them or not. Two consequences worth holding while you
write: the slate is read EVERY session, so its length is a standing context cost
(~2,700 est. tokens at present); and the reader is no longer free to skip it, so a
field padded with narration is padding that everyone pays for, forever. Extra keys
beyond those three are NOT read — put it in one of the three or accept that nothing
will see it.

The charter lives beside this file in `intention+why.json`.

## What it does

Write a slate record conforming to `CairnCommons/slates/_charter+why.json`:

- **at_sea** — what's actively being worked, and its state.
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

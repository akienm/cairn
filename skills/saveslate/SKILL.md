---
name: saveslate
description: Session close — compile the slate FROM INSTRUMENTS (git log, ticket cursors, the standing chain) and write it THROUGH THE DOOR, which refuses a slate written from the head alone. The next session inherits what you write here as ground truth.
---

# /saveslate — session close

Precipitate the session's continuity into a durable artifact. Since 2026-08-03
(ticket `slate-compiles-from-the-world`, tenant #3 of the skill_block seam) the
slate **compiles from the world and writes through a door** — the read half
(`bin/cmd/slate`, fired by the SessionStart hook) injects it into every future
session, so a confident wrong slate compounds forever; the door is what stops
that at the source.

The charter lives beside this file in `intention+why.json` — its
`input_contract` is the packet's live field list
(`python3 -m cairn.machines.skill_block contract saveslate`).

## 1. RUN THE INSTRUMENTS — before writing a word

The slate is compiled from these outputs, not from your impression of the session:

```bash
# what actually happened (both repos) — and the heads the door will verify
git -C ~/dev/src/cairn log --oneline -15 && git -C ~/dev/src/cairn rev-parse HEAD
git -C ~/dev/src/CairnCommons log --oneline -15 && git -C ~/dev/src/CairnCommons rev-parse HEAD
# which tickets moved (cursor brackets changed this session)
git -C ~/dev/src/CairnCommons diff HEAD~15 --stat -- tickets/ | tail -20
# any voyage in flight — the standing chain for its ticket
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.machines.chart.live chain <ticket-id>
```

The two `rev-parse HEAD` hashes go in the packet's `instruments_read.git_heads` —
**the door refuses a write whose heads do not match the live repos**, so this step
cannot be skipped or faked from the transcript.

## 2. Compile the three fields — from those outputs

- **at_sea** — what's actively being worked, and its state.
- **next_direction** — the intended next move.
- **open_threads** — unresolved questions, IOUs, things to verify.

Honest and specific: name files/tickets/gates, flag *my read* vs *ratified*,
convert relative dates to absolute. **The reader consumes ONLY these three** —
any other content key is refused (context nothing reads is paid forever), and the
three together must stay under the measured ceiling (10,000 chars; the corpus
median is ~6,900 — long slates are the defect, not the flex).

## 3. Fire the door — the write rides it

Write the packet (slate_id, the three fields, instruments_read, bullets, exit)
to your scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/saveslate/door.py --session <session-id> <scratchpad>/slate_packet.json
```

A refusal names every lack in one pass and **writes nothing** — fix and refire.
On pass the door berths the firing AND writes `CairnCommons/slates/<id>.json` in
the same act; there is no other path to the store. Report the berth and the slate
path, then commit the slate (committed is part of done).

## Relation to CC's memory

CC's `~/.claude` memory is a personal cross-session store; a **slate is the
in-commons, shareable continuity record**. They can agree; when they differ,
say so.

## Stay honest

- A slate records the *current best guess* at the boundary — not a claim that
  anything is finished. "Drafted, not yet ratified" is a truer line than "done."
  (The door checks that you LOOKED; whether you looked honestly is still yours —
  the `slate-door-refusals` watch counts whether the door ever bites.)

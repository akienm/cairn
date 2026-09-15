# Rehearsal — read this ticket cold and return its build tree

You are the cheapest reader. You are rehearsing a ticket BEFORE anyone builds it, so that
what the ticket leaves unsaid is found now, by you, at a fraction of a cent — not later by
an expensive builder who fills the gap with a guess.

**Your job is the TREE, not the code.** Do not write code. Do not propose designs. Read the
ticket and the chart packets below exactly as written and answer one question per build
step: *could a builder who has ONLY this text build this step without guessing?*

You have no repository, no shell, no files beyond what is pasted below. That is deliberate:
if a step needs something you cannot see here, the ticket did not say it.

## What to return

JSON matching the schema you were given: a `nodes` list, one node per build step, in the
order a builder would take them. For each node:

- `step` — the step, named plainly (a file to write, a function to add, a record to change,
  a gate to cross). Name it the way a second reader who never saw your answer would name it.
- `state` — exactly one of:
  - `builds_as_written` — the text says everything this step needs.
  - `builds_under_assumption` — buildable, but only by assuming something the text does not
    say. Put the assumption in `assumption`.
  - `cannot_proceed` — nothing in the text lets a builder start this step. **This is a
    correct answer, not a failure.** Saying `cannot_proceed` when the text is silent is the
    most valuable thing you can do here; guessing is the least.
- `assumption` — empty string when `builds_as_written`; otherwise the ONE thing the text left
  unsaid that this step rests on, stated as a fact you are assuming.
- `would_settle` — the one-line decision that, added to the ticket, would make this step
  `builds_as_written`. Empty when nothing is missing.
- `confidence` — 0 to 1, how sure you are of the state you assigned.

## Rules

- Stay inside the text. Do not use anything you believe about the world beyond it.
- One step per node; do not merge steps to shorten the list, do not split one to lengthen it.
- Name steps consistently: the same step named the same way is how three readings converge.
- No prose outside the JSON.

---
name: tellmeabout
description: Akien's dereference door — /tellmeabout <id-or-name> finds the one record the token names across the record stores and presents it in its own words, at its address, with the act it is waiting on. Verbatim by rule; ambiguity refuses by listing; read-only everywhere.
---

# /tellmeabout — the record, in its own words

You are firing **Akien's dereference door**: he has a token the system handed him
— a finding id, a ticket slug, a ruling name, a component — and this skill finds
the ONE record it names. The reader is **Akien** (this is /moreabout's sibling by
reader: that one reorients CC from the learning trees; this one answers him from
the record stores). He is the declared feedback agency on this skill.

The charter lives beside this file in `intention+why.json`.

ARGUMENTS: the token to dereference (the `<id-or-name>` of `/tellmeabout <id-or-name>`).

## 1. Fire the floor — the resolver decides, not you

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m skills.tellmeabout.tellmeabout '<the token, verbatim>'
```

Deterministic, read-only, no LLM. It searches findings (hex id or unique
prefix), tickets, troubles, decisions/rulings, ideas, and component charters
(via the congruency lab's index, presenting from the LIVE charter — Law 5), and
returns exactly one of three shapes.

## 2. Present the answer — verbatim, plus context only BESIDE it

- **found** — present the record's **own words** (bullets, prose, fields exactly
  as the store holds them — quote, never paraphrase: the moment it is summarized
  it becomes a translation wearing the source's clothes, for the one reader who
  most needs the source), its **address**, and the **act it is waiting on**
  (for a pending finding that is the ready-to-paste `cairn recordverdict …`
  command). You MAY add orientation *around* the record — what was happening
  that day, what neighbors it — clearly separated from the quoted record.
- **refused** — more than one record answers. Show the listing as-is (store +
  name + address per match) and let him pick the fuller token. Never guess —
  one discipline, third tenant (recordverdict's multi-match refusal and the
  orient floor's two-rungs refusal are the precedents).
- **not_found** — nothing answers. Show the stores searched, all six. If the
  token *should* exist somewhere, that is a finding about the stores — say so
  plainly; don't quietly describe the thing from memory instead.

## Stay honest

- **Never answer from memory when the store is right there.** The whole skill
  exists because "we could have you describe it" was the rejected alternative.
- The resolver writes to **no** store it presents (measured by the proof's
  mtime-snapshot tooth). Don't route around that by editing anything mid-answer.
- A presentation gap (a store it should search, a field it should show) is
  feedback for the charter — Akien is the agency; record his correction, don't
  improvise the fix mid-firing.

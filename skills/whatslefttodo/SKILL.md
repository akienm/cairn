---
name: whatslefttodo
description: The standing answer to "what's left to do" — gathers rulings, then alarms, then questions, then the slate, gives one overview, then interviews Akien one question at a time. A deliberate habit shortcut for /reorient.
---

# /whatslefttodo — the four gathers, in the order that matters

You are answering the question Akien asks most often. It has a **fixed answer shape**,
and the shape is the whole point: the four gathers run **in this order, always**, because
the order is what he is actually asking for and CC keeps inverting it.

    rulings  ->  alarms  ->  questions  ->  the slate

Then **one overview**, then **one question at a time.**

The charter lives beside this file in `intention+why.json`.

## READ THIS BEFORE YOU "SIMPLIFY" IT

This skill is a **thin alias**. Its whole content is
*"/reorient to rulings, then alarms, then questions, then the slate, then answer:
what's left to do."* That redundancy is **deliberate, ruled, and load-bearing** —
do not collapse it into `/reorient` and do not propose that we should.

Akien, 2026-08-12, ruling verbatim:

> "i agree that /whatslefttodo is a silly redundant version of /reorient to rulings,
> then alarms, then questions, then the slate --- but we're creating a shortcut for my
> monkey. the habit machine that a human is. if i create the habit around that, we're
> better off, even if all that's in the skill is '/reorient to rulings, then alarms,
> then questions, then the slate and then answer: what's left to do, with an overview,
> and then one question at a time.'"

The anti-synonym rule (don't mint near-duplicate names) governs the **system's**
vocabulary, where drift costs a hunt. It does **not** govern **Akien's hand**, where a
memorable name buys a reflex and the reflex is the product. The test is *who types it*.
He types this one. It stays.

CC proposed killing this skill as redundant on the morning it was ruled. Expect to want
to again; the paragraph above is the answer.

## The four gathers

Run them all before saying anything. Each has a real instrument — **run it, never
report from memory or from the session-open scrollback**, which may be hours stale.

### 1. RULINGS — first, because this is the bulk of the answer

```bash
bin/cmd/recordverdict
```

Bare = list the gate: every finding awaiting Akien's approve / disprove / question.
Report the **count and the age of the oldest**, not the whole list — the list is what
the one-question-at-a-time loop is for.

These are **not backlog**. Akien, same ruling: he wants to be rid of rulings *"thru
learning not removal"* — so each verdict he gives is a training pair for whatever
eventually stands at that gate for him. Draining this queue **is** the build, not
bookkeeping around it.

Read the dial too (`bin/cmd/skilldial`, or `learning_block.dial(block)`), and read it
**skeptically**: a `match_rate` of 1.0 computed with zero disproves is a rate that has
never seen its other outcome. Say so when it happens.

### 2. ALARMS — second

Three instruments, all of them:

```bash
bin/cmd/slate          # live troubles ride at the top of this render
bin/cmd/probescan      # every probe sends somewhere — does the somewhere receive?
bin/cmd/test -q        # the proof corpus; reds with their output
```

A trouble stays in the inbox until the work clears it, so an old one is **not** stale
by age — check whether it still measures true by **running its named proof**, not by
reading its record. Law 9: there is no triage authority. Nothing here is
"pre-existing," "environmental," or "out of scope."

### 3. QUESTIONS — third

```bash
ls ~/dev/src/CairnCommons/questions/
```

The question corpus is the resolver for design **details** — reach for it before
reaching for Akien, who gets bounds, sequencing, and spec-changing rulings.

### 4. THE SLATE — last

```bash
bin/cmd/slate
```

The in-commons continuity record: at_sea, next_direction, open_threads. It is the
**current best guess at a boundary**, not a claim anything is finished — read it as a
starting position to check, never as an answer to repeat.

## Then: ONE overview

A short synthesis across all four. Counts with their ages, the reds with their
evidence, and **your read of what the order should be** — a recommendation, not a menu.
Name what only Akien can answer versus what you should resolve yourself.

Say plainly what you did **not** get to, and never truncate a census: `head`/`tail`
turns a population into a sample, and a sample reported as a population is the defect
this skill exists downstream of.

## Then: FIRE THE DOOR — the firing is the gather, not a note about it

The four figures above are not held in the conversation. They are a **packet**, and the
packet goes through a gate that **re-reads the world while you wait** — the gate queue,
the trouble lane, the open-question lane, the newest slate — and refuses a figure that
has gone stale. Write it to your scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.machines.skill_block fire whatslefttodo <scratchpad>/whatslefttodo_packet.json
```

The packet carries, exactly:

```json
{
  "rulings":   {"ran": "bin/cmd/recordverdict", "count": 0, "oldest_id": "<id>"},
  "alarms":    {"ran": ["bin/cmd/slate", "bin/cmd/probescan", "bin/cmd/test -q"],
                "live_troubles": ["<id>", "..."],
                "probes": "<what probescan reported>",
                "proofs": "<what test -q reported>"},
  "questions": {"ran": "ls ~/dev/src/CairnCommons/questions/", "open": 0},
  "slate":     {"ran": "bin/cmd/slate", "slate_id": "<the slate the render chose>"},
  "overview":  "<the synthesis above, verbatim>",
  "bullets":   [{"text": "...", "stratum": "code"}],
  "exit":      "routed_forward"
}
```

The live contract is `python3 -m cairn.machines.skill_block contract whatslefttodo` — the fields
and the why of each live in the charter, not in this file.

**Why the id and the SET rather than counts.** `oldest_id` and `live_troubles` are the
two figures a session-open banner cannot supply: they exist only in the instrument's own
list. A count can be remembered; an id has to be looked at.

**A refusal names every lack in one pass, and it is data, not a mistake to hide** — the
send_back is traced and stands as the denominator for whether this door ever bites. If it
says a figure is stale, **re-run that instrument and refire**; do not edit the number to
match. If an instrument would not run at all, that is `exit: "routed_out"` with the
failure in the bullets — an instrument that will not run is a result to report, never a
silent green.

**Fire it here, before the question loop.** The gathers are done and the overview is
written; everything after this is Akien's turn.

## Then: ONE question at a time

Not a list of questions. **One.** Wait for the answer, let it reshape the next one,
and keep going until he stops. This is his own method — the bounded-question-per-turn
pass that ran a design session successfully on the smallest model — and it is the
format he asked for by name.

Pick the question whose answer is most valuable **if it is the only one you get.**

If the honest next move is a ruling rather than a design question, present the finding
and take the verdict — that is still one question at a time, and it is the one he asked
for first.

## Stay honest

- Run every instrument. **Three of the four gathers are the session-open banner's own
  lanes** — the hook and this skill call the same readers — so the banner is not wrong
  by construction, only by **clock**. That is exactly why the door re-reads them at the
  instant of firing: what it catches is not a fabrication, it is an hours-old truth
  presented as a current one.
- Cursor states, ticket counts, and dials are **records**; proofs and probescan are
  **measurements**. When you cite a record, say that it is one.
- If a gather comes back empty, that is a result — report it. An empty scan is a red
  until something says otherwise, never a silent green.

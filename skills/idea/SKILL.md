# /idea — write it down, move on

The workflow's **first step** (`press_office/WorkflowDefinition.md`, step `capture`)
and the only one whose input comes from outside the system. Somebody has an idea and
says so; this puts it at an address so it can be reached for later.

**Interpretation is deferred.** That is the design, not a shortcut. Do not analyse the
idea, do not improve it, do not decide whether it belongs — `/intent` does that, and it
is allowed to kill it there. The one job here is that the prose survives.

The charter lives beside this file in `intention+why.json`; the store's charter is
`CairnCommons/ideas/_charter+why.json`.

## Capture it verbatim

**Do not summarize.** The spec lives in Akien's head and everything written here is a
lossy translation of it — capture is the one moment where the loss is zero, and
tidying spends it. If he said it in three rambling sentences, three rambling sentences
is the record. Trim nothing but the invocation itself.

If *you* had the idea, say so in `author`. An idea authored by Akien **is** the source;
one authored by CC is already a translation, and a later reader who cannot tell them
apart cannot tell the spec from a guess at it.

## Fire the door

Write the packet to your scratchpad and fire:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/idea/door.py <scratchpad>/idea_packet.json
```

Three fields, the smallest contract in the system:

- **prose** — the idea, in the author's own words, verbatim.
- **author** — `Akien`, `CC`, or whoever had it.
- **bullets** — `{"text": ..., "stratum": "code"|"tree"}`, what was **noticed** while
  writing it down: a collision, a prior-art hit, a neighbouring ticket. Never what the
  idea *means*. **`"nothing noticed at capture"` is a legal and common bullet** — and
  reaching for it is usually right. A bullet that starts interpreting has moved
  `/intent`'s work one step earlier, to the moment it is most expensive and least
  likely to be right.

The live contract is `python3 -m cairn.machines.skill_block contract idea`. A refusal names
every lack in one pass and is itself recorded.

## What you produce

- **the record** — `CairnCommons/ideas/<YYYY-MM-DD>-<slug>.json`, printed as `idea`.
  This is the durable artifact: commons, git, survives the machine.
- **a berth** — under `~/.cairn/devices/skill_block/0/berths/idea/`. Instance-space;
  it records the firing and dies with the box.

**Carry the `id` forward, not the berth path.** When `/intent` later fires on this
idea, its `from_idea` field takes that id — the commons one — because a berth path is
meaningless on any other machine.

## Operator reviews the record

After the door fires, **present the idea record to the operator**. Read the idea
file at its printed path (`CairnCommons/ideas/<id>.json`) and show its full
content. The operator reviews the actual text — the prose as captured, the author,
the bullets — before the idea goes on.

**Wait for the operator's response.** Three outcomes:
- **Sign-off** — the idea record is accepted as written. Proceed.
- **Correction** — the operator names what to fix. Edit the record, present it
  again.
- **Rejection** — the idea should not have been captured this way. Note why in
  the bullets.

This is the review surface — the artifact itself, not a finding about it.

## Then stop

*"It's a one and done. Its end state is just when you and I move on to the next
thing."* — Akien, 2026-08-04.

There is no route back and nothing to decide. Do not offer to turn it into an
intention, do not rank it against other ideas, do not ask whether he wants to pursue
it. The queue is a queue; reaching into it is a separate, later act.

The natural next move, whenever somebody reaches for it:

- **`/intent [idea]`** — where it gets traced, challenged, and possibly killed.

## Stay honest

- CP1: if you cannot tell what was said, ask for it again rather than writing your
  best reconstruction. A confident paraphrase in the `prose` field is a translation
  wearing the source's clothes.
- Don't file to `notes/` instead. A note is a fact worth keeping; an idea is a
  candidate for work, and the queue question — *what have I not turned into work
  yet?* — cannot be asked of a mixed store. The distinction, and the case for
  collapsing the two, is recorded in `CairnCommons/ideas/_charter+why.json`.

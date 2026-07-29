---
name: commit
description: Interim checkpoint — stage, commit, and push the current work. A non-terminal marker in the fluid middle, NOT a claim of doneness. Durability-of-stones is a separate gate on the emit chokepoint, not this skill.
---

# /commit — interim checkpoint

Save a point in the work: stage, commit, push. This is a **non-terminal
checkpoint** in the fluid middle — a place you could come back to — not a
declaration that anything is finished or proved.

The charter lives beside this file in `intention+why.json`.

## What it does

1. Show what changed (`git status`, `git diff --stat`) so the commit is deliberate.
2. Stage the intended changes.
3. Commit with a clear message describing the checkpoint, ending with:

   ```
   Co-Authored-By: <the model actually writing the commit> <noreply@anthropic.com>
   ```
4. Push, if a remote is configured.

If work is on the default branch and this is durable/shared work, branch first
rather than committing straight to it.

## What it is NOT

- **Not the durability gate.** "Every stone committed + pushed" is a *gate* on the
  emit chokepoint (physics, an IOU until built) — not this skill. A skill that
  exists to *force* a behavior is policy standing in for a missing gate. This skill
  is the interim act; the gate is the guarantee. They coexist — they'd only collide
  under an exclusive-and-terminal reading, which the keystone forbids.
- **Not a proof.** Committing does not close a gate or mark a node done.

## Stay honest

- **Err toward committing.** The two errors are not symmetric: an unnecessary commit
  costs a line of history, an uncommitted one can cost the work. So checkpoint often
  and autonomously — waiting to be asked put Akien back in the operator role the
  founding intention removes him from.
- The message says what this checkpoint *is*, not "done" unless a gate actually closed.

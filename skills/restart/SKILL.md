---
name: restart
description: Restart this Claude Code session onto a new build — measure what is behind the session, write the slate through the saveslate door, then hand off. The measurement decides whether this session may end itself or whether a second one is stood up beside it.
---

# /restart — measure, save, hand off

Three steps, **in this order and no other**. The order is the whole safety of the
skill: a status read that comes after the slate is a restart that may have nothing
to come back to, and a relaunch that comes before the slate is a session that ends
with nothing written down.

The charter lives beside this file in `intention+why.json`. Ticket `15b80c0c393c`.

## 1. MEASURE — what is behind this session?

```bash
cairn cc restart status
```

Capture the stdout and hand the captured text to the selector — **the selector
decides the branch, not the reader**:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "import sys; sys.path.insert(0, '$HOME/dev/src/cairn/skills/restart'); import selector; print(selector.branch(sys.stdin.read()))"
```

It prints exactly one of two words, and there is no third:

- **`now`** — a loop is holding this session (`inner loop: HOLDING (pid N)`).
  Relaunching is safe: ending CC hands the terminal back to the loop, and the loop
  brings it straight back.
- **`spawn`** — everything else. No loop line, a loop line saying NONE, an empty
  read, a failed command. Nothing behind this session may be killed, so the hand-off
  is a second instance stood up beside it.

Do not read the status yourself and decide. The rule is asymmetric on purpose — the
verb that kills this session is returned only on a positive, structured match — and
that asymmetry is proved at `proofs/test_restart_selector.py`, not re-derived here.

## 2. SAVE — the slate, through its door

Fire **/saveslate** **as a skill**, through the Skill tool. Never shell it: its door
refuses a packet whose `instruments_read.git_heads` do not match the live repos, and
only a CC session can compile those.

**A refusal ABORTS the restart — any refusal, for any reason.** Print the refusal
verbatim, state that nothing was relaunched, and stop. Do not retry, do not fall
back to a shorter slate, and do not arm a flag. The slate and the relaunch are one
act; half of it is worse than none, because a session spent and nothing written down
is the failure the slate exists to prevent.

## 3. HAND OFF — fire the verb step 1 chose

**On `now`:**

```bash
cairn cc restart now
```

This ends the conversation. The loop brings it back with `--continue`. There is
nothing to report afterward because there is no afterward in this session.

**On `spawn`:**

```bash
cairn cc restart spawn
```

Nothing dies. Then **report** the new instance's tmux session and its remote-control
name exactly as the verb printed them, and **stop** — do not kill this session, do
not sign off, do not arm a flag afterward. The operator picks the new instance up
when they choose, and this one stays reachable until they do.

## Stay honest

The one failure this skill must never cause is a **hang-up**: a session ended with no
loop behind it and no reachable replacement already standing. Every rule above bends
toward that — the asymmetric match, the abort on a slate refusal, the spawn branch
that kills nothing. If any step is ambiguous, the answer is `spawn`.

Report a skipped step as skipped. "Restarted" is verified by the new session
existing, never by this one's narration.

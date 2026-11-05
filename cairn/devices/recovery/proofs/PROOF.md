# Proof obligation — launchers / superclaude

Law 5: proofs beside code. Hand-run until a launcher self-test exists.

## Falsifier

`superclaude` launches Claude Code with exactly the standing contract:

- session `--name <hostname>_cc_0` and `--remote-control <hostname>_cc_0`
- `--dangerously-skip-permissions` present
- context switch (command line always wins): `--1m` → `CLAUDE_CODE_DISABLE_1M_CONTEXT`
  unset; `--200k` → `=1`; neither → inherit environment, else file default, else
  unconstrained
- all other args forwarded to `claude` unchanged

## v0 check (hand-run, cheap — this is the `--dry-run` path)

```
superclaude --dry-run                 # neither flag → 200K (file default; FILE_DEFAULT_200K=1)
superclaude --200k --dry-run          # 200K (DISABLE=1)
superclaude --1m --dry-run            # 1M (DISABLE unset) — command line wins
CLAUDE_CODE_DISABLE_1M_CONTEXT=1 superclaude --1m --dry-run   # 1M — --1m unsets the env 200K
CLAUDE_CODE_DISABLE_1M_CONTEXT=1 superclaude --dry-run        # 200K — environment respected
superclaude --1m --model X --dry-run  # --model X forwarded after the standing flags
```

The `--dry-run` output IS the proof surface: it shows the resolved context state and
the exact `exec claude …` line without launching. The live proof is Akien's restart —
he launches a bare `superclaude` and confirms the session comes up 200K/named/remote/
dangerous (the "prove it along the way" step; 200K is the file default as of
2026-07-15 — ticket default-superclaude-to-200k).

**Live proof — RESULT (2026-07-15, measured):** a bare `superclaude` was relaunched
and the session awoke with a **200K** context window (confirmed via `/context`:
`50.1k/200k`). The file default won — no `--1m`, no inherited env override. This is
the falsifier the `--dry-run` cases could not reach (Law 3); it passed. Ticket
default-superclaude-to-200k → validated.

## Known omissions (v0, tracked not hidden)

- No credential loading / OpenRouter-var strip (the quarry launcher did this for a
  specific 401 incident). Cairn relies on `claude`'s own auth. If a launch hits an
  auth redirect, that's the measured signal to add a strip — not before.
- Hostname is fixed to `_cc_0` (singleton). Multi-instance slot-scan is a quarry
  feature to re-add only when a second concurrent instance is a real need.

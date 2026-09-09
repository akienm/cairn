# Proof obligation — skill:/sorted

Law 5: proofs beside code. Recorded until the enforcing mechanism exists.

## The gate (derivation gate)

A `skill`-class node reaches `done` only when **cairnmap recompiles green**.
**Status: DISCHARGED (scrubbed 2026-09-09).** cairnmap IS built — `cairn/tools/cairnmap/`,
fired as `cairnmap --gate`. This file said "cairnmap is not built yet" for weeks after it was,
and the identical stale line was found and discharged in `skills/intent/proofs/PROOF.md` on
2026-08-01 — in that one file. Eight siblings kept it, because the sweep was never run and a
hand-run obligation note has no way to notice anything. The line is worse than merely stale:
it was a standing reason not to look. Today the derivation gate is real and the honest debt is
a different one — `cairnmap --gate` exits 1 over this corpus, and 15 of its 21 findings are
false, caused by a roster field the corpus retired. That is ticket `7aed0fd0ba29`, not this
file's obligation.

## v0 behavioral check (hand-run)

- The completeness check fires all four questions (assumption / missing /
  falsifiable / collides) and a **red exits not-ready** — it does not let an
  incomplete node cast.
- Casting types the node AND binds a gate-set; a node with no falsifier does not cast.
- A cast node files to `tickets/`; filing is a consequence of resolving, not a
  separate skill (no `/ticket`).
- "Stuck" reaches an escalation, never confabulation (CP1).
- The proof-gate check-type matches the node-class (proof gate for code, quorum
  signature for concept-piece) — it does not apply the tester to a human-proved node.

## Falsifier for this skill specifically

A run of `/sorted` that casts an un-wrapped node (one that should have failed the
completeness check) is a red for this skill — the gate leaked.

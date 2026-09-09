# Proof obligation — skill:/commit

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

## The OTHER gate this skill is often confused with

The **durability-of-stones gate** — "every stone committed + pushed" — is *not*
this skill. It belongs on the emit chokepoint as physics (an IOU in CLAUDE.md's
"rules awaiting physics"). This proof records that they are distinct so the
confusion doesn't recur: the skill is the interim act, the gate is the guarantee.

## v0 behavioral check (hand-run)

- Shows the diff before committing (deliberate, not blind).
- Message ends with the Co-Authored-By line.
- Does not claim "done" — a checkpoint is not a closed gate.
- Push only when Akien has asked; branch before committing durable work to a
  default branch.

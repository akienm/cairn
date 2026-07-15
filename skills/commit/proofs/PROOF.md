# Proof obligation — skill:/commit

Law 5: proofs beside code. Recorded until the enforcing mechanism exists.

## The gate (derivation gate)

A `skill`-class node reaches `done` only when **cairnmap recompiles green**.
**Status: IOU** — cairnmap is not built yet. Debt tracked (Law 4), not a resting state.

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

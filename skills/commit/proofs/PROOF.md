# Proof obligation — skill:/commit

Law 5: proofs beside code. Recorded until the enforcing mechanism exists.

## The gate

The skill class's derivation gate retired with the tool that ran it (ticket
`d547b4859f9a`, outline 19.6): `cairn help` is the one help surface (2.4.2). This
skill's gate is its own proofs, sealed by the tester, like every code-seam.

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

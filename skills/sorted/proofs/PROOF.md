# Proof obligation — skill:/sorted

Law 5: proofs beside code. Recorded until the enforcing mechanism exists.

## The gate

The skill class's derivation gate retired with the tool that ran it (ticket
`d547b4859f9a`, outline 19.6): `cairn help` is the one help surface (2.4.2). This
skill's gate is its own proofs, sealed by the tester, like every code-seam.

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

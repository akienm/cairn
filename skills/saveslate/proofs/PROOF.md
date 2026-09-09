# Proof obligation — skill:/saveslate

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

- Writes a slate conforming to `CairnCommons/slates/_charter+why.json`.
- The slate names specifics (files/tickets/gates), marks my-read vs ratified, and
  uses absolute dates.
- Records open threads rather than collapsing them into a false "done" (Law 7).

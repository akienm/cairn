# Proof obligation — press_office (and its pieces)

Law 5: every component carries its proofs beside its code. `press_office` produces
**concept-pieces**, not code — so its proof is not a tester VALIDATION but a
**quorum signature gate**: N human reviewers read it and sign. It kicks back on
rejection exactly like a red build (CP2 — the rejection is data, routed back to
the point of creation).

## IntentionBasedDesignForHumans.md

- **falsifier** — an outside reader (not already inside Cairn) can restate the
  pattern back in their own words, and could apply it to a system of their own. If
  it only lands for someone already fluent in Cairn, it has failed its purpose.
- **method** — review by ≥1 human (Akien first; more readers widen the quorum).
  Recorded as a VALIDATION when the tester's notary role is live: `method = "review
  by N readers"`, `caller = the reviewers`, `verdict`, `evidence = their restated-
  back summary`.
- **status** — IOU. The VALIDATIONS store and the tester's notary role are not
  built yet; until then the review is hand-run and its outcome noted here. Debt
  tracked (Law 4), not a resting state.

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

## GraphTreeMemoryTechnicalBrief.md

Written 2026-08-05 for a named outside reader (an enterprise architect for AI),
which makes its quorum unusually concrete: **the reader is the gate.**

- **falsifier, the comprehension half** — the reader finishes it once and can say
  back, unprompted, how a query gets answered *without touching the model*, and
  what changes when the walk misses. The specific lived failure to watch for: he
  reads the whole thing and then asks *"so is this RAG with extra steps?"* — that
  question means §1's table did not land, and the piece failed at its first job.
- **falsifier, the honesty half — and this one is louder, because the piece goes
  outward under Akien's name.** Any claim in it that a reader later finds
  overstates what actually runs is a RED, not an erratum. The brief carries a
  "How to read this" contract promising that measurements appear with their real
  numbers and unbuilt mechanisms are named as unbuilt; a single violation voids
  the contract for the whole document. Two places carry the most risk and were
  written most carefully: §4 (per-tree tables and the shear are the *restore
  target*, not the running store) and §2.7 (the home-field finding, which is ours
  and against us).
- **method** — review by Akien first (signature gate), then the named reader. His
  restated-back summary is the evidence. A follow-up question that reveals a
  misunderstanding is data routed back here, not a conversation to have and drop.
- **status** — IOU, hand-run. Not signed.

## NoveltyDrivenGraphTreeExpansion.md

- **falsifier, the one that matters** — a reader cannot tell, from the text alone,
  which statements were **measured** and which were **designed**. The paper's whole
  standing rests on that separation (Law 3 in an outward register), and it claims
  n=1 in seven places on purpose. If a reviewer cites one of our design sections
  as a result, the labelling failed.
- **falsifier, the contribution half** — §5's mechanism (minted nodes win the
  similarity race for their own question, so a high score is not evidence) turns
  out to be already named and solved in the literature we have not yet read. That
  outcome is **not a failure of the work** — it is Law 1 arriving from outside, and
  the correct response is a citation, not a defence. It IS a failure of §2, whose
  survey rests on one secondary source and says so.
- **antiproof owed** — the paper asserts a phenomenon from n=1 plus one
  corroborating observation. §7's E2 (manufactured-resolution rate) is the
  measurement that would make it a result. Until E2 runs, this piece is an
  architecture-and-protocol paper and must not be described as anything else.
- **method** — review by Akien (signature gate), then by one reader from each of
  the three fields named in §2, in the order §5.8 of the companion brief gives:
  cognitive architecture, neuro-symbolic, dynamic graph learning. "This is new"
  and "we solved that in 2003" are both passing outcomes; silence is not.
- **status** — IOU, hand-run. Not signed. Not submitted anywhere.

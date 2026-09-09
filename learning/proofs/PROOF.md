# Proof — gate_view (learning store, rung 1)

Interim proof by inspection. SCRUBBED 2026-09-09: this said "the tester is not built";
the tester IS built — `cairn/devices/tester/`, and it seals validations beside proofs
across the corpus. The blocker named here is gone, and the charter beside this file was
corrected in the same sweep. The REAL debt is narrower and worse: `learning/proofs/`
holds only this file and no `test_*.py` at all, so there is nothing for the tester to
run. A code-seam is not *done* until tested AND committed, and this one has never been
tested — not because the instrument was missing, but because no proof was ever written. What follows is the honest interim gate: a real record
round-trips (written to `CairnCommons/learning/records/` → recalled here by gate),
and the projection's output is verifiably the fold of the records by inspection.

## Claim

`gate_view.py` is a pure, zero-inference projection: its output is exactly the
records in `CairnCommons/learning/records/` grouped by `gate`, newest-first, with the
ceiling guardrail flagged. This casts fold-the-settled (Law 1) into code.

## Measured — full view (2026-07-17)

```
$ python3 gate_view.py
gate: build-now-vs-defer  [2 records]
  2026-07-17  confirmation  The gate is learning to open: the settled lesson caught the novel instance without re-derivation (Law 1).
  2026-07-16  correction    This record exists because of this datum — building the store today instead of deferring it is the amendment in action.

gate: cast-founding-intention-solo  [1 record]  ⚠ never-auto-opens (ceiling)
  2026-07-16  correction    CC wrote the shadow of the intention, not the intention. The challenge found the parent.

gate: ci-on-github  [1 record]
  2026-07-16  correction    GitHub is hosting/durability only; running stays on Akien's machines.

gate: naming-scope  [1 record]
  2026-07-16  correction    Different mind-types accumulate different wisdom; a global store would blur them.

gate: repo-visibility  [1 record]  ⚠ never-auto-opens (ceiling)
  2026-07-16  confirmation  Asking before publishing to the world was the correct move, confirmed by Akien engaging it as a real choice.

gate: system-memory-architecture  [1 record]  ⚠ never-auto-opens (ceiling)
  2026-07-17  confirmation  Open: whether horizon-of-awareness warrants its own concept-piece ... Not cast solo — raised to Akien.
```

## Measured — sparse recall, one gate

```
$ python3 gate_view.py build-now-vs-defer
gate: build-now-vs-defer  [2 records]
  2026-07-17  confirmation  The gate is learning to open: the settled lesson caught the novel instance without re-derivation (Law 1).
  2026-07-16  correction    This record exists because of this datum — building the store today instead of deferring it is the amendment in action.
```

## Verdict — PASS (interim, by inspection)

- **Fold is faithful.** 7 records across 2 files (`2026-07-16-session.json` ×5,
  `2026-07-17-session.json` ×2) → 6 gates. Every record appears under its gate;
  `build-now-vs-defer` correctly shows both instances — the settled lesson (07-16)
  and its recurrence (07-17). This *is* the round-trip: 07-16-04 was captured, then
  recalled at a like decision today, producing 07-17-01.
- **Sparse recall works.** The gate filter surfaces one gate's evidence — recall
  spends context on the relevant gate, not the corpus (horizon-of-awareness in code).
- **Ceiling flagged** on the three ceiling gates.

## Found by this proof — the next rung (now closed)

Rung 1's proof caught its own gap: `ci-on-github` is a never-auto-open gate (Actions
disabled by physics) but was NOT flagged, because its record said "close hard," not
"ceiling" — the prose heuristic missed it.

## Rung 3 — ceiling as a structured field (2026-07-17)

Records gained a `ceiling: true/false` field; `has_ceiling` now reads it instead of
matching prose. Re-run — `ci-on-github` now flags correctly:

```
$ python3 gate_view.py
...
gate: ci-on-github  [1 record]  ⚠ never-auto-opens (ceiling)
  2026-07-16  correction    GitHub is hosting/durability only; running stays on Akien's machines.
...
gate: proceed-on-light-ack  [1 record]
  2026-07-17  weak          Dogfood: CC deciding a low-ceiling gate on its own ...
```

**PASS (interim).** The guardrail is now physics: a gate is ceilinged iff a record
asserts `ceiling: true`, ORed across the gate's records (one never-auto-open sticks).
The fold can no longer miss a ceiling to a wording choice. (Still by inspection: no `test_*.py` exists here — see the scrub note above.)

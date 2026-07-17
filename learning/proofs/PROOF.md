# Proof — gate_view (learning store, rung 1)

Interim proof by inspection. The tester is not built (IOU, tracked on
`cc-learning-store` + CLAUDE.md rules-awaiting-physics); a code-seam is not *done*
until tested AND committed. What follows is the honest interim gate: a real record
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

## Found by this proof — the next rung

`ci-on-github` is a never-auto-open gate (Actions disabled by physics) but is NOT
flagged, because its record says "close hard," not "ceiling." The prose heuristic
missed it. This is exactly why **rung 3 makes the ceiling a structured field** — a
never-auto-open guardrail must be physics, not a substring match (Law 4). The proof
surfaced its own successor.

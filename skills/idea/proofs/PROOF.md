# Proof obligation — skill:/idea

Law 5: proofs beside code.

## The gate (derivation gate)

A `skill`-class node reaches `done` only when **cairnmap recompiles green**.
**Status: IOU** — cairnmap is not built yet. Debt tracked (Law 4), not a resting state.

## The mechanical proof

`test_idea_door.py` — 26 teeth, every root injected. Run:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/idea/proofs/test_idea_door.py
```

The tooth that carries the step's whole why is **VERBATIM**: the prose is stored
byte-identical, leading whitespace, newlines and all. A door that normalised or trimmed
would pass every other check while defeating the step — capture is the one moment where
translation loss is zero, and tidying spends it.

The tooth that earned its keep on the first run is **live trace untouched**. It caught
the proof's own CLI subprocess writing a `send_back` into the live trace for
`skill:idea` — which would have made a fixture indistinguishable from a real refused
capture in the very denominator `bin/cmd/skilldial` reads.

## Falsifier for this skill specifically

- A capture whose stored `prose` is not byte-identical to what was said.
- A capture that succeeds with no record in `CairnCommons/ideas/` — the berth is the
  receipt, the record is the work.
- An `/idea` firing that asks a question. The gate is "captured text that can be
  interpreted later"; every additional question is friction on the one step that
  cannot afford any, and a capture door people stop using loses ideas exactly as
  reliably as no door at all.

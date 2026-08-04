# Proof obligation — skill:/design

Law 5: proofs beside code.

## The gate (derivation gate)

A `skill`-class node reaches `done` only when **cairnmap recompiles green**.
**Status: IOU** — cairnmap is not built yet. Debt tracked (Law 4), not a resting state.

## The mechanical proof

`test_design_door.py` — 30 teeth, every root injected. Run:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/design/proofs/test_design_door.py
```

The sharpest tooth is **the corpse**: a berth that exists, reads cleanly, and came from
the right door, but exited `routed_out`. A naive implementation passes it — it is
present and well-formed. Designing on it spends the resolver on a node the cheapest
gate in the system already turned away, which is the waste Law 1 names.

The second is **countable**: a return trip from `/sorted` must be distinguishable from
a first pass. That is the only signal we have about which of `/intent`'s questions are
letting things through, and prose in the field would erase it.

## Falsifier for this skill specifically

- A design session that opens on a berth nobody can find, or on one that was killed.
- A second pass recorded as `entering_from: intent`. That is not a small inaccuracy —
  it is the measurement inverting, and it makes a door that is leaking look like a
  door that is working.
- An `exit` field appearing on this door. The step's exits are `/sorted`'s to record;
  two components recording one outcome is how they come to disagree about it.

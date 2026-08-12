# Proof obligation — skill:/whatslefttodo

Law 5: proofs beside code.

## The gate (derivation gate)

A `skill`-class node reaches `done` only when **cairnmap recompiles green**.
**Status: IOU** — cairnmap is not built yet. Debt tracked (Law 4), not a resting state.

## The mechanical proof

`test_whatslefttodo.py` — 33 teeth, every root injected. Run:

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 skills/whatslefttodo/proofs/test_whatslefttodo.py
```

Until 2026-08-12 the `proof` field of this charter read **"NONE — and this is a real
gap, not a class exemption"**, and the `gates` field read **"NONE, and that is the
design."** Both were true. What made the gap real rather than tolerable is that the
charter also named the debt in two halves — *"nothing detects a /whatslefttodo that
skipped a gather **or reported a stale count**"* — and only one of those halves is
reachable by a contract that checks fields are present.

**The teeth that carry the whole why are the STALE ones.** A door that only checked
presence would go green having closed half a debt, which is the exact shape of a tooth
that passes because of the defect. So the judge re-reads the world at the instant of
firing and the proof pins the relation: reported ≠ measured ⇒ refused, with **both**
values named so the fix is one edit.

**The tooth that pins the honesty of the whole file is `an instrument the judge cannot
reach is a REFUSAL, not a quiet pass`.** A judge that goes silent when its reader is
unreachable would report a green world it never looked at — the vacuous gate the seam
exists to stop (Law 8).

**Not one tooth asserts a snapshot.** The gate held 104 findings the day this was
written; a tooth pinned to 104 would go red at the moment its condition was satisfied,
which is a failure this corpus has now met three times. Every refusal tooth injects the
measurement; the live-world teeth assert only shape (`int`, sorted list of ids, a slate
stem that is not `_`-prefixed). The **pass/refuse pair at the end** is what keeps the
pass from being tautological: one packet built from the live readers fires clean, and
the same packet with a single figure moved refuses — so a door that never returned a
lack could not pass both.

## Falsifier for this skill specifically

- A firing that passes carrying a figure the instrument would not produce right now.
  That is the stale half of the debt, and it is what the door exists for.
- A firing that passes with a gather whose `ran` does not name its instrument.
- A judge that returns `[]` because a reader threw. Silence is the failure mode here,
  not the wrong answer.
- **`probescan` and `test -q` are not re-run**, by decision: the proof corpus costs
  minutes and a minutes-long judge is one the operator learns to route around. Their
  figures ride the packet operator-reported and are checked for presence only. That is
  a **named residue**, and a firing that fabricates them is not detected. If it ever
  matters, the fix is a cached last-run stamp those two commands leave behind — not a
  judge that shells out.
- Nothing detects an **overview offered as a menu instead of a recommendation**, which
  the charter's falsifier reds on. That needs a reader that judges meaning; it is prose
  in `SKILL.md` today.

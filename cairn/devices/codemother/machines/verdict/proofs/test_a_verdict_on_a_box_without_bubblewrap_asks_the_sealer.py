"""Proof for ticket 86cccb7d30f7 — a verdict on a box without bubblewrap asks the sealer.

Measured 2026-11-19 on akiendell (Windows): `sail.py verdict 35bb99574043` and `... 1eeeab70c59e`
were refused because the gate's instrument run exited 2 with
`cairn test --exec: refused — the instance seal is not confirmed (indeterminate: cannot build the
instance seal: bubblewrap (bwrap) is not installed); the command was not run`. Outline 9.4.8.1:
the instrument's run is seal-grade and runs where the sealer runs; a box without bubblewrap ASKS
for it and does not run it itself. Today the refusal is recorded (`seal_refused`) and nothing
asks anyone.

RED-FIRST, AND RED ON LINUX TOO. No bwrap is needed: the instrument runner is a stub that answers
the refusal line, and the sealer is a stub the proof hands to the gate through the keyword
``sealer`` of ``observe_instruments`` (a callable ``sealer(command) -> run record``; a record
carrying ``"pending": True`` means the ask went out and no outcome is back; a raise means no
sealer is reachable). The build may rename the seam, and must then rename it here. Until the seam
exists every tooth fails on the unknown keyword.

1. a refused run sends one ask for that command to the sealer, and the reading names the sealer;
2. the sealer's outcome becomes the verdict's outcome: its exit 0 agrees a pass, its exit 1
   contradicts one and refuses;
3. an ask with no outcome yet reads not-run, never red, and the box's own refused run is never
   recorded as a pass;
4. with no sealer reachable the gate still refuses, loud, naming the seal line, and writes no pass.

    bin/cairn test cairn/devices/codemother/machines/verdict/proofs/test_a_verdict_on_a_box_without_bubblewrap_asks_the_sealer.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"86cccb7d30f7": {
    "1": "test_a_refused_run_asks_the_sealer_and_names_it",
    "2": "test_the_sealers_outcome_becomes_the_verdicts",
    "3": "test_an_unanswered_ask_reads_not_run_never_red",
    "4": "test_no_sealer_reachable_still_refuses_loudly"}}

REFUSAL = ("cairn test --exec: refused — the instance seal is not confirmed (indeterminate: cannot "
           "build the instance seal: bubblewrap (bwrap) is not installed); the command was not run")
PLENTY = 64 * 1024 ** 3


def _v():
    from cairn.devices.codemother.machines.verdict import verdict
    return verdict


def _artifact(outcome="pass"):
    return {"verdicts": [{"claim": "a windows clause", "instrument": "`true 1`", "outcome": outcome}]}


def _refused_runner(command, **kw):
    """What run_instrument returns on a box with no bwrap, with no fork and no bwrap needed."""
    return {"command": command, "exit": 2, "timed_out": False, "timeout_s": 1, "seconds": 0.0,
            "tail": REFUSAL, "seal_refused": REFUSAL}


class _Sealer:
    name = "akiendelllinux_cc_0"

    def __init__(self, answer=None, raises=None):
        self.asked, self.answer, self.raises = [], answer, raises

    def __call__(self, command, **kw):
        self.asked.append(command)
        if self.raises:
            raise self.raises
        return dict(self.answer or {})


def _observe(artifact, sealer):
    try:
        return _v().observe_instruments(artifact, runner=_refused_runner, sealer=sealer,
                                        mem_available=lambda: PLENTY)
    except TypeError as exc:
        raise AssertionError("the gate has no seam to ask a sealer (%s)" % exc)


def _lacks(artifact, readings):
    return [e for e in _v().inspect_verdict(artifact, observations=readings)
            if isinstance(e, dict) and e.get("lack")]


def test_a_refused_run_asks_the_sealer_and_names_it():
    sealer = _Sealer({"command": "true 1", "exit": 0, "timed_out": False, "timeout_s": 1,
                      "seconds": 0.1, "tail": ""})
    readings = _observe(_artifact(), sealer)
    assert sealer.asked == ["true 1"], "one ask for the refused command goes to the sealer: %r" % sealer.asked
    assert _Sealer.name in repr(readings), "the reply names the sealer that was asked: %r" % readings


def test_the_sealers_outcome_becomes_the_verdicts():
    green = _observe(_artifact("pass"), _Sealer({"command": "true 1", "exit": 0, "timed_out": False,
                                                 "timeout_s": 1, "seconds": 0.1, "tail": ""}))
    assert _v().judged_run(green[0]).get("exit") == 0, \
        "the verdict is judged by the sealer's exit 0, not the box's refused exit 2: %r" % green
    red = _observe(_artifact("pass"), _Sealer({"command": "true 1", "exit": 1, "timed_out": False,
                                               "timeout_s": 1, "seconds": 0.1, "tail": "boom"}))
    assert _v().judged_run(red[0]).get("exit") == 1 and _lacks(_artifact("pass"), red), \
        "a sealer's exit 1 contradicts a reported pass and the gate refuses it: %r" % red


def test_an_unanswered_ask_reads_not_run_never_red():
    readings = _observe(_artifact("pass"), _Sealer({"pending": True}))
    assert readings[0].get("state") == "not-run", "an ask with no outcome reads not-run: %r" % readings
    assert not any("re-run disagrees" in str(e.get("lack")) for e in _lacks(_artifact("pass"), readings)), \
        "not-run is never recorded as a red disagreement"
    assert not any(r.get("exit") == 0 for r in (readings[0].get("run"), readings[0].get("run_alone"))
                   if r), "the box's own refused run is never recorded as a pass"


def test_no_sealer_reachable_still_refuses_loudly():
    readings = _observe(_artifact("pass"), _Sealer(raises=ConnectionError("no sealer reachable")))
    lacks = _lacks(_artifact("pass"), readings)
    assert lacks, "with no sealer the gate refuses, it does not pass"
    assert any("bubblewrap" in str(e.get("lack")) or "instance seal is not confirmed" in str(e.get("lack"))
               for e in lacks), "the refusal names the seal line: %r" % lacks


def _main() -> int:
    checks = [test_a_refused_run_asks_the_sealer_and_names_it,
              test_the_sealers_outcome_becomes_the_verdicts,
              test_an_unanswered_ask_reads_not_run_never_red,
              test_no_sealer_reachable_still_refuses_loudly]
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as exc:
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {exc}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed: {failed}")
        return 1
    print("green — a box without bubblewrap asks the sealer and judges by its outcome.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

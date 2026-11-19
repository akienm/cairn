"""Proof for ticket 60ca4c6a9b50: a close names the crossing the gate answered.

Measured 2026-11-19 on 79aa8b19a840: close.sh committed '79aa8b19a840: PROVED refused at clearance' three
times (commons f51888e9, 105278a2, c7000c0c). The clearance replies said accepted BUILDME, accepted
PROVEME and refused BUILDME. close.sh wrote that one fixed subject for every outcome short of PROVED,
including an accepted crossing.

1. sail.py cross, given a refusing clearance reply with target BUILDME, returns 1 and names 'at BUILDME'
   and the reason;
2. close.sh's not-PROVED block, run as written with RC 0 and a cursor at [PROVEME], commits
   'PROVEME crossed at clearance, not yet PROVED', never 'refused', and exits 4;
3. the same block with RC 1 commits '<T> refused at clearance' for the target sail.py named
   (BUILDME, PROVED), and 'the crossing refused at clearance' when none is named; each exits 1;
4. with RC 0 and '-> [PROVED]' the block commits nothing and falls through.

Tooth 1 runs in the scratch world of test_sail_queues_the_ticket_at_codemothers_gates.py (borrowed by
path at call time). Teeth 2-4 take close.sh's block from 'if [ $RC -ne 0 ] ||' through the first
column-0 'fi' and run it with bash, commit_all stubbed to print its subject.

    python3 cairn/devices/cc/proofs/test_a_close_names_the_crossing_the_gate_answered.py   # exit 0 = green
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "60ca4c6a9b50": {
        "1": "test_a_refusal_names_the_target_it_was_refused_at",
        "2": "test_an_accepted_crossing_short_of_proved_is_named_crossed",
        "3": "test_a_refusal_is_named_for_its_target",
        "4": "test_a_proved_crossing_falls_through",
    },
}

_HERE = Path(__file__).resolve().parent
_CLOSE = _REPO_ROOT / "cairn" / "devices" / "cc" / "scripts" / "close.sh"
_ID = "60ca4c6a9b50"
_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931: a bare bash is the WSL launcher on Windows


def _harness():
    spec = importlib.util.spec_from_file_location(
        "cc_sail_gates_harness_60ca", _HERE / "test_sail_queues_the_ticket_at_codemothers_gates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _block() -> str:
    lines = _CLOSE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("if [ $RC -ne 0 ] ||"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "fi")
    return "\n".join(lines[start:end + 1])


def _run(rc: int, out: str) -> tuple[list[str], bool, int]:
    """Run close.sh's not-PROVED block as written: (subjects committed, fell through, exit code)."""
    script = ('commit_all() { echo "SUBJECT:$1"; }\n'
              f'ID={_ID}\nRC={rc}\nOUT="$1"\n' + _block() + "\necho FELL_THROUGH\n")
    p = subprocess.run([_BASH, "-c", script, "block", out], capture_output=True, text=True, timeout=30)
    subjects = [ln[len("SUBJECT:"):] for ln in p.stdout.splitlines() if ln.startswith("SUBJECT:")]
    return subjects, "FELL_THROUGH" in p.stdout, p.returncode


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


def test_a_refusal_names_the_target_it_was_refused_at():
    h = _harness()
    sail = h._sail()
    with h._world("PROVEME") as w:
        bus = h._Bus([{"body": {"accepted": False, "target": "BUILDME",
                                "reason": "fixme_gate refused: 1 of 1 checks did not match"}}])
        said, out = h._quiet()
        rc = sail.cross(h._TID, participant=sail.Asker(bus), tickets_dir=w["store"], out=out, err=out)
        assert rc == 1, f"rc={rc}: {said}"
        assert any(f"refused {h._TID} at BUILDME" in s and "fixme_gate refused" in s for s in said), said


def test_an_accepted_crossing_short_of_proved_is_named_crossed():
    subjects, fell, code = _run(0, _wf("PROVEME"))
    assert subjects == ["PROVEME crossed at clearance, not yet PROVED"], subjects
    assert not any("refused" in s for s in subjects), subjects
    assert code == 4 and not fell, (code, fell)


def test_a_refusal_is_named_for_its_target():
    for out, want in ((f"clearance refused {_ID} at BUILDME: fixme_gate refused", "BUILDME refused at clearance"),
                      (f"clearance refused {_ID} at PROVED: ExitGateRed: no verdict", "PROVED refused at clearance"),
                      (f"clearance refused {_ID} at its next phase: no reply", "the crossing refused at clearance")):
        subjects, fell, code = _run(1, out)
        assert subjects == [want], (out, subjects)
        assert code == 1 and not fell, (out, code, fell)


def test_a_proved_crossing_falls_through():
    subjects, fell, code = _run(0, _wf("PROVED"))
    assert subjects == [], subjects
    assert fell and code == 0, (fell, code)


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)

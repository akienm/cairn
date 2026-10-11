"""Proof: clearance reads a plan approval on re-read of the plan (ticket bf1cd5d79805).

F50 (Akien, 2026-10-09): "the plan based tickets are inherently preapproved." The tester now
seals a proofs-only build whose ticket plan names every skipped file as ``{"approved": "plan"}``
(its own proof: test_the_tester_records_an_approved_proofs_only_build.py). Until this build the
rung re-read every ``approved`` value as a question id, so "plan" re-read as no question and
redded hollow_approval_unresolved on every such build.

ACCEPTS IT ONLY ON RE-READ, as a question approval is. The tester's word is not trusted at the
gate: "plan" counts for a file only when the crossing ticket's own ``writes_to`` list names that
file. Anything else is ``hollow_approval_unresolved``, never folded into unreadable.

Three teeth, matching the falsifier:
  1. a file sealed {"approved": "plan"} that the ticket's writes_to names yields NO lack.
  2. a file sealed {"approved": "plan"} the plan does not name (absent from writes_to, named
     only in prose, or no writes_to at all) yields exactly ``hollow_approval_unresolved``
     naming that file.
  3. the standing clearance proofs (the question approval among them) stay green.

The fake ``seal_reader`` hands hollow_lacks the reading directly, so this measures the rung and
nothing else (RULE 1). ``hollow_lacks`` is resolved at call time so reverting clearance.py reds a
tooth instead of breaking the import.
    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_clearance_reads_a_plan_approval.py
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROOF_TIMEOUT_S = 1800  # tooth 3 runs the standing clearance proofs in subprocesses

PROVES = {
    "bf1cd5d79805": {
        "1": "test_a_plan_approval_the_plan_names_is_covered",
        "2": "test_a_plan_approval_the_plan_does_not_name_is_unresolved",
        "3": "test_the_standing_clearance_proofs_stay_green",
    },
}

_TID = "bf1cd5d79805"
_PROOF = "cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py"


def _lacks(reading, ticket_extra: dict) -> list[dict]:
    clearance = importlib.import_module("cairn.devices.cairn.machines.harbor_master.clearance")

    def seal_reader(path, artifact=False):
        return {"evidence": {"hollow": {_TID: reading}}}

    ticket = {"id": _TID, "node_class": "code-seam", **ticket_extra}
    return clearance.hollow_lacks(ticket, [_PROOF], repo_root=_REPO_ROOT,
                                  seal_reader=seal_reader, question_root=scratch_dir("cairn-planq-"))


def _kinds(lacks) -> list[str]:
    return sorted(l["kind"] for l in lacks)


def test_a_plan_approval_the_plan_names_is_covered():
    reading = {"a.py": ["test_x"], "p.py": {"approved": "plan"}, "q.py": {"approved": "plan"}}
    got = _lacks(reading, {"writes_to": ["a.py", "p.py", "q.py"]})
    assert got == [], f"a plan approval the plan names must yield [], got {_kinds(got)}"


def test_a_plan_approval_the_plan_does_not_name_is_unresolved():
    cases = {
        "absent from writes_to": {"writes_to": ["a.py", "q.py"]},
        "named only in prose": {"how": "write p.py", "writes_to": ["a.py", "q.py"]},
        "no writes_to at all": {},
        "writes_to not a list": {"writes_to": "p.py"},
    }
    for label, extra in cases.items():
        got = _lacks({"a.py": ["test_x"], "p.py": {"approved": "plan"},
                      "q.py": {"approved": "plan"}}, extra)
        assert _kinds(got) == ["hollow_approval_unresolved"], (label, _kinds(got))
        want = ["p.py"] if isinstance(extra.get("writes_to"), list) else ["p.py", "q.py"]
        assert got[0]["values"].get("files") == want, (label, got[0])


def test_the_standing_clearance_proofs_stay_green():
    for rel in (_PROOF,
                "cairn/devices/cairn/machines/harbor_master/proofs/test_clearance_accepts_a_recorded_approval.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], capture_output=True,
                           text=True, timeout=1500, cwd=_REPO_ROOT)
        assert r.returncode == 0, (rel, r.stdout[-1500:], r.stderr[-1500:])


def main() -> int:
    failed = 0
    for name in PROVES[_TID].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("GREEN" if not failed else f"RED ({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof: clearance accepts a recorded approval only on re-read (ticket ec4ca415f43d).

MEASURED 2026-10-06 on 45c168cc1ff1: its build wrote only its two proofs, so its hollow sealed
``{}`` and this rung refuses hollow_nothing_measured — with no repair of the code able to give
it anything to revert. Ruling 8p (Akien, 2026-10-06): his approval of that proof change IS the
measurement (Law 10); the tester records it on the reading as ``{"approved": <qid>}`` (sibling
child f5bba1daa72a) and this rung accepts it.

ACCEPTS IT ONLY ON RE-READ. The tester's word that a question approved the change is not
trusted at the gate: the qid is read back through the question tool's public ``read`` and
counts only when it resolves, is resolved, is bound to THIS ticket, and was answered by Akien.
Anything else is its own lack, ``hollow_approval_unresolved`` — never folded into unreadable.

Four teeth, matching the falsifier:
  1. an Akien-resolved question bound to the ticket, beside a covered file, yields NO lack.
  2. answered by cc, still open, bound to another ticket, or nonexistent each yield exactly
     ``hollow_approval_unresolved``.
  3. an empty reading is still ``hollow_nothing_measured``.
  4. the standing clearance proofs stay green.

The question store is a scratch directory handed in as ``question_root``; the fake
``seal_reader`` hands hollow_lacks the reading directly, so this measures the rung and nothing
else (RULE 1). ``hollow_lacks`` is resolved at call time so reverting clearance.py reds a tooth
instead of breaking the import.
    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_clearance_accepts_a_recorded_approval.py
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROOF_TIMEOUT_S = 1800  # tooth 4 runs test_clearance.py in a subprocess

PROVES = {
    "ec4ca415f43d": {
        "1": "test_an_akien_approval_bound_to_the_ticket_is_covered",
        "2": "test_any_other_approval_is_unresolved",
        "3": "test_an_empty_reading_still_measured_nothing",
        "4": "test_the_standing_clearance_proofs_stay_green",
    },
}

_TID = "ec4ca415f43d"
_PROOF = "cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py"
_AKIEN = "Akien, recorded by caller class cc"


def _store() -> Path:
    return scratch_dir("cairn-approvalq-")


def _question(root: Path, qid: str, *, ticket: str = _TID, resolved: bool = True,
              answered_by: str | None = _AKIEN) -> str:
    record = {
        "id": qid, "date": "2026-10-06", "ticket": ticket,
        "question": "May the proof change cross PROVED on your approval?",
        "why_it_blocks": "fixture", "raised_by": "tester", "born_of": None, "source": None,
        "resolved": resolved, "answer": "yes" if resolved else None,
        "answered_by": answered_by if resolved else None,
        "answered_at": "2026-10-06T09:00:00" if resolved else None,
        "spawned": [] if resolved else None,
    }
    (root / f"{qid}.json").write_text(json.dumps(record), encoding="utf-8")
    return qid


def _lacks(reading, **kw) -> list[dict]:
    clearance = importlib.import_module("cairn.devices.cairn.machines.harbor_master.clearance")

    def seal_reader(path, artifact=False):
        return {"evidence": {"hollow": {_TID: reading}}}

    ticket = {"id": _TID, "node_class": "code-seam"}
    return clearance.hollow_lacks(ticket, [_PROOF], repo_root=_REPO_ROOT,
                                  seal_reader=seal_reader, **kw)


def _kinds(lacks) -> list[str]:
    return sorted(l["kind"] for l in lacks)


def test_an_akien_approval_bound_to_the_ticket_is_covered():
    root = _store()
    qid = _question(root, "open-a99r0e000001")
    reading = {"a.py": ["test_x"], "p.py": {"approved": qid}, "q.py": {"approved": qid}}
    got = _lacks(reading, question_root=root)
    assert got == [], f"an Akien-resolved approval bound to {_TID} must yield [], got {_kinds(got)}"


def test_any_other_approval_is_unresolved():
    root = _store()
    cases = {
        "answered by cc": _question(root, "open-a99r0e000101", answered_by="cc"),
        "measured, not his": _question(
            root, "open-a99r0e000102",
            answered_by="measurement: /tmp/x.json, recorded by caller class cc"),
        "still open": _question(root, "open-a99r0e000103", resolved=False),
        "bound to another ticket": _question(root, "open-a99r0e000104", ticket="0ther71cket00"),
        "nonexistent": "open-a99r0e0001ff",
    }
    for label, qid in cases.items():
        got = _lacks({"a.py": ["test_x"], "p.py": {"approved": qid}}, question_root=root)
        assert _kinds(got) == ["hollow_approval_unresolved"], (label, _kinds(got))
        assert got[0]["values"].get("files") == ["p.py"], (label, got[0])


def test_an_empty_reading_still_measured_nothing():
    got = _kinds(_lacks({}))
    assert got == ["hollow_nothing_measured"], got


def test_the_standing_clearance_proofs_stay_green():
    for rel in (_PROOF,
                "cairn/devices/cairn/machines/harbor_master/proofs/test_a_notified_file_is_covered.py"):
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

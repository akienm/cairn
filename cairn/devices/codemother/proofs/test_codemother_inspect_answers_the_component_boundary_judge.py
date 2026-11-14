"""Proof (ticket 31f431873401): codemother's ``inspect`` answers the component-boundary judge by name.

The BUILDME lane (ticket 67d479860f5d) asks ``buildme_stays_in_its_component`` (ticket 8d14f4aa9e72,
cairn/machines/build_inspector) through codemother's ``inspect`` verb, and ``inspect`` refuses any name
off ``INSPECT_JUDGES`` before anything runs (shim.py). The list lives in codemother and the judge in
build_inspector, so RULE 1 puts the one line in its own ticket.

The shim's ``inspect`` handler is driven directly (``CodeMotherDevice()._handle_inspect``), the same
handler the bus reaches, with the arguments in their wire form, so the proof needs no bus and the
judge runs in the process that asked (no patch in the asker the judge cannot see).

  1. ``inspect`` for buildme_stays_in_its_component over a scratch ticket that writes outside its
     owner answers accepted, with the judge's own findings (one foreign finding), not a refusal
     naming an unlisted judge; and what it answers equals the direct call.
  2. a name not on INSPECT_JUDGES (a real inspector function, ``_charter_dirs``) is still refused by
     name and nothing runs (a spy on it is never called).

    python3 cairn/devices/codemother/proofs/test_codemother_inspect_answers_the_component_boundary_judge.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"31f431873401": {
    "1": "test_inspect_answers_the_component_boundary_judge_by_name",
    "2": "test_a_judge_off_the_list_is_still_refused_by_name_and_nothing_runs",
}}

TID = "c0b0a1d2e3f4"
JUDGE = "buildme_stays_in_its_component"
CHARTERS = ("cairn/tools/base/intention+why.json", "cairn/machines/build_inspector/intention+why.json")


def _world():
    """A scratch tree whose tracked files are two charters, and a scratch commons beside it holding one
    ticket owned by cairn/tools/base that writes into cairn/machines/build_inspector."""
    from cairn.tools.scratch.scratch import git_env, scratch_dir
    d = scratch_dir("inspect_31f4_")
    commons, tree = d / "CairnCommons", d / "cairn"
    (commons / "tickets").mkdir(parents=True)
    tree.mkdir()
    env = git_env()
    subprocess.run(["git", "init", "-q", str(tree)], check=True, env=env)
    for c in CHARTERS:
        (tree / c).parent.mkdir(parents=True, exist_ok=True)
        (tree / c).write_text("{}\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "-C", str(tree), "add", "--", *CHARTERS], check=True, env=env)
    writes = ["cairn/tools/base/transitions.py", "cairn/machines/build_inspector/inspector.py"]
    (commons / "tickets" / f"{TID}-x.json").write_text(json.dumps(
        {"ticket": TID, "owning_intention": CHARTERS[0],
         "decisions": [{"n": 1, "text": "D1", "writes_to": writes}],
         "bounds": {"in": writes, "out": []}}, indent=2) + "\n", encoding="utf-8", newline="\n")
    return tree


def _inspect(judge: str, *args, **kwargs) -> dict:
    from cairn.devices.codemother.shim import CodeMotherDevice
    from cairn.tools.inspect_wire.inspect_wire import wire_encode
    return CodeMotherDevice()._handle_inspect({"body": {"judge": judge, "args": wire_encode(list(args)),
                                                      "kwargs": wire_encode(kwargs)}})


def test_inspect_answers_the_component_boundary_judge_by_name():
    from cairn.devices.codemother.shim import INSPECT_JUDGES
    from cairn.machines.build_inspector import inspector
    from cairn.tools.inspect_wire.inspect_wire import wire_decode
    assert JUDGE in INSPECT_JUDGES, f"codemother's INSPECT_JUDGES does not list {JUDGE}"
    tree = _world()
    reply = _inspect(JUDGE, TID, tickets_root=tree)
    assert reply.get("accepted") is True, f"inspect refused the judge: {reply.get('reason')}"
    answered = wire_decode(reply["data"])
    direct = getattr(inspector, JUDGE)(TID, tickets_root=tree)
    assert answered == direct, (answered, direct)
    kinds = [(f.get("values") or {}).get("kind") for f in answered]
    assert kinds == ["foreign"], f"the judge's answer through inspect is not one foreign finding: {answered}"


def test_a_judge_off_the_list_is_still_refused_by_name_and_nothing_runs():
    from unittest import mock
    from cairn.machines.build_inspector import inspector
    with mock.patch.object(inspector, "_charter_dirs", side_effect=AssertionError("a judge off the list ran")) as spy:
        reply = _inspect("_charter_dirs", _world())
    assert reply.get("accepted") is False and "_charter_dirs" in (reply.get("reason") or ""), reply
    assert spy.call_count == 0, "the refused name ran"


TEETH = [test_inspect_answers_the_component_boundary_judge_by_name,
         test_a_judge_off_the_list_is_still_refused_by_name_and_nothing_runs]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

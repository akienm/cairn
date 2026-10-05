"""The inference sole-path rule admits the bus client's local socket, and nothing else (ticket f5a344e6c629).

Akien, answering CairnCommons/questions/open-10941757e6b7.json on 2026-10-04: the point of the
rule is that nobody goes around an established device; controlling socket imports was only the
mechanism, "I'll go with your yes". cairn/tools/bus_client/remote.py imports socket to speak the
local AF_UNIX bus socket (<home>/bus.sock), never the inference host, so it is admitted by name.
The admission is ONE file: another bus_client module that grows a dialer is still a second door.

This proof measures inference_domain's own seat — the rule as test_host.py states it — over the
real repo and over a planted graph, and that the charter's falsifier (6) states the admission.
Teeth import inside their bodies, so a reverted seat reds a tooth instead of breaking the file.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f5a344e6c629": {
    "1": "test_the_real_repo_has_one_door",
    "2": "test_a_planted_dialer_is_still_caught",
    "3": "test_the_charter_names_the_answer",
}}

_HERE = Path(__file__).resolve().parent
_COMPONENT = _HERE.parent
_QUESTION = _REPO_ROOT.parent / "CairnCommons" / "questions" / "open-10941757e6b7.json"


def _rule() -> dict:
    """test_host.py's _SOLE_PATH, loaded from its file so this proof reads the seat, never a copy."""
    spec = importlib.util.spec_from_file_location("_sole_path_host_seat", _HERE / "test_host.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._SOLE_PATH


def test_the_real_repo_has_one_door():
    from cairn.tools.import_sieve import sieve
    caught = sieve.catches(sieve.import_graph(str(_REPO_ROOT)), _rule())
    assert caught == [], caught


def test_a_planted_dialer_is_still_caught():
    from cairn.tools.import_sieve import sieve
    planted = {f"filler/m{i}.py": {"json"} for i in range(25)}
    planted["cairn/tools/bus_client/remote.py"] = sieve.imports_in("import socket")
    planted["cairn/tools/bus_client/bus_client.py"] = sieve.imports_in("import socket")
    planted["skills/rogue/probe.py"] = sieve.imports_in("import socket")
    planted["cairn/devices/inference_domain/host.py"] = sieve.imports_in("import urllib.request")
    caught = sieve.catches(planted, _rule())
    where = sorted(c.split(" imports ", 1)[0] for c in caught)
    assert where == ["cairn/tools/bus_client/bus_client.py", "skills/rogue/probe.py"], caught
    assert all("cairn/devices/inference_domain/" in c for c in caught), caught


def test_the_charter_names_the_answer():
    charter = json.loads((_COMPONENT / "intention+why.json").read_text())
    falsifier = str(charter.get("falsifier") or "")
    clause6 = falsifier[falsifier.find("(6)"):falsifier.find("(7)")]
    assert "open-10941757e6b7" in clause6, clause6[:300]
    assert "cairn/tools/bus_client/remote.py" in clause6, clause6[:300]
    question = json.loads(_QUESTION.read_text())
    assert question.get("resolved") is True and question.get("answer"), question.get("resolved")


def main() -> int:
    fails = 0
    for name in PROVES["f5a344e6c629"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

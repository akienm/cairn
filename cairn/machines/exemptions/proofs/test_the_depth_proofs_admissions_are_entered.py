"""Proof for ticket 3751ba501581 — the depth proof's admissions are entered in the exemption set.

Outline 9.4.6: "exemptions: the declared list of places a check skips something, each with its
reason. WHY: a skip with no written reason is a hole nobody can see." Ticket 3ff3ae16b2b9 gave
the inference sole-path rule a fourth seat (its depth proof) with no entries there, and the
admission sieve (b364df579e49) read four unentered admissions.

Teeth, one per falsifier clause:

  1. inspect(component='exemptions') carries no sole_path_admissions_are_entered finding;
  2. each of bus_client/remote.py, bus_client/tls.py, bus/proofs/test_the_bus_speaks_tcp.py has
     an entry at the depth seat naming it, kind sieve-scope, whose justification_kind and
     evidence equal those of the test_import_sieve.py seat's entry for the same file;
  3. exactly three entries stand at the depth seat, so the synthetic bus/proofs/test_x.py is out
     of the sieve's reach rather than entered;
  4. the depth proof passes.

    python3 cairn/machines/exemptions/proofs/test_the_depth_proofs_admissions_are_entered.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"3751ba501581": {
    "1": "the_live_set_reads_clean",
    "2": "each_admission_matches_its_sibling",
    "3": "three_entries_stand_at_the_depth_seat",
    "4": "the_depth_proof_passes",
}}

SET = REPO / "cairn/machines/exemptions/exemption_set.json"
DEPTH = "cairn/tools/import_sieve/proofs/test_an_admission_holds_at_any_depth.py"
SIBLING = "cairn/tools/import_sieve/proofs/test_import_sieve.py"
MEMBERS = {"bus_client/remote.py": "cairn/tools/bus_client/remote.py",
           "bus_client/tls.py": "cairn/tools/bus_client/tls.py",
           "bus/proofs/test_the_bus_speaks_tcp.py":
               "cairn/devices/cairn/machines/bus/proofs/test_the_bus_speaks_tcp.py"}
FAILURES: list[str] = []


def _check(name, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}", flush=True)
    except Exception as exc:  # noqa: BLE001 — a tooth reds by name, whatever broke it
        print(f"  FAIL  {name}\n        {type(exc).__name__}: {str(exc)[:1200]}", flush=True)
        FAILURES.append(name)


def _entries() -> list[dict]:
    return [e for e in json.loads(SET.read_text(encoding="utf-8"))["exemptions"] if isinstance(e, dict)]


def the_live_set_reads_clean():
    from cairn.machines.build_inspector import inspector
    report = inspector.inspect(component="exemptions")
    mine = [f.get("about") for f in report["findings"]
            if f.get("method") == "sole_path_admissions_are_entered"]
    assert mine == [], mine


def each_admission_matches_its_sibling():
    entries = _entries()
    for member, full in MEMBERS.items():
        here = [e for e in entries if e.get("path") == DEPTH and member in str(e.get("symbol"))]
        assert len(here) == 1, f"{member}: {len(here)} entries at {DEPTH}"
        sib = [e for e in entries if e.get("path") == SIBLING and full in str(e.get("symbol"))]
        assert len(sib) == 1, f"{full}: {len(sib)} entries at {SIBLING}"
        e, s = here[0], sib[0]
        assert e.get("kind") == "sieve-scope", (member, e.get("kind"))
        assert (e.get("justification_kind"), e.get("evidence")) == \
            (s.get("justification_kind"), s.get("evidence")), (member, e, s)


def three_entries_stand_at_the_depth_seat():
    at = [e.get("id") for e in _entries() if e.get("path") == DEPTH]
    assert len(at) == 3, at


def the_depth_proof_passes():
    r = subprocess.run([sys.executable, str(REPO / DEPTH)], cwd=REPO, capture_output=True,
                       text=True, timeout=600)
    assert r.returncode == 0, (r.stdout + r.stderr)[-1200:]


def main() -> int:
    for name in PROVES["3751ba501581"].values():
        _check(name, globals()[name])
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A proof declares its own time limit, and every tester run of it uses that limit (ticket 8383a32d20c5).

Akien, 2026-10-04: per-proof time limits. Each proof that needs more than the caller's budget
declares a top-level ``PROOF_TIMEOUT_S`` integer; run_proof reads it from the source (never by
import) and uses it over whatever timeout the caller passed — the hand seal, the reseal door and
the hollow alike, because all three run through run_proof. A declaration that is not a positive
integer literal reds the run rather than falling back to the caller's budget. And since the
budget is now the proof's own byte, a change of timeout alone is no longer a changed measurement
condition: the record keeps it, ``conditions.changed`` stops comparing it, so a green over a red
that only the timeout explains posts no notice (measured: n-daf1b756e369, 'timeout: 900 -> 120').

Every tooth imports the tester INSIDE its body, so a reverted device.py or conditions.py reds
teeth instead of breaking this file's import.
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"8383a32d20c5": {
    "1": "test_a_declared_limit_beats_the_callers_budget",
    "2": "test_an_undeclared_proof_takes_the_callers_budget",
    "3": "test_a_bad_declaration_reds_the_run",
    "4": "test_a_timeout_alone_is_not_a_changed_condition",
    "5": "test_the_slow_tester_proofs_declare_a_limit",
    "6": "test_the_conditions_notice_proof_stays_green_on_fixtures",
}}

_BODY = '''import time
PROVES = {"aaaaaaaaaaaa": {"1": "test_fixture_tooth"}}
time.sleep(2)
print("ok   test_fixture_tooth")
'''
_SLOW = ("test_hollow.py", "test_the_hollow_anchor_ignores_instrument_commits.py",
         "test_the_hollow_measures_the_repaired_build.py")


def _proof(prefix: str, header: str = "") -> Path:
    root = scratch_dir(prefix) / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text((header + "\n" if header else "") + _BODY)
    return proof


def _run(proof: Path, *, timeout: int, sink: str = "none") -> dict:
    from cairn.devices.tester.device import TesterDevice
    kw = {"scratch_sweep": {"skipped": "proof fixture"}} if sink == "validations" else {}
    return TesterDevice().run_proof(proof, sink=sink, caller="proof-fixture", timeout=timeout,
                                    isolation="none", **kw)


@contextlib.contextmanager
def _store(standing: list, home: Path):
    """read_validations answers `standing`; persist_validation records instead of writing."""
    import cairn.tools.validation_store.validation_store as vs
    from cairn.devices.tester import notices
    persisted: list = []
    saved = (vs.read_validations, vs.persist_validation, notices.HOME)
    vs.read_validations = lambda proof_path=None, **kw: list(standing)
    vs.persist_validation = lambda record, **kw: persisted.append(record) or "recorded"
    notices.HOME = home
    try:
        yield persisted
    finally:
        vs.read_validations, vs.persist_validation, notices.HOME = saved


def test_a_declared_limit_beats_the_callers_budget():
    rec = _run(_proof("cairn-ppt-1-", "PROOF_TIMEOUT_S = 7"), timeout=1)
    ev = rec["evidence"]
    assert rec["verdict"] == "green", ev.get("stderr_tail")
    assert ev["conditions"]["timeout"] == 7, ev["conditions"]


def test_an_undeclared_proof_takes_the_callers_budget():
    rec = _run(_proof("cairn-ppt-2-"), timeout=61)
    ev = rec["evidence"]
    assert rec["verdict"] == "green", ev.get("stderr_tail")
    assert ev["conditions"]["timeout"] == 61, ev["conditions"]


def test_a_bad_declaration_reds_the_run():
    for header in ('PROOF_TIMEOUT_S = "9"', "PROOF_TIMEOUT_S = 0", "PROOF_TIMEOUT_S = True",
                   "PROOF_TIMEOUT_S = 60 * 15"):
        rec = _run(_proof("cairn-ppt-3-", header), timeout=30)
        tail = str(rec["evidence"].get("stderr_tail") or "")
        assert rec["verdict"] == "red", (header, rec["evidence"])
        assert "PROOF_TIMEOUT_S" in tail, (header, tail)


def test_a_timeout_alone_is_not_a_changed_condition():
    from cairn.devices.tester import conditions
    assert conditions.changed({"timeout": 30, "proof": "a"}, {"timeout": 900, "proof": "a"}) == []
    proof = _proof("cairn-ppt-4-")
    home = proof.parents[2] / "notices"
    with _store([], home):
        first = _run(proof, timeout=60)
    red = dict(first, verdict="red")
    red["evidence"] = dict(first["evidence"],
                           conditions=dict(first["evidence"]["conditions"], timeout=30))
    with _store([red], home):
        rec = _run(proof, timeout=60, sink="validations")
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert "conditions_moved" not in rec["evidence"], rec["evidence"].get("conditions_moved")
    posted = sorted(home.glob("n-*.json")) if home.is_dir() else []
    assert posted == [], posted


def test_the_slow_tester_proofs_declare_a_limit():
    from cairn.devices.tester.device import declared_timeout
    here = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs"
    got = {name: declared_timeout(here / name) for name in _SLOW}
    assert all(v == 900 for v in got.values()), got


def test_the_conditions_notice_proof_stays_green_on_fixtures():
    import subprocess
    neighbour = (_REPO_ROOT / "cairn" / "devices" / "tester" / "proofs"
                 / "test_a_green_over_a_red_under_other_conditions_notifies.py")
    source = neighbour.read_text()
    assert source.count('fixtures="0" * 64') >= 2, "teeth 2 and 7 no longer move fixtures"
    assert "under_other_fixtures_posts_one_notice" in source
    done = subprocess.run([sys.executable, str(neighbour)], cwd=_REPO_ROOT,
                          capture_output=True, text=True, timeout=600)
    assert done.returncode == 0, done.stdout[-800:] + done.stderr[-800:]


def main() -> int:
    fails = 0
    for name in PROVES["8383a32d20c5"].values():
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

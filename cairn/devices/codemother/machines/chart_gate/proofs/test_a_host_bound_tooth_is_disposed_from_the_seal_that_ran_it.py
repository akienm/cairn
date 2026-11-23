"""Proof for ticket 7a275507818e — the verdict gate disposes a host-bound tooth from the seal of the host that ran it.

Measured 2026-11-23 on akiendelllinux: dc945eb1f072's Linux verdict was disposed killed ("bin/cairn test
bin/proofs/test_cairn_resolves_from_powershell.py exited 1") while akiendell_cc_0's Windows seal of that
proof on these bytes stood green on both teeth. The Linux run's only FAIL lines read UNRAN.
``StageGate._dispose`` disposed confirmed only on exit 0; verdict's ``host_bound_reading`` (50ac45cde4dd)
was asked only by the verdict door's criterion re-run.

The world is a fixture: a scratch component holding a proof and a FIXTURE seal (the approach of the verdict
machine's host-bound proof), a scratch commons mirror holding the validate and hypothesize berths (the
approach of the far-box berth proof), and an injected runner returning the measured run shapes. No
instrument forks, no live seal is read.

    python3 cairn/devices/codemother/machines/chart_gate/proofs/test_a_host_bound_tooth_is_disposed_from_the_seal_that_ran_it.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "7a275507818e": {
        "1": "test_an_unran_only_run_with_a_green_seal_on_these_bytes_is_confirmed",
        "2": "test_a_fail_line_that_is_not_unran_stays_killed",
        "3": "test_no_seal_on_these_bytes_stays_killed",
        "4": "test_a_green_run_needs_no_seal_and_a_timed_out_run_is_killed",
        "5": "test_the_gate_asks_verdicts_own_reader",
    },
}

_TEETH = ["tooth_1_a", "tooth_2_b"]
_UNRAN = ["FAIL tooth_1_a: AssertionError: UNRAN: PATHEXT resolution is Windows-only; run this on a Windows box",
          "FAIL tooth_2_b: AssertionError: UNRAN: cmd.exe is Windows-only; run this on a Windows box"]


def _component(tmp: Path, *, seal: bool = True, stale: bool = False) -> Path:
    """A scratch component: proofs/test_fx.py and, when asked, a green seal on it."""
    from cairn.tools.validation_store.validation_store import source_fingerprint
    (tmp / "proofs").mkdir()
    proof = tmp / "proofs" / "test_fx.py"
    proof.write_text("PROVES = {}\n", encoding="utf-8")
    if seal:
        fp = ("0" * 64) if stale else source_fingerprint(str(proof))
        (tmp / "validations").mkdir()
        (tmp / "validations" / "test_fx.json").write_text(json.dumps([{
            "claim": "proof test_fx.py passes", "caller": "cairn test", "verdict": "green",
            "date": "2026-11-23", "method": "fixture Windows seal",
            "evidence": {"teeth_green": list(_TEETH), "teeth_red": [], "source_fingerprint": fp}}]),
            encoding="utf-8")
    return proof


def _runner_for(exit_code, fail_lines, timed_out=False):
    def _runner(command, *, timeout_s=600, cwd=None):
        return {"command": command, "exit": exit_code, "timed_out": timed_out, "timeout_s": timeout_s,
                "seconds": 0.0, "tail": "\n".join(fail_lines), "fail_lines": list(fail_lines)}
    return _runner


@contextmanager
def _world(*, seal=True, stale=False):
    """A scratch component and a scratch commons mirror; ``chain._commons_mirror`` pointed at it."""
    from cairn.tools.chain import chain
    with tempfile.TemporaryDirectory(prefix="hostdispose-") as tmp:
        root = Path(tmp)
        (root / "comp").mkdir()
        proof = _component(root / "comp", seal=seal, stale=stale)
        mirror = root / "mirror"
        mirror.mkdir()
        spelling = "/home/akien/.cairn/devices/chart/0/packets/"
        hyp_name, val_name = "hypothesize-20261123T000000-aaaa.json", "validate-20261123T000001-bbbb.json"
        (mirror / hyp_name).write_text(json.dumps({"hypotheses": [
            {"piece": "the host-bound proof", "expect": "every tooth passes",
             "instrument": f"`bin/cairn test {proof.as_posix()}`"}]}), encoding="utf-8")
        (mirror / val_name).write_text(json.dumps({"hypothesize_ref": spelling + hyp_name}), encoding="utf-8")
        was = chain._commons_mirror
        chain._commons_mirror = lambda: str(mirror)
        try:
            yield {"validate_ref": spelling + val_name}
        finally:
            chain._commons_mirror = was


def _dispose(w, runner):
    from cairn.devices.codemother.machines.chart_gate.gate import StageGate

    class _Mute:
        def post(self, **_):
            return None
    got = StageGate("verdict", participant=_Mute(), runner=runner)._dispose(
        {"ticket": "7a275507818e", "validate_ref": w["validate_ref"]})
    assert len(got["dispositions"]) == 1, got
    return got["dispositions"][0]


def test_an_unran_only_run_with_a_green_seal_on_these_bytes_is_confirmed():
    with _world() as w:
        d = _dispose(w, _runner_for(1, _UNRAN))
    assert d["disposition"] == "confirmed", d
    assert isinstance(d.get("host_read"), dict) and d["host_read"].get("teeth") == sorted(_TEETH), d
    assert "exited 1" in d["by"] and "2026-11-23" in d["by"], d
    print("ok test_an_unran_only_run_with_a_green_seal_on_these_bytes_is_confirmed")


def test_a_fail_line_that_is_not_unran_stays_killed():
    with _world() as w:
        d = _dispose(w, _runner_for(1, _UNRAN + ["FAIL tooth_3_c: AssertionError: 2 != 3"]))
    assert d["disposition"] == "killed" and "host_read" not in d, d
    print("ok test_a_fail_line_that_is_not_unran_stays_killed")


def test_no_seal_on_these_bytes_stays_killed():
    for kw in ({"seal": False}, {"stale": True}):
        with _world(**kw) as w:
            d = _dispose(w, _runner_for(1, _UNRAN))
        assert d["disposition"] == "killed" and "host_read" not in d, (kw, d)
    print("ok test_no_seal_on_these_bytes_stays_killed")


def test_a_green_run_needs_no_seal_and_a_timed_out_run_is_killed():
    with _world(seal=False) as w:
        d = _dispose(w, _runner_for(0, []))
    assert d["disposition"] == "confirmed" and "host_read" not in d, d
    with _world() as w:
        d = _dispose(w, _runner_for(None, _UNRAN, timed_out=True))
    assert d["disposition"] == "killed" and "host_read" not in d, d
    print("ok test_a_green_run_needs_no_seal_and_a_timed_out_run_is_killed")


def test_the_gate_asks_verdicts_own_reader():
    from cairn.devices.codemother.machines.verdict import verdict as V
    asked = []
    was = V.host_bound_reading

    def _none(command, fail_lines, root=V.CAIRN_ROOT):
        asked.append(command)
        return None
    V.host_bound_reading = _none
    try:
        with _world() as w:
            d = _dispose(w, _runner_for(1, _UNRAN))
    finally:
        V.host_bound_reading = was
    assert asked, "the gate never asked verdict.host_bound_reading"
    assert d["disposition"] == "killed", d
    print("ok test_the_gate_asks_verdicts_own_reader")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

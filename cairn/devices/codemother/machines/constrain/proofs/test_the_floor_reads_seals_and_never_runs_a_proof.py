"""Proof for ticket 5243cf9dc630 — constrain's floor reads seals and never runs a proof.

Measured 2026-11-12: b0e65cf8a77e's floor asked the tester to run 44 proofs one after another
inside the chart stage (1858 s), the longest 1040.8 s, and every ask queued at the tester's one
shim lock. The fix: the floor reports each instrument's state from its standing seal, proven
green and every other state an unknown, and makes no tester ask at all.

The world. A scratch class-space root that is its own git repository, holding one tool
component (``cairn/tools/alpha``) with a charter, a module and planted proofs, each sealed by a
validations record written beside it the way the tester writes one (directory recipe: the seal's
``source_fingerprint`` is taken by ``cairn.tools.base.validation.source_fingerprint``). The
tester's bus is replaced by a counting stub for every tooth: ``reach`` answers any ask with a
green record, so a floor that asks is caught twice, by the count and by the green it was handed.
Clause 4 reads the tester's own component as it stood at e1d7881233e6, extracted by
``git archive`` into scratch (the live repository is not touched).

    bin/cairn test cairn/devices/codemother/machines/constrain/proofs/test_the_floor_reads_seals_and_never_runs_a_proof.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "5243cf9dc630": {
        "1": "test_a_proven_seal_reads_green_with_no_tester_ask",
        "2": "test_moved_red_and_never_sealed_ride_out_as_unknowns_with_no_ask",
        "3": "test_two_firings_agree_and_provenance_reproduces_them",
        "4": "test_the_floor_over_the_tester_asks_nothing_and_finishes_under_30_s",
    },
}

_ALPHA = os.path.join("cairn", "tools", "alpha")
_PIN = "e1d7881233e6"  # the commit clause 4 names
_BUDGET_S = 30.0


class _Tester:
    """The tester's bus, stubbed: every ask is counted and answered green."""

    def __init__(self) -> None:
        self.asks: list[dict] = []

    def request(self, **kw):
        self.asks.append(kw)
        return {"body": {"record": {"verdict": "green"}}}


@contextmanager
def _counted_tester():
    from cairn.tools.bus_client import bus_client
    stub, saved = _Tester(), bus_client.reach
    bus_client.reach = lambda *a, **kw: stub
    try:
        yield stub
    finally:
        bus_client.reach = saved


def _git(root: str, *args: str, **env) -> None:
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "p@x",
                        "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "p@x", **env})


def _world(**proofs: str) -> tuple[str, str]:
    """A scratch root, committed an hour ago, with ``proofs`` planted under alpha; and an
    orient berth that refs alpha by path."""
    from cairn.tools.scratch.scratch import scratch_dir
    root = str(scratch_dir("floor_reads_seals_"))
    home = os.path.join(root, _ALPHA)
    os.makedirs(os.path.join(home, "proofs"))
    Path(home, "alpha.py").write_text("x = 1\n")
    Path(home, "intention+why.json").write_text(json.dumps({
        "component": "alpha", "falsifier": "RED if alpha writes outside its table",
        "gates": "proof gate under the tester", "owner": "CC owns code"}))
    for name, body in proofs.items():
        Path(home, "proofs", name + ".py").write_text(body)
    berth = os.path.join(root, "instance", "orient-20261112T000000-5243cf9dc630.json")
    os.makedirs(os.path.dirname(berth))
    Path(berth).write_text(json.dumps({"intent": "bound alpha", "domain": "alpha",
                                       "scope": "IN: alpha", "unknowns": [],
                                       "refs": [os.path.join(_ALPHA, "alpha.py")],
                                       "confidence": 0.8, "provenance": {}}))
    hour_ago = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 3600))
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the world", GIT_COMMITTER_DATE=hour_ago,
         GIT_AUTHOR_DATE=hour_ago)
    return root, berth


def _seal(root: str, name: str, verdict: str, *, fingerprint: str | None = None) -> None:
    """A validations record beside proof ``name``, the shape the tester writes, dated now."""
    from cairn.tools.base.validation import source_fingerprint
    proof = os.path.join(root, _ALPHA, "proofs", name + ".py")
    vdir = os.path.join(root, _ALPHA, "validations")
    os.makedirs(vdir, exist_ok=True)
    record = {"claim": f"proof {name}.py passes", "caller": "cairn test",
              "date": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": verdict,
              "evidence": {"source_fingerprint": fingerprint or source_fingerprint(proof)}}
    Path(vdir, name + ".json").write_text(json.dumps([record]))


def _rel(name: str) -> str:
    return os.path.join(_ALPHA, "proofs", name + ".py")


def test_a_proven_seal_reads_green_with_no_tester_ask():
    from cairn.devices.codemother.machines.constrain import constrain
    root, berth = _world(test_sealed_green="raise SystemExit(0)\n")
    _seal(root, "test_sealed_green", "green")
    with _counted_tester() as tester:
        checks, cost = constrain.instrument_constraints(berth, root=root)
    assert [(c["source"], c["verdict"]) for c in checks] == [(_rel("test_sealed_green"), "green")], checks
    assert "standing seal" in checks[0]["text"], checks[0]["text"]
    assert tester.asks == [], f"a proven seal was asked of the tester: {tester.asks}"
    assert cost["instruments"] == 1, cost
    print("ok test_a_proven_seal_reads_green_with_no_tester_ask")


def test_moved_red_and_never_sealed_ride_out_as_unknowns_with_no_ask():
    from cairn.devices.codemother.machines.constrain import constrain
    root, berth = _world(test_sealed_red="raise SystemExit(1)\n",
                         test_moved="raise SystemExit(0)\n",
                         test_never_sealed="raise SystemExit(0)\n")
    _seal(root, "test_sealed_red", "red")
    _seal(root, "test_moved", "green")
    # the code moves under the green seal: one module edited, uncommitted
    Path(root, _ALPHA, "alpha.py").write_text("x = 2\n")
    with _counted_tester() as tester:
        fl = constrain.floor_packet(berth, root=root)
    assert tester.asks == [], f"the floor asked the tester {len(tester.asks)} time(s)"
    by = {c["source"]: c for c in fl["constraints"] if c["kind"] == "check"}
    want = {_rel("test_sealed_red"): "red", _rel("test_moved"): "moved",
            _rel("test_never_sealed"): "never-sealed"}
    assert {s: c["verdict"] for s, c in by.items()} == want, {s: c["verdict"] for s, c in by.items()}
    moved = by[_rel("test_moved")]["text"]
    assert os.path.join(_ALPHA, "alpha.py") in moved and "changed since the seal" in moved, moved
    assert "validations" not in moved.split("changed since the seal")[-1], moved
    unknowns = " ".join(fl["unknowns"] or [])
    for source, state in want.items():
        assert f"{source} is {state}" in unknowns, f"{source} ({state}) is not an unknown: {unknowns}"
    print("ok test_moved_red_and_never_sealed_ride_out_as_unknowns_with_no_ask")


def test_two_firings_agree_and_provenance_reproduces_them():
    from cairn.devices.codemother.machines.constrain import constrain
    root, berth = _world(test_sealed_green="raise SystemExit(0)\n",
                         test_sealed_red="raise SystemExit(1)\n",
                         test_moved="raise SystemExit(0)\n",
                         test_never_sealed="raise SystemExit(0)\n")
    _seal(root, "test_sealed_green", "green")
    _seal(root, "test_sealed_red", "red")
    _seal(root, "test_moved", "green", fingerprint="0" * 64)
    with _counted_tester() as tester:
        first = constrain.floor_packet(berth, root=root)
        second = constrain.floor_packet(berth, root=root)
        packet = {"intent_ref": berth, "constraints": first["constraints"],
                  "unknowns": first["unknowns"], "provenance": {}}
        prov = constrain.measured_provenance(packet, root=root)
    assert tester.asks == [], tester.asks
    for field in ("constraints", "unknowns"):
        assert first[field] == second[field], f"two firings over the same bytes differ on {field}"
        assert prov.get(field) == "floor", f"measured_provenance did not reproduce {field}: {prov}"
    assert len([c for c in first["constraints"] if c["kind"] == "check"]) == 4, first["constraints"]
    print("ok test_two_firings_agree_and_provenance_reproduces_them")


def test_the_floor_over_the_tester_asks_nothing_and_finishes_under_30_s():
    from cairn.devices.codemother.machines.constrain import constrain
    from cairn.tools.scratch.scratch import scratch_dir
    root = str(scratch_dir("floor_over_tester_"))
    archive = subprocess.run(["git", "-C", str(_REPO_ROOT), "archive", _PIN,
                              "cairn/devices/tester"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", root], input=archive, check=True)
    berth = os.path.join(root, "instance", "orient-20261112T000000-tester.json")
    os.makedirs(os.path.dirname(berth))
    Path(berth).write_text(json.dumps({"intent": "bound the tester", "domain": "tester",
                                       "scope": "IN: tester", "unknowns": [],
                                       "refs": ["cairn/devices/tester/device.py"],
                                       "confidence": 0.8, "provenance": {}}))
    with _counted_tester() as tester:
        t0 = time.monotonic()
        checks, cost = constrain.instrument_constraints(berth, root=root)
        took = time.monotonic() - t0
    assert cost["instruments"] >= 30 and len(checks) == cost["instruments"], cost
    assert tester.asks == [], f"the floor over the tester asked it {len(tester.asks)} time(s)"
    assert took < _BUDGET_S, f"the floor over the tester took {took:.1f} s"
    states = sorted({c["verdict"] for c in checks})
    print(f"ok test_the_floor_over_the_tester_asks_nothing_and_finishes_under_30_s "
          f"({cost['instruments']} instruments in {took:.2f} s, states {states})")


def main() -> int:
    failed = 0
    for name in PROVES["5243cf9dc630"].values():
        try:
            globals()[name]()
        except Exception as exc:  # noqa: BLE001 — every tooth runs; each red is named
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

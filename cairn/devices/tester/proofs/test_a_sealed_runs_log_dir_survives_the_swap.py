"""A sealed run's own log directory survives the swap (ticket bdd46aec0789).

Measured 2026-11-14 (ticket 2a6adebdd79b): a proof run under ``cairn test --exec`` wrote a
bus-bounce line under logs/tester/0/runs/<test>/, read it back inside the run, and nothing of
it reached the live ~/.cairn/logs. The instance seal binds a swap over ~/.cairn, so every write
the subject makes lands in the swap, and the swap is removed when the run ends. The run's own
log directory went with it. Consumers: 2a6adebdd79b (the bounce record) and 69cd (reads it).

The tester carries the WHOLE runs/<test>/ directory out of the swap before removing the swap,
and never names any device's file, so any device's run log survives (RULE 1: the provider
does not know its consumers).

  (1) a sealed run whose proof writes a line under runs/$CAIRN_TESTER_TEST_ID/ has that line
      live under run_dir(test)/sealed/ after the swap is gone, through run_proof and run_exec;
  (2) the swap the run made is still removed.

THE BIND IS DONE BY HAND, as in test_instance_seal's _PathSwapIsolation: this host refuses a
nested bwrap, and the seal's own run of this proof is nested. The fixture isolation hands the
subject the swap's path in BDD4_FIXTURE_SWAP, and the subject writes where ~/.cairn would put
the line under the bind. Everything else (the carry, the sweep) is the tester's own code.
Every tooth imports the tester inside its body, so a reverted device.py reds teeth.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "bdd46aec0789": {
        "1": "test_a_sealed_runs_log_line_reads_live_after_the_swap_is_gone",
        "2": "test_the_swap_the_run_made_is_still_removed",
    },
}

_LINE = '{"fixture": "bdd4", "survives": true}'

# The subject: writes one line into its run's log directory as the bind would place it.
_WRITER = '''\
import os, sys
from pathlib import Path
sys.path.insert(0, %r)
from cairn.tools.base.address import log_path
from cairn.devices.tester.isolation import _INSTANCE_ROOT
rel = (log_path("tester") / "runs" / os.environ["CAIRN_TESTER_TEST_ID"]).relative_to(_INSTANCE_ROOT)
d = Path(os.environ["BDD4_FIXTURE_SWAP"]) / rel
d.mkdir(parents=True, exist_ok=True)
(d / "fixture.jsonl").write_text(%r + "\\n")
print("ok   test_fixture_tooth")
''' % (str(_REPO_ROOT), _LINE)


def _sealed(dev):
    """Point the tester's seal at a small swap and a hand bind; return the list of swaps made."""
    from cairn.devices.tester.isolation import _SEAL_PREFIX, NoIsolation, SEALED, Seal

    made: list[Path] = []

    class _HandBind(NoIsolation):
        def wrap(self, argv, cwd, *, instance_swap=None):
            if instance_swap is None:
                return list(argv)
            return ["env", "-C", cwd, f"BDD4_FIXTURE_SWAP={instance_swap}"] + list(argv)

    def _snapshot():
        swap = scratch_dir(f"{_SEAL_PREFIX}{os.getpid()}-") / "cairn"
        swap.mkdir()
        made.append(swap)
        return str(swap)

    saved = {k: getattr(dev, k) for k in ("inside_an_instance_seal", "bwrap_available",
                                          "snapshot_instance_space", "check_instance_seal",
                                          "get_isolation")}
    dev.inside_an_instance_seal = lambda: False
    dev.bwrap_available = lambda: (True, "fixture: hand bind")
    dev.snapshot_instance_space = _snapshot
    dev.check_instance_seal = lambda iso, swap, cwd: Seal(SEALED, "fixture: hand bind")
    dev.get_isolation = lambda name: _HandBind()
    return made, lambda: [setattr(dev, k, v) for k, v in saved.items()]


def _run_dir(test: str) -> Path:
    from cairn.tools.base.address import log_path
    return log_path("tester") / "runs" / test


def _trash(path: Path) -> None:
    if path.exists():
        subprocess.run([str(_REPO_ROOT / "bin" / "cmd" / "trash"), str(path)],
                       capture_output=True, text=True)


def _via_run_proof():
    import cairn.devices.tester.device as dev
    root = scratch_dir("cairn-bdd4-proof-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text(_WRITER)
    made, restore = _sealed(dev)
    try:
        rec = dev.TesterDevice().run_proof(proof, sink="none", caller="proof-fixture-bdd4",
                                           timeout=120, isolation="none")
    finally:
        restore()
    return rec, rec["evidence"].get("test"), made


def _via_run_exec():
    import cairn.devices.tester.device as dev
    tmp = scratch_dir("cairn-bdd4-exec-")
    script = tmp / "writer.py"
    script.write_text(_WRITER)
    seen = tmp / "test-id"
    made, restore = _sealed(dev)
    try:
        rc = dev.TesterDevice().run_exec(
            f'echo -n "$CAIRN_TESTER_TEST_ID" > {seen} && {sys.executable} {script}',
            timeout=120, cwd=str(tmp))
    finally:
        restore()
    return rc, (seen.read_text() if seen.exists() else None), made


def test_a_sealed_runs_log_line_reads_live_after_the_swap_is_gone():
    rec, test, made = _via_run_proof()
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert made, "the run made no swap, so it measured nothing about one"
    carried = _run_dir(test) / "sealed" / "fixture.jsonl"
    try:
        assert carried.is_file(), f"run_proof: the swap's run log was not carried to {carried}"
        assert carried.read_text().strip() == _LINE, carried.read_text()
        assert rec["evidence"].get("run_log_carried", {}).get("carried") == ["fixture.jsonl"], \
            rec["evidence"].get("run_log_carried")
    finally:
        _trash(_run_dir(test))

    rc, test, made = _via_run_exec()
    assert rc == 0 and test, (rc, test)
    carried = _run_dir(test) / "sealed" / "fixture.jsonl"
    try:
        assert carried.is_file(), f"run_exec: the swap's run log was not carried to {carried}"
        assert carried.read_text().strip() == _LINE, carried.read_text()
    finally:
        _trash(_run_dir(test))


def test_the_swap_the_run_made_is_still_removed():
    rec, test, made = _via_run_proof()
    _trash(_run_dir(test))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    assert made and not any(m.parent.exists() for m in made), \
        f"run_proof left its swap behind: {[str(m.parent) for m in made if m.parent.exists()]}"
    rc, test, made = _via_run_exec()
    if test:
        _trash(_run_dir(test))
    assert rc == 0
    assert made and not any(m.parent.exists() for m in made), \
        f"run_exec left its swap behind: {[str(m.parent) for m in made if m.parent.exists()]}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))

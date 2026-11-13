"""The tester's closure runner puts the proof's own directory first on sys.path (ticket cfb4cb45d85c).

Measured 2026-11-13 on akiendell: run_proof called from cwd = the live root printed
sys.path[0] == '' and imported the live cairn, so a proof in a worktree measured the live
checkout instead of its own. The runner is ``python -c <runner>``, and ``-c`` puts the
CALLER's cwd first on sys.path. ``python <proof>`` puts the proof's directory there, and
the runner exists to read the subject exactly as ``python <proof>`` would.

Both teeth run the REAL tester through ``run_proof`` (``sink="none"``, isolation none) over a
fixture probe under a scratch root, from a cwd that is not the probe's directory. Windows is
simulated on Linux: there the wrap hands back the bare argv, so the subject inherits the
caller's cwd, while on Linux bwrap's ``--chdir`` sets it to the proof's directory and hides
the bug. ``NoIsolation.wrap`` is wrapped to answer as on Windows and restored after.

    bin/cairn test <this file>
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROBE = """import os, sys
print("PATH0=" + os.path.abspath(sys.path[0] or os.getcwd()) + ("" if sys.path[0] else " (empty)"))
import cfb4_sibling
print("SIB=" + cfb4_sibling.VALUE)
print("  ok   test_probe")
"""


def _scratch(prefix: str) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return Path(scratch_dir(prefix))


def _probe() -> Path:
    d = _scratch("cfb4-proof-dir-")
    (d / "cfb4_sibling.py").write_text('VALUE = "beside the proof"\n', encoding="utf-8")
    p = d / "test_cfb4_probe.py"
    p.write_text(PROBE, encoding="utf-8")
    return p


@contextmanager
def _cwd(path):
    was = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(was)


@contextmanager
def _as_on_windows():
    """The wrap answers as on Windows: the bare argv, with no cwd change."""
    from cairn.devices.tester import isolation
    cls = isolation.NoIsolation
    was = cls.wrap
    cls.wrap = lambda self, argv, cwd, *, instance_swap=None: list(argv)
    try:
        yield
    finally:
        cls.wrap = was


def _run(proof: Path, cwd) -> dict:
    from cairn.devices.tester.device import TesterDevice
    with _cwd(cwd), _as_on_windows():
        record = TesterDevice().run_proof(proof, sink="none", caller="cfb4cb45d85c",
                                          isolation="none")
    out = record["evidence"]["stdout_tail"]
    print("       " + out.replace("\n", "\n       ").rstrip())
    lines = dict(l.split("=", 1) for l in out.splitlines() if "=" in l and l[:4] in ("PATH", "SIB="))
    return {"record": record, **lines}


def test_from_the_live_root_sys_path_0_is_the_proofs_own_directory():
    proof = _probe()
    got = _run(proof, REPO)
    assert "PATH0" in got, f"the probe never said its sys.path[0]: {got['record']['evidence']}"
    assert got["PATH0"] == str(proof.parent), (
        f"sys.path[0] read {got['PATH0']!r}, not the proof's directory {str(proof.parent)!r}")


def test_a_module_beside_the_proof_beats_one_in_the_callers_cwd():
    proof = _probe()
    foreign = _scratch("cfb4-caller-cwd-")
    (foreign / "cfb4_sibling.py").write_text('VALUE = "the caller\'s cwd"\n', encoding="utf-8")
    got = _run(proof, foreign)
    assert got.get("SIB") == "beside the proof", (
        f"the probe imported {got.get('SIB')!r}: {got['record']['evidence']}")


PROVES = {
    "cfb4cb45d85c": {
        "1": "test_from_the_live_root_sys_path_0_is_the_proofs_own_directory",
        "2": "test_a_module_beside_the_proof_beats_one_in_the_callers_cwd",
    },
}


if __name__ == "__main__":
    reds = 0
    for name, fn in [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — each tooth's failure is said, verbatim
            reds += 1
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print("\nGREEN" if not reds else f"\nRED ({reds})")
    sys.exit(1 if reds else 0)

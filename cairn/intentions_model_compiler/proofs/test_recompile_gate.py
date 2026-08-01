"""Proof for intentions-model-compiler child c — the WRITE GATE (recompile_gate.sh).

Teeth a hollow gate could not pass:

  - POKES THE DOOR. Running the gate compiles the model from sources: point it at a temp
    source tree and the model appears on disk holding exactly those sources. A gate that
    no-ops (the hollow build) trips this.
  - REVERTS A STALE MODEL. Garbage written to the model path is replaced by the true
    projection when the gate fires — the write-door's drift-reversal, reached through the
    gate. A gate that left the garbage trips this.
  - NON-BLOCKING, LOUD IN THE RECORD (Law 7). When the compile CANNOT write, the gate still
    exits 0 (a save is never blocked by an unrelated recompile) AND records the failure to
    the instance-space log — the error is collapsed at the surface, never lost. A gate that
    crashed the session, or swallowed the failure silently, trips this.

The gate is HOST-NOTICING, not owner-emitting (see the charter host_seam / IOU): whether the
FileChanged hook FIRES on a disk change is host behavior, verified out of turn — not here.
This proves the COMMAND the hook pokes.

    python3 cairn/intentions_model_compiler/proofs/test_recompile_gate.py   # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

_GATE = Path(__file__).resolve().parents[1] / "recompile_gate.sh"


def _tree(d: str) -> tuple[str, str]:
    """A minimal two-tree source layout the gate can compile."""
    commons = os.path.join(d, "CairnCommons")
    code = os.path.join(d, "cairn")
    os.makedirs(os.path.join(commons, "intentions-not-beside-code"))
    os.makedirs(os.path.join(commons, "intentions-congruency-lab"))
    os.makedirs(os.path.join(code, "cairn", "base"))
    with open(os.path.join(commons, "intentions-not-beside-code", "telos.md"), "w") as f:
        f.write("the frame")
    with open(os.path.join(code, "cairn", "base", "intention+why.json"), "w") as f:
        json.dump({"what": "substrate"}, f)
    return commons, code


def _run(commons: str, code: str, out: str, logdir: str) -> subprocess.CompletedProcess:
    # A proof-poked gate run is not a real firing: its trace goes to a scratch berth.
    env = {**os.environ, "CAIRN_LB_TRACE_ROOT": tempfile.mkdtemp(prefix="rg-proof-traces-"),
           "CAIRN_COMMONS_ROOT": commons, "CAIRN_CODE_ROOT": code,
           "CAIRN_LAB_OUT": out, "CAIRN_LOG_DIR": logdir}
    return subprocess.run(["bash", str(_GATE)], capture_output=True, text=True, env=env)


def test_the_gate_pokes_the_door():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        r = _run(commons, code, lab, os.path.join(d, "logs"))
        assert r.returncode == 0, f"the gate must exit 0, got {r.returncode}: {r.stderr!r}"
        got = {n for n in os.listdir(lab) if not n.startswith("_")}
        assert got == {"telos.md", "cairn-base--intention+why.json"}, \
            f"both source trees copied in via the gate — a no-op gate copies nothing; got {got}"


def test_the_gate_reverts_a_hand_edited_copy():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        lab = os.path.join(commons, "intentions-congruency-lab")
        with open(os.path.join(lab, "telos.md"), "w") as f:
            f.write("HAND-EDITED GARBAGE")
        _run(commons, code, lab, os.path.join(d, "logs"))
        with open(os.path.join(lab, "telos.md"), encoding="utf-8") as f:
            assert f.read() == "the frame", \
                "the hand-edit was reverted to the source (drift does not survive a gate firing)"


def test_non_blocking_but_loud_in_the_record():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        # An impossible out path (its parent is a FILE) makes the write-door raise.
        blocker = os.path.join(d, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        out = os.path.join(blocker, "cannot", "lab")
        logdir = os.path.join(d, "logs")
        r = _run(commons, code, out, logdir)
        assert r.returncode == 0, "a failed recompile never blocks the session (exit 0)"
        log = os.path.join(logdir, "recompile-gate.log")
        assert os.path.exists(log), "the failure is recorded, not swallowed (Law 7)"
        assert "FAILED" in open(log, encoding="utf-8").read(), "the record names the failure"


def _main() -> int:
    checks = [
        test_the_gate_pokes_the_door,
        test_the_gate_reverts_a_hand_edited_copy,
        test_non_blocking_but_loud_in_the_record,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — recompile_gate: the write gate pokes the copy door (the lab fills and "
          "reverts drift), never blocks a save, and records a failed run rather than "
          "swallowing it (Law 7). Host-noticing, not owner-emitting — the IOU is in the charter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

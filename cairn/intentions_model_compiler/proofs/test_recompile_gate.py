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
    os.makedirs(os.path.join(commons, "intentions-other"))
    os.makedirs(os.path.join(commons, "intentions"))
    os.makedirs(os.path.join(code, "base"))
    with open(os.path.join(commons, "intentions-other", "telos.md"), "w") as f:
        f.write("the frame")
    with open(os.path.join(code, "base", "intention+why.json"), "w") as f:
        json.dump({"what": "substrate"}, f)
    return commons, code


def _run(commons: str, code: str, out: str, logdir: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CAIRN_COMMONS_ROOT": commons, "CAIRN_CODE_ROOT": code,
           "CAIRN_MODEL_OUT": out, "CAIRN_LOG_DIR": logdir}
    return subprocess.run(["bash", str(_GATE)], capture_output=True, text=True, env=env)


def test_the_gate_pokes_the_door():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        out = os.path.join(commons, "intentions", "_model.json")
        r = _run(commons, code, out, os.path.join(d, "logs"))
        assert r.returncode == 0, f"the gate must exit 0, got {r.returncode}: {r.stderr!r}"
        with open(out, encoding="utf-8") as f:
            model = json.load(f)
        assert {i["id"] for i in model["intentions"]} == {"telos", "base"}, \
            "both source trees compiled in via the gate — a no-op gate writes no model"


def test_the_gate_reverts_a_stale_model():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        out = os.path.join(commons, "intentions", "_model.json")
        with open(out, "w") as f:
            f.write("HAND-EDITED GARBAGE")
        _run(commons, code, out, os.path.join(d, "logs"))
        with open(out, encoding="utf-8") as f:
            model = json.load(f)     # would raise if still garbage
        assert {i["id"] for i in model["intentions"]} == {"telos", "base"}, \
            "the stale model was reverted to the true projection (drift does not survive a gate firing)"


def test_non_blocking_but_loud_in_the_record():
    with tempfile.TemporaryDirectory() as d:
        commons, code = _tree(d)
        # An impossible out path (its parent is a FILE) makes the write-door raise.
        blocker = os.path.join(d, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        out = os.path.join(blocker, "cannot", "_model.json")
        logdir = os.path.join(d, "logs")
        r = _run(commons, code, out, logdir)
        assert r.returncode == 0, "a failed recompile never blocks the session (exit 0)"
        log = os.path.join(logdir, "recompile-gate.log")
        assert os.path.exists(log), "the failure is recorded, not swallowed (Law 7)"
        assert "FAILED" in open(log, encoding="utf-8").read(), "the record names the failure"


def _main() -> int:
    checks = [
        test_the_gate_pokes_the_door,
        test_the_gate_reverts_a_stale_model,
        test_non_blocking_but_loud_in_the_record,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — recompile_gate: the write gate pokes the compile door (the model appears "
          "and reverts drift), never blocks a save, and records a failed compile rather than "
          "swallowing it (Law 7). Host-noticing, not owner-emitting — the IOU is in the charter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

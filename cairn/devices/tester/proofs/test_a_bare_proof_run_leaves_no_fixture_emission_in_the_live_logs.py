"""Proof (ticket 97175c117de3) — a proof run leaves no fixture emission in the live logs tree.

MEASURED 2026-11-14. On akiendelllinux, ~/.cairn/logs/charter/0 held 7,435 append_entry
emissions, 4,910 of them for a /tmp fixture history. On akienyoga9i all 80 live charter
emissions carried a Temp fixture location. A one-append stand-in wrote one live file run bare,
and on Windows (no bwrap, so no instance seal) one more under ``bin/cairn test``.

This file holds the tooth that stands under every answer to Q#101 (open-e628fac13860):
  (2) the stand-in run under ``bin/cairn test`` (the tester's published entry — RULE 1) passes,
      and no new file naming it appears under the live ``~/.cairn/logs``. The instance seal
      swaps instance-space out from under the subject, so its emission lands in the swap.
      Green on Linux. RED on Windows until Windows has an instance seal — a true red.
Tooth (1), the bare spelling, waits on Q#101's answer, which decides what "bare" is refused by.

Files are counted BY THE STAND-IN'S OWN ID, a fresh token per run, never ``find -newer``: a
concurrent proof's emissions would otherwise read as this one's. The stand-in's fixture world is
under a scratch dir of this proof's own.

    python cairn/devices/tester/proofs/test_a_bare_proof_run_leaves_no_fixture_emission_in_the_live_logs.py
"""
from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

PROOF_TIMEOUT_S = 300

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "97175c117de3": {
        "2": "test_a_tester_run_leaves_no_fixture_emission_in_the_live_logs",
    },
}

_LIVE_LOGS = Path.home() / ".cairn" / "logs"
_CAIRN_ARGV = bash_script_argv(str(REPO / "bin" / "cairn"))

# One append_entry on a fixture history in a fresh temp dir, its record carrying TOKEN as its id
# so the emission (values.identity, and the pointer) names this run and nothing else.
_STAND_IN = """
import sys, tempfile
from pathlib import Path
sys.path.insert(0, {repo!r})
from cairn.tools.charter.projector import append_entry
d = Path(tempfile.mkdtemp(prefix="emission-fixture-"))
append_entry(str(d / "history.json"), str(d / "state.json"), {{"id": {token!r}, "standing": "fixture"}})
print("ok   test_one_append_on_a_fixture_history", flush=True)
"""


def _live_files_naming(token: str) -> list[Path]:
    if not _LIVE_LOGS.is_dir():
        return []
    hits = []
    for f in _LIVE_LOGS.rglob("*.json"):
        try:
            if token in f.read_text(encoding="utf-8", errors="replace"):
                hits.append(f)
        except OSError:
            continue
    return hits


def test_a_tester_run_leaves_no_fixture_emission_in_the_live_logs():
    token = f"emission-standin-{uuid.uuid4().hex[:12]}"
    world = scratch_dir("testing-emission-world-")
    proof = world / "test_one_append_stand_in.py"
    proof.write_bytes(_STAND_IN.format(repo=str(REPO), token=token).encode())
    env = git_env()
    for k in ("TMPDIR", "TEMP", "TMP"):
        env[k] = str(world)
    assert not _live_files_naming(token), "a fresh token already names a live file — the count measures nothing"
    r = subprocess.run([*_CAIRN_ARGV, "test", str(proof), "--timeout", "120"], capture_output=True,
                       text=True, cwd=str(REPO), env=env, timeout=PROOF_TIMEOUT_S - 30)
    leaked = _live_files_naming(token)
    try:
        assert r.returncode == 0, (f"the stand-in did not pass under bin/cairn test (rc {r.returncode}); "
                                   f"stdout: {r.stdout[-800:]} stderr: {r.stderr[-400:]}")
        assert not leaked, (f"a tester run wrote {len(leaked)} file(s) naming its fixture into the live "
                            f"logs: {[str(p) for p in leaked]}")
    finally:
        for f in leaked:               # a red leaves nothing of its own behind in the live tree
            f.unlink(missing_ok=True)


if __name__ == "__main__":
    failed = 0
    for name in [n for p in PROVES.values() for n in p.values()]:
        try:
            globals()[name]()
            print(f"ok   {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)

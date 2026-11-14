"""Proof (ticket 56b61c10bdbe) — a proof run through the tester on Windows writes nothing under
the live ~/.cairn.

MEASURED 2026-11-14 on akienyoga9i: bwrap_available() is false on Windows, so the tester records
the instance seal INDETERMINATE and the subject writes live. A SEEDED-BY-A-PROOF file
(test_instance_seal.py:60) sat in the live ~/.cairn as the evidence. The seal this ticket builds
starts the subject at Low integrity, with its home, profile, LocalAppData and temp pointed at a
Low-labelled swap. Anything the redirect misses is refused by the kernel, because the live root
is Medium.

The teeth, red-first:
  (1) a stand-in run under ``bin/cairn test`` reports the seal marker and a ~/.cairn that is not
      the account's, and no live file names its fresh token (the 97175c117de3 tooth-2 shape);
  (2) its write to the ABSOLUTE live root (scratch.account_home(), i.e. SHGetKnownFolderPath)
      is PermissionError and lands nowhere: the kernel holds the seal, not the env;
  (3) it can write its own ~/.cairn (the swap) and its temp, so the seal does not merely deny;
  (4) with the Low launch faulted (CAIRN_TESTER_LOWIL_FAULT=1), a seal that would otherwise
      confirm reads INDETERMINATE and names the launcher. Never a confirmed seal;
  (5) a nested ``bin/cairn test`` inside a sealed run inherits the same ~/.cairn.

The stand-ins report into this proof's own world dir, which this proof labels Low, since a Low
subject cannot write a Medium dir. Runs on win32 only. Elsewhere it SKIPS LOUDLY, naming the
platform; Linux is covered by the bwrap seal's own proofs.

    python cairn/devices/tester/proofs/test_a_windows_tester_run_writes_nothing_under_the_live_cairn.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

PROOF_TIMEOUT_S = 400

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.scratch.scratch import account_home, git_env, scratch_dir  # noqa: E402

PROVES = {
    "56b61c10bdbe": {
        "1": "test_1_a_tester_run_is_sealed_and_leaves_no_token_in_the_live_logs",
        "2": "test_2_an_absolute_write_to_the_live_root_is_refused_by_the_kernel",
        "3": "test_3_the_subject_can_write_its_swap_and_its_temp",
        "4": "test_4_a_faulted_low_launch_reads_indeterminate_never_sealed",
        "5": "test_5_a_nested_tester_run_inherits_the_same_swap",
    },
}

_CAIRN_ARGV = bash_script_argv(str(REPO / "bin" / "cairn"))
_LIVE = account_home() / ".cairn"

# The stand-in: writes a token file under ITS ~/.cairn/logs, tries the absolute live root, tries
# its temp, and reports all of it (plus the marker and its ~/.cairn identity) as JSON. With
# NEST set, it first runs itself again under bin/cairn test as the inner subject.
_STAND_IN = r'''
import json, os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, {repo!r})
from cairn.tools.scratch.scratch import account_home
token, report, nest = {token!r}, Path({report!r}), {nest!r}
r = {{"sealed": os.environ.get("CAIRN_TESTER_INSTANCE_SEALED") == "1"}}
home = Path.home() / ".cairn"
st = os.stat(home) if home.exists() else None
r["cairn"] = [st.st_dev, st.st_ino] if st else None
def attempt(key, p):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(token)
        r[key] = "WROTE"
    except Exception as e:
        r[key] = type(e).__name__
attempt("swap_write", home / "logs" / (token + ".json"))
attempt("absolute_live_write", account_home() / ".cairn" / "logs" / (token + "-absolute.json"))
attempt("temp_write", Path(tempfile.gettempdir()) / (token + ".tmp"))
if nest:
    inner = report.with_name("inner_" + Path(__file__).name)
    inner.write_text(Path(__file__).read_text().replace(repr(nest), "None", 1)
                     .replace(repr(str(report)), repr(str(report.with_name("inner.json"))), 1))
    p = subprocess.run({cairn_argv!r} + ["test", str(inner), "--timeout", "120"],
                       capture_output=True, text=True, cwd={repo!r})
    r["nested_rc"] = p.returncode
    r["nested_tail"] = p.stdout[-600:]
report.write_text(json.dumps(r))
print("ok   test_one_sealed_stand_in", flush=True)
'''


def _windows() -> bool:
    if sys.platform != "win32":
        print(f"SKIP 56b61c10bdbe: Windows seal teeth run on win32 only; this is {sys.platform}")
        return False
    return True


def _low_world() -> Path:
    world = scratch_dir("testing-winseal-world-")
    r = subprocess.run(["icacls", str(world), "/setintegritylevel", "(OI)(CI)L"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"could not label the proof's own world Low: {r.stdout} {r.stderr}"
    return world


def _live_files_naming(token: str) -> list[Path]:
    if not _LIVE.is_dir():
        return []
    hits = []
    for f in _LIVE.rglob(f"*{token}*"):
        hits.append(f)
    return hits


_RUNS: dict[bool, tuple] = {}


def _run_stand_in(nest: bool = False):
    """One stand-in run under bin/cairn test, shared by the teeth that read it."""
    if nest in _RUNS:
        return _RUNS[nest]
    token = f"winseal-standin-{uuid.uuid4().hex[:12]}"
    world = _low_world()
    report = world / "report.json"
    proof = world / "test_winseal_stand_in.py"
    proof.write_text(_STAND_IN.format(repo=str(REPO), token=token, report=str(report),
                                      nest="nest" if nest else None, cairn_argv=_CAIRN_ARGV),
                     encoding="utf-8")
    assert not _live_files_naming(token), "a fresh token already names a live file — the count measures nothing"
    p = subprocess.run([*_CAIRN_ARGV, "test", str(proof), "--timeout", "240"], capture_output=True,
                       text=True, cwd=str(REPO), env=git_env(), timeout=PROOF_TIMEOUT_S - 60)
    seen = _live_files_naming(token)
    for f in seen:                     # a red leaves nothing of its own in the tree it read
        f.unlink(missing_ok=True)
    got = json.loads(report.read_text()) if report.exists() else None
    inner = world / "inner.json"
    got_inner = json.loads(inner.read_text()) if inner.exists() else None
    _RUNS[nest] = (p, got, seen, got_inner)
    return _RUNS[nest]


def _live_identity():
    st = os.stat(_LIVE) if _LIVE.exists() else None
    return [st.st_dev, st.st_ino] if st else None


def test_1_a_tester_run_is_sealed_and_leaves_no_token_in_the_live_logs():
    if not _windows():
        return
    p, got, seen, _ = _run_stand_in()
    assert p.returncode == 0, f"the stand-in did not pass under bin/cairn test (rc {p.returncode}): {p.stdout[-800:]} {p.stderr[-400:]}"
    assert got is not None, f"the stand-in wrote no report: {p.stdout[-600:]}"
    assert got["sealed"], f"no seal marker: the subject ran unsealed. Report: {got}"
    assert got["cairn"] != _live_identity(), f"the subject's ~/.cairn IS the live root: {got['cairn']}"
    assert not seen, f"the run wrote {len(seen)} file(s) naming its token into the live root: {[str(s) for s in seen]}"


def test_2_an_absolute_write_to_the_live_root_is_refused_by_the_kernel():
    if not _windows():
        return
    p, got, seen, _ = _run_stand_in()
    assert got is not None, f"the stand-in wrote no report: {p.stdout[-600:]}"
    assert got["absolute_live_write"] == "PermissionError", (
        f"a write to the account's absolute live root read {got['absolute_live_write']!r}, not "
        f"PermissionError: the env redirect is all that stood between the subject and live")
    assert not any("absolute" in s.name for s in seen), f"the absolute write landed live: {seen}"


def test_3_the_subject_can_write_its_swap_and_its_temp():
    if not _windows():
        return
    p, got, _, _ = _run_stand_in()
    assert got is not None, f"the stand-in wrote no report: {p.stdout[-600:]}"
    # A write that lands in the LIVE root is not a write to a swap: red-first measured this tooth
    # green on an unsealed run, so the swap must exist before its writability means anything.
    assert got["sealed"] and got["cairn"] != _live_identity(), (
        f"there is no swap to write: marker {got['sealed']}, ~/.cairn {got['cairn']} vs live {_live_identity()}")
    assert got["swap_write"] == "WROTE" and got["temp_write"] == "WROTE", (
        f"a seal that only denies: swap {got['swap_write']}, temp {got['temp_write']}")


def test_4_a_faulted_low_launch_reads_indeterminate_never_sealed():
    if not _windows():
        return
    from cairn.devices.tester import isolation as iso
    cwd = str(Path(__file__).resolve().parent)
    swap = iso.snapshot_instance_space()
    try:
        clean = iso.check_instance_seal(iso.NoIsolation(), swap, cwd)
        assert clean.sealed, f"precondition: an unfaulted Windows seal must confirm, read {clean.verdict}: {clean.detail}"
        os.environ["CAIRN_TESTER_LOWIL_FAULT"] = "1"
        try:
            faulted = iso.check_instance_seal(iso.NoIsolation(), swap, cwd)
        finally:
            os.environ.pop("CAIRN_TESTER_LOWIL_FAULT", None)
        assert faulted.verdict == iso.INDETERMINATE and not faulted.sealed, (
            f"a faulted Low launch read {faulted.verdict}: {faulted.detail}")
        assert "low" in faulted.detail.lower(), f"the INDETERMINATE does not name the launcher: {faulted.detail}"
    finally:
        shutil.rmtree(Path(swap).parent, ignore_errors=True)


def test_5_a_nested_tester_run_inherits_the_same_swap():
    if not _windows():
        return
    p, got, seen, inner = _run_stand_in(nest=True)
    assert got is not None, f"the outer stand-in wrote no report: {p.stdout[-600:]}"
    assert got.get("nested_rc") == 0, f"the nested run failed (rc {got.get('nested_rc')}): {got.get('nested_tail')}"
    assert inner is not None, "the inner stand-in wrote no report"
    assert inner["sealed"] and inner["cairn"] == got["cairn"], (
        f"the nested run did not inherit the outer swap: outer {got['cairn']}, inner {inner['cairn']}, "
        f"marker {inner['sealed']}")
    assert not seen, f"the nested run wrote live: {[str(s) for s in seen]}"


if __name__ == "__main__":
    failed = 0
    for name in [n for p in PROVES.values() for n in p.values()]:
        try:
            globals()[name]()
            print(f"ok   {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {str(e)[:400]}")
    sys.exit(1 if failed else 0)

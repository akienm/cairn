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

Ruling C (orchestrator, 2026-11-14): MSYS bash cannot start at Low (msys-2.0.dll's
NtCreateDirectoryObject gets 0xC0000022, and the process exits 0xC0000142), so a subject that
drives bash runs DETECT-kind. That means the same redirect at the caller's integrity, witnessed by
a before/after manifest of the live root, which runs on every Windows sealed run of either kind:
  (6) a detect-kind run names its kind and why, and a write it makes to the root the manifest
      watches reads BREACHED, naming the path. The watched root is a scratch stand-in for live,
      swapped in-process, so this proof never writes the real live root;
  (7) a subject whose source does not read as driving bash, but which spawns bash anyway, runs
      prevent-kind, and its run reads INDETERMINATE naming bash, never red;
  (8) a clean prevent-kind run records seal_kind prevent, no why, and a measured live manifest
      with zero writes.

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
        "6": "test_6_a_detect_kind_run_names_its_kind_and_a_live_write_reads_breached",
        "7": "test_7_a_prevent_kind_subject_that_spawns_bash_reads_indeterminate_naming_bash",
        "8": "test_8_a_clean_prevent_kind_run_records_its_kind_and_an_empty_live_manifest",
    },
}

_CAIRN_ARGV = bash_script_argv(str(REPO / "bin" / "cairn"))
_LIVE = account_home() / ".cairn"

# The stand-in: writes a token file under ITS ~/.cairn/logs, tries the absolute live root, tries
# its temp, and reports all of it (plus the marker and its ~/.cairn identity) as JSON. With
# NEST set, it first runs itself again under bin/cairn test as the inner subject. Only the nested
# one carries the bin/cairn argv in its text: that text is what makes a run detect-kind (ruling C),
# and teeth 1-3 measure the prevent kind. A nested (detect-kind) stand-in skips the absolute live
# write: nothing refuses it under detect, so it would land live; tooth 6 measures that witness.
_STAND_IN = r'''
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, {repo!r})
from cairn.tools.scratch.scratch import account_home, scratch_dir
token, report, nest, probe_live = {token!r}, Path({report!r}), {nest!r}, {probe_live!r}
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
if probe_live:   # prevent-kind only: under detect nothing refuses it, and it would land live
    attempt("absolute_live_write", account_home() / ".cairn" / "logs" / (token + "-absolute.json"))
try:   # through the scratch door, which builds on the (redirected) TEMP
    attempt("temp_write", scratch_dir("winseal-temp-") / (token + ".tmp"))
except Exception as e:
    r["temp_write"] = type(e).__name__
{nest_block}
report.write_text(json.dumps(r))
print("ok   test_one_sealed_stand_in", flush=True)
'''
_NEST_BLOCK = r'''
if nest:
    inner = report.with_name("inner_" + Path(__file__).name)
    inner.write_text(Path(__file__).read_text().replace(repr(nest), "None", 1)
                     .replace(repr(str(report)), repr(str(report.with_name("inner.json"))), 1))
    p = subprocess.run({cairn_argv!r} + ["test", str(inner), "--timeout", "120"],
                       capture_output=True, text=True, cwd={repo!r})
    r["nested_rc"] = p.returncode
    r["nested_tail"] = p.stdout[-600:]
'''

# Tooth 6's subject: it drives bash by name (so it is detect-kind), then writes a token into the
# root the manifest watches, which tooth 6 points at a scratch stand-in for live.
_DETECT_SUBJECT = r'''
import shutil, subprocess, sys
from pathlib import Path
assert subprocess.run([shutil.which("bash"), "-c", "exit 0"]).returncode == 0, "bash did not run"
Path({watched!r}, {token!r}).write_text("x")
print("ok   test_detect_stand_in", flush=True)
'''

# Tooth 7's subject: its source does not read as driving bash, and it spawns bash anyway.
_HIDDEN_BASH_SUBJECT = r'''
import shutil, subprocess, sys
exe = shutil.which("b" + "ash")
r = subprocess.run([exe, "-c", "exit 0"])
assert r.returncode == 0, f"the hidden spawn exited {r.returncode}"
print("ok   test_hidden_spawn_stand_in", flush=True)
'''

# Tooth 8's subject: python only, writes its own ~/.cairn.
_CLEAN_SUBJECT = r'''
from pathlib import Path
(Path.home() / ".cairn" / {token!r}).write_text("x")
print("ok   test_clean_stand_in", flush=True)
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
    block = _NEST_BLOCK.format(cairn_argv=_CAIRN_ARGV, repo=str(REPO)) if nest else ""
    proof.write_text(_STAND_IN.format(repo=str(REPO), token=token, report=str(report),
                                      nest="nest" if nest else None, nest_block=block,
                                      probe_live=not nest),
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


def _run_in_process(source: str, name: str, watched: Path | None = None) -> dict:
    """One run_proof of ``source`` (sink none, so nothing persists), with the manifest's watched
    root swapped for ``watched`` when given. Returns the record."""
    from cairn.devices.tester import device as d
    world = _low_world()
    proof = world / name
    proof.write_text(source, encoding="utf-8")
    real = d._live_root
    if watched is not None:
        d._live_root = lambda: watched
    try:
        return d.TesterDevice().run_proof(proof, sink="none", caller="56b61c10bdbe proof", timeout=120)
    finally:
        d._live_root = real


def test_6_a_detect_kind_run_names_its_kind_and_a_live_write_reads_breached():
    if not _windows():
        return
    token = f"winseal-detect-{uuid.uuid4().hex[:12]}"
    watched = scratch_dir("testing-winseal-watched-")
    (watched / "standing.txt").write_text("before")
    rec = _run_in_process(_DETECT_SUBJECT.format(watched=str(watched), token=token),
                          "test_winseal_detect_stand_in.py", watched=watched)
    seal = rec["evidence"]["instance_seal"]
    assert seal.get("seal_kind") == "detect", f"a subject that drives bash ran {seal.get('seal_kind')!r}: {seal}"
    assert "bash" in (seal.get("seal_kind_why") or ""), f"a detect seal without its why: {seal}"
    assert rec["verdict"] == "green", (f"the detect-kind subject did not run green (bash at the "
                                       f"caller's integrity must start): {rec['verdict']} "
                                       f"{rec['evidence'].get('stderr_tail')}")
    live = seal.get("live_writes") or {}
    assert live.get("measured") and token in live.get("paths", []), f"the manifest did not see the write: {live}"
    assert seal["verdict"] == "breached" and token in seal["detail"], (
        f"a write to the watched root read {seal['verdict']}: {seal['detail']}")


def test_7_a_prevent_kind_subject_that_spawns_bash_reads_indeterminate_naming_bash():
    if not _windows():
        return
    rec = _run_in_process(_HIDDEN_BASH_SUBJECT, "test_winseal_hidden_bash_stand_in.py")
    seal = rec["evidence"]["instance_seal"]
    assert seal.get("seal_kind") == "prevent", f"precondition: the hidden spawn must run prevent-kind: {seal}"
    assert rec["verdict"] == "indeterminate", (
        f"a bash spawned at Low read {rec['verdict']!r}, not indeterminate: "
        f"{rec['evidence'].get('stderr_tail')}")
    assert "bash" in rec["evidence"].get("indeterminate", "").lower(), (
        f"the INDETERMINATE does not name bash: {rec['evidence'].get('indeterminate')}")


def test_8_a_clean_prevent_kind_run_records_its_kind_and_an_empty_live_manifest():
    if not _windows():
        return
    token = f"winseal-clean-{uuid.uuid4().hex[:12]}"
    rec = _run_in_process(_CLEAN_SUBJECT.format(token=token), "test_winseal_clean_stand_in.py")
    seal = rec["evidence"]["instance_seal"]
    assert rec["verdict"] == "green" and seal["verdict"] == "sealed", (
        f"a clean subject read {rec['verdict']}, seal {seal['verdict']}: {seal['detail']}")
    assert seal.get("seal_kind") == "prevent" and "seal_kind_why" not in seal, f"kind not recorded as prevent: {seal}"
    live = seal.get("live_writes") or {}
    assert live.get("measured") and live.get("count") == 0, f"the live manifest was not measured empty: {live}"
    assert token in seal["wrote_to_instance"]["paths"], f"its swap write was not witnessed: {seal['wrote_to_instance']}"


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

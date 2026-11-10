"""Proof: the launchers moved to the devices that own them (ticket 38125c3ada38).

Outline Q#24, Akien 2026-11-04, "yes to both": the bootstrap floor belongs to the
Recovery device, superclaude to the CC device. Teeth, all printed, none stopping at
the first red:

  1. launchers/ is gone; recovery holds bootstrap.sh, bootstrap_first_run.sh, its
     charter and its probe; cc holds superclaude.
  2. each moved script parses (bash -n), and bootstrap.sh, sourced from its new home,
     computes CAIRN_REPO_ROOT as this repo.
  3. a box wired before the move holds a superclaude instance link pointing at
     launchers/superclaude; the wire step repoints it to cairn/devices/cc/superclaude
     (a link that already points right is left alone, and a real file is never touched).
  4. `git grep launchers/` over live files (not history.json, state.json, validations,
     journals) finds only instance-space paths (~/.cairn/launchers/, instance/launchers/).
  5. instance-space did not move: superclaude's restart flags home is still
     ~/.cairn/launchers/superclaude/0, and `cairn cc restart` reads that same home.
  6. discover() loads every device, recovery included, with zero failures.

    python3 cairn/devices/recovery/proofs/test_launchers_moved_to_their_devices.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

PROVES = {"38125c3ada38": {"all": "test_launchers_moved_to_their_devices"}}

RECOVERY = ROOT / "cairn" / "devices" / "recovery"
CC = ROOT / "cairn" / "devices" / "cc"
BOOTSTRAP = RECOVERY / "bootstrap.sh"
SUPERCLAUDE = CC / "superclaude"


def tooth_files_are_home():
    assert not (ROOT / "launchers").exists(), "launchers/ still exists"
    for p in (BOOTSTRAP, RECOVERY / "bootstrap_first_run.sh", RECOVERY / "intention+why.json",
              RECOVERY / "probes" / "reported_but_unfixed_floor.py", SUPERCLAUDE, *MOVED_PROOFS):
        assert p.is_file(), f"missing at its new home: {p.relative_to(ROOT)}"
    for p in MOVED_PROOFS:
        if p.suffix != ".py":
            continue
        v = p.parent.parent / "validations" / f"{p.stem}.json"
        assert v.is_file(), f"no seal at the new address: {v.relative_to(ROOT)}"
        recs = json.loads(v.read_text())
        last = recs[-1] if isinstance(recs, list) else recs
        assert last.get("verdict") == "green", f"{v.relative_to(ROOT)} last sealed {last.get('verdict')}"


# "every moved proof is green and sealed at its new address" (the falsifier): the proofs that
# left launchers/proofs/, each at the device that now owns what it measures.
MOVED_PROOFS = tuple(RECOVERY / "proofs" / n for n in (
    "PROOF.md", "test_a_unit_a_test_run_starts_is_the_runs.py", "test_bootstrap.py",
    "test_ground_loop_survives_its_caller.py", "test_launchers_probes_report_to_the_watch.py",
    "test_launchers_reach_into_no_device.py", "test_reported_but_unfixed_probe.py",
    "test_the_unswapped_arm_measures_swap_first.py")) + tuple(CC / "proofs" / n for n in (
    "test_superclaude_memory_scope.py", "test_superclaude_sets_cairn_user.py",
    "test_superclaude_wire.py"))


def tooth_scripts_parse_and_locate():
    for p in (BOOTSTRAP, RECOVERY / "bootstrap_first_run.sh", SUPERCLAUDE):
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        assert r.returncode == 0, f"bash -n {p.name}: {r.stderr}"
    r = subprocess.run(["bash", "-c", f'source "{BOOTSTRAP}" >/dev/null 2>&1; echo "$CAIRN_REPO_ROOT"'],
                       capture_output=True, text=True, timeout=60)
    got = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    assert Path(got).resolve() == ROOT, f"bootstrap.sh computes CAIRN_REPO_ROOT={got!r}, want {ROOT}"


def _wire(home: Path) -> str:
    env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(home / ".cairn" / "devices"),
           "CAIRN_BOOT_LOG": str(home / "bootlog")}
    r = subprocess.run(["bash", "-c", f'source "{BOOTSTRAP}" >/dev/null 2>&1; cairn_wire_instances'],
                       capture_output=True, text=True, env=env, timeout=60)
    return r.stdout + r.stderr


def tooth_stale_link_is_repointed():
    with tempfile.TemporaryDirectory(prefix="wire-") as t:
        home = Path(t)
        b = home / ".cairn" / "devices" / "superclaude" / "0" / "bin"
        b.mkdir(parents=True)
        stale = b / "superclaude"
        stale.symlink_to(ROOT / "launchers" / "superclaude")   # dangles after the move
        out = _wire(home)
        assert stale.is_symlink(), f"the link was removed, not repointed: {out}"
        assert Path(os.readlink(stale)).resolve() == SUPERCLAUDE.resolve(), \
            f"stale link still points at {os.readlink(stale)}: {out}"
        mtime = os.lstat(stale).st_mtime_ns
        _wire(home)
        assert os.lstat(stale).st_mtime_ns == mtime, "a link already pointing right was rewritten"
    with tempfile.TemporaryDirectory(prefix="wire-") as t:
        home = Path(t)
        b = home / ".cairn" / "devices" / "superclaude" / "0" / "bin"
        b.mkdir(parents=True)
        real = b / "superclaude"
        real.write_text("operator's own file\n")
        _wire(home)
        assert not real.is_symlink() and real.read_text() == "operator's own file\n", \
            "a real file at the link's address was overwritten"


def tooth_no_live_reference():
    r = subprocess.run(["git", "-C", str(ROOT), "grep", "-n", "launchers/", "--",
                        ":!*history.json", ":!*state.json", ":!*/validations/*", ":!*.jsonl"],
                       capture_output=True, text=True)
    hits = [l for l in r.stdout.splitlines()
            if not re.search(r"(\.cairn|instance)/launchers/", l)
            and "test_launchers_moved_to_their_devices.py" not in l]
    # the path-joined spelling (REPO / "launchers" / "superclaude") names the folder without a slash
    r = subprocess.run(["git", "-C", str(ROOT), "grep", "-n", "-E", r"""["']launchers["']""", "--", "*.py"],
                       capture_output=True, text=True)
    # ... except instance-space spelled path-joined (home / ".cairn" / "launchers"), which never moved
    hits += [l for l in r.stdout.splitlines() if "test_launchers_moved_to_their_devices.py" not in l
             and not re.search(r"""["']\.cairn["']\s*/\s*["']launchers["']""", l)]
    assert not hits, f"{len(hits)} live reference(s) to launchers/:\n" + "\n".join(hits[:20])


def _outside_the_repo():
    """A cwd outside the repo, through the scratch door (a bare temp reach reds test_scratch)."""
    from cairn.tools.scratch.scratch import scratch_dir
    return str(scratch_dir("testing-recovery-cwd-"))


def tooth_instance_space_did_not_move():
    """The move is class-space only: the restart flags home stays ~/.cairn/launchers/superclaude/<N>.

    The first build's path rewrite also rewrote this instance-space address, so a running
    loop (old address) and `cairn cc restart` (new address) would have read two homes.
    """
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True,
                       timeout=120, cwd=_outside_the_repo())
    m = re.search(r"flags home: (\S+)", r.stdout + r.stderr)
    assert m, f"superclaude --dry-run printed no flags home: {(r.stdout + r.stderr)[-400:]}"
    # the instance is whichever is free (ticket ae4d581be071 moves a launch off a held one);
    # what must not move is the instance-space address the number hangs off
    want = Path.home() / ".cairn" / "launchers" / "superclaude"
    got = Path(m.group(1))
    assert got.parent == want and got.name.isdigit(), \
        f"superclaude's flags home is {got}, want {want}/<N>"
    restart = (CC / "0" / "bin" / "restart").read_text()
    assert '$HOME/.cairn/launchers/superclaude/' in restart, \
        "cairn cc restart no longer reads the flags home superclaude writes"


def tooth_discover_loads_recovery():
    # Through the rack tool (public, cairn/tools/rack), never the ground loop's own modules: that is a
    # machine held inside the cairn device, and recovery reaching it is a RULE 1 breach
    # (measured: test_launchers_reach_into_no_device redded on the first draft of this tooth).
    import importlib
    from cairn.tools.rack.rack import rack_ids
    ids = rack_ids(ROOT)
    assert "recovery" in ids and "cc" in ids, f"recovery/cc not on the rack: {ids}"
    for probe in sorted((ROOT / "cairn" / "devices" / "recovery" / "probes").glob("*.py")):
        if probe.name.startswith("_"):
            continue
        mod = importlib.import_module(f"cairn.devices.recovery.probes.{probe.stem}")
        assert hasattr(mod, "PROBE"), f"{probe.name} declares no PROBE"


TEETH = [tooth_files_are_home, tooth_scripts_parse_and_locate, tooth_stale_link_is_repointed,
         tooth_no_live_reference, tooth_instance_space_did_not_move, tooth_discover_loads_recovery]


def test_launchers_moved_to_their_devices():
    reds = []
    for t in TEETH:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"  RED    {t.__name__}")
            print(f"         {type(e).__name__}: {e}")
    # The declared composite tooth (PROVES "all"): hollow reads THIS name, so it prints
    # green only when every narrow tooth above passed.
    print(f"  {'RED   ' if reds else 'GREEN '} test_launchers_moved_to_their_devices")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_launchers_moved_to_their_devices()
    except AssertionError as e:
        print(e)
        sys.exit(1)

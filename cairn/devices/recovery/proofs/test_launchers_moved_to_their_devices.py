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
              RECOVERY / "probes" / "reported_but_unfixed_floor.py", SUPERCLAUDE):
        assert p.is_file(), f"missing at its new home: {p.relative_to(ROOT)}"


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
    hits += [l for l in r.stdout.splitlines() if "test_launchers_moved_to_their_devices.py" not in l]
    assert not hits, f"{len(hits)} live reference(s) to launchers/:\n" + "\n".join(hits[:20])


def tooth_instance_space_did_not_move():
    """The move is class-space only: the restart flags home stays ~/.cairn/launchers/superclaude/<N>.

    The first build's path rewrite also rewrote this instance-space address, so a running
    loop (old address) and `cairn cc restart` (new address) would have read two homes.
    """
    r = subprocess.run([str(SUPERCLAUDE), "--dry-run"], capture_output=True, text=True,
                       timeout=120, cwd=tempfile.gettempdir())
    m = re.search(r"flags home: (\S+)", r.stdout + r.stderr)
    assert m, f"superclaude --dry-run printed no flags home: {(r.stdout + r.stderr)[-400:]}"
    want = Path.home() / ".cairn" / "launchers" / "superclaude" / "0"
    assert Path(m.group(1)) == want, f"superclaude's flags home is {m.group(1)}, want {want}"
    restart = (CC / "0" / "bin" / "restart").read_text()
    assert '$HOME/.cairn/launchers/superclaude/' in restart, \
        "cairn cc restart no longer reads the flags home superclaude writes"


def tooth_discover_loads_recovery():
    # Through the rack tool (public, cairn/tools/rack), never ground_loop.discovery: that is a
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
            print(f"GREEN {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"RED   {t.__name__}: {e}")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_launchers_moved_to_their_devices()
    except AssertionError as e:
        print(e)
        sys.exit(1)

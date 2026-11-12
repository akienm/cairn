"""Proof: the installer lives in the Recovery device (ticket ce1d61032eff).

The installer is the rescue service's machine, so it berths under the device that holds it:
it moved from the top-level cairn/machines/ into cairn/devices/recovery/machines/installer/. One tooth per
falsifier clause, all printed, none stopping at the first red:

  1. the old dir is gone; the new dir holds installer.py, ask_user.sh, its charter and both
     moved proofs.
  2. git grep for the old dotted and slash spellings over live files (not history.json,
     state.json, validations, journals) finds only the new address.
  3. bin/cmd/install --dry-run exits 0 from the new home, and the module's _REPO holds bin/cairn.
  4. nothing under ~/.cairn outside venvs, logs, mail, notices and chart packets carries the
     old spelling in a path or a live config key.
  5. the device census loads recovery with its installer machine, with zero unreadable rows.

    python3 cairn/devices/recovery/machines/installer/proofs/test_installer_lives_in_recovery.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
assert (ROOT / "bin" / "cairn").exists(), f"ROOT {ROOT} does not hold bin/cairn"

PROVES = {"ce1d61032eff": {
    "1": "tooth_files_are_home",
    "2": "tooth_no_live_reference",
    "3": "tooth_install_runs_from_the_new_home",
    "4": "tooth_instance_space_carries_no_old_path",
    "5": "tooth_census_loads_the_installer",
}}

NEW = ROOT / "cairn" / "devices" / "recovery" / "machines" / "installer"
# Spelled in pieces so this file is not itself a hit for tooth 2.
OLD_DOTTED = "cairn.machines" + ".installer"
OLD_SLASH = "cairn/machines" + "/installer"
NEW_DOTTED = "cairn.devices.recovery.machines.installer"
NEW_SLASH = "cairn/devices/recovery/machines/installer"


def _strip_new(text: str) -> str:
    # Any spelling of the new address, with or without its cairn/ prefix, is the new address.
    return text.replace("recovery.machines.installer", "").replace("recovery/machines/installer", "")


def tooth_files_are_home():
    assert not (ROOT / OLD_SLASH).exists(), f"{OLD_SLASH} still exists"
    for p in (NEW / "installer.py", NEW / "ask_user.sh", NEW / "intention+why.json",
              NEW / "proofs" / "test_installer.py",
              NEW / "proofs" / "test_install_lays_the_journal_merge_driver.py"):
        assert p.is_file(), f"missing at its new home: {p.relative_to(ROOT)}"


def tooth_no_live_reference():
    # The bare spelling too (no cairn. prefix): a relative module path is still the
    # old address. Every hit must be an occurrence of the new address and nothing else.
    out = subprocess.run(
        ["git", "-C", str(ROOT), "grep", "-nE", r"machines[./]installer", "--", ".",
         ":!*history.json", ":!*state.json", ":!*/validations/*", ":!*.jsonl"],
        capture_output=True, text=True)
    assert out.returncode in (0, 1), f"git grep failed: {out.stderr}"
    stale = [ln for ln in out.stdout.splitlines()
             if re.search(r"machines[./]installer", _strip_new(ln.split(":", 2)[-1]))]
    assert not stale, "live files still name the old address:\n  " + "\n  ".join(stale[:20])


def tooth_install_runs_from_the_new_home():
    r = subprocess.run([str(ROOT / "bin" / "cmd" / "install"), "--dry-run"], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"bin/cmd/install --dry-run exit {r.returncode}: {r.stderr[-800:]}"
    from cairn.devices.recovery.machines.installer import installer
    assert Path(installer.__file__).resolve().parent == NEW.resolve(), installer.__file__
    assert (installer._REPO / "bin" / "cairn").exists(), f"_REPO {installer._REPO} holds no bin/cairn"


# History lanes: they record what happened at the old address and are not live config.
_SKIP = {"berths", "activations", "venvs", "venv", ".venv", "logs", "log", "mail", "notices", "packets", "chart_packets",
         "__pycache__", "node_modules", ".git"}
# Live config, not records: a berth or a watch activation is the record of a firing (history), and
# a JSON file is config only when its name says so. Measured 2026-11-12 in the first run: every
# content hit was a skill_block berth or a codemother activation, none a config key.
_CONFIG_SUFFIXES = {".toml", ".cfg", ".ini", ".conf", ".env", ".yaml", ".yml", ".sh", ".service", ""}


def _is_config(p: Path) -> bool:
    if p.suffix == ".json":
        return any(w in p.name for w in ("config", "settings", "wiring"))
    return p.suffix in _CONFIG_SUFFIXES


def tooth_instance_space_carries_no_old_path():
    home = Path(os.environ.get("CAIRN_HOME", Path.home() / ".cairn"))
    if not home.is_dir():
        return  # a box with no instance space carries no old path
    hits = []
    for dirpath, dirnames, filenames in os.walk(home, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP and "packet" not in d]
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if re.search(r"machines[./]installer", _strip_new(str(p))):
                hits.append(f"path: {p}")
            if p.is_symlink() and re.search(r"machines[./]installer",
                                            _strip_new(os.readlink(p))):
                hits.append(f"link: {p} -> {os.readlink(p)}")
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_symlink() or not _is_config(p):
                continue
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if OLD_DOTTED in _strip_new(text) or OLD_SLASH in _strip_new(text):
                hits.append(f"content: {p}")
    assert not hits, "instance space carries the old address:\n  " + "\n  ".join(hits[:20])


def tooth_census_loads_the_installer():
    from cairn.tools.orient.orient import device_census
    c = device_census(root=ROOT / "cairn")["measured"]
    assert not c["unreadable"], f"census unreadable rows: {c['unreadable']}"
    dirs = {row["dir"]: row for row in c["components"]}
    assert "devices/recovery" in dirs, "recovery missing from the census"
    row = dirs.get(NEW_SLASH[len("cairn/"):])
    assert row, f"installer not under recovery: {[d for d in dirs if 'installer' in d]}"
    assert row["charter_on_disk"] and row["proofs"] >= 3, row
    assert OLD_SLASH[len("cairn/"):] not in dirs, "the census still finds the old address"


TEETH = [tooth_files_are_home, tooth_no_live_reference, tooth_install_runs_from_the_new_home,
         tooth_instance_space_carries_no_old_path, tooth_census_loads_the_installer]


def test_installer_lives_in_recovery():
    reds = []
    for t in TEETH:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"  RED    {t.__name__}")
            print(f"         {type(e).__name__}: {e}")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_installer_lives_in_recovery()
    except AssertionError as e:
        print(e)
        sys.exit(1)

"""Proof that the components the outline retires are gone from class-space.

Outline rule 1.3.7: code that is no longer needed is deleted; git history keeps it. A deleted
component cannot hold its own proof, so the retirements berth here, in bin: the surface every
Cairn facility is reached through. Each retirement ticket adds its own PROVES key and teeth.

Ticket 80df7712b8c5 (quarry_index, outline 17.13 / Q#44, Akien 2026-11-06), one tooth per
falsifier clause:

  1. cairn/machines/quarry_index/ is absent from the working tree;
  2. no file in the repo names the module or its folder (records of truth and caches excepted);
  3. the compiler module cannot be loaded: importing it exits nonzero with "No module named"
     (an import, never `-m`, so the red-first run cannot run the compiler).

Ticket 6935a4a71f93 (nothing hangs off the git post-commit hook, outline 9.4.3.3.2; counting_block
also by 17.11.5), one tooth per falsifier clause:

  1. cairn/tools/post_commit/, cairn/machines/counting_block/ and CodeMother's commit feeder
     (post_commit.py, hooks/post-commit, probes/commit_fires_activations.py and
     proofs/test_a_commit_reaches_the_watcher.py) are absent, and git tracks no */hooks/post-commit;
  2. no file in the repo names the three modules or their paths (records and caches excepted);
  3. none of the three modules can be imported;
  4. no post-commit hook is installed in the repo's git common dir (a host-seam: git cannot see it).

Ticket 7778e24dd82e (the instance-izer retires and the bus delivers only to devices, outline 19.16),
one tooth per falsifier clause:

  1. cairn/tools/ + the tool's folder and the bus's folder-mail proof are absent;
  2. no file in the repo names the module, its folder, its declaration file, the bus's three
     folder-delivery names or the address function for folders (records and caches excepted);
  3. the module cannot be imported;
  4. no declaration file stands under the live instance root and its folders/ does not exist
     (instance-space: git cannot see it).

Ticket 6208d0a27d6e (the live-ness tool retires and the ground loop owns its record, Q#53 /
outline 1.2.7, 5.6.3, 5.7.3.5), one tooth per falsifier clause it owns (5-8 berth with the
ground loop and base proofs):

  1. the tool's folder and the ground loop's proof that it reads the tool's cadence are absent;
  2. no file in the repo names the module, its folder, its record read and write, its pane data
     or its staleness threshold (records and caches excepted);
  3. the module cannot be imported;
  4. no record under the tool's name stands in the live ground loop home (instance-space).

Reads only the repo, never CairnCommons (the hollow worktree has none beside it).

    python3 bin/proofs/test_retired_components_are_gone.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

PROVES = {
    "80df7712b8c5": {
        "1": "quarry_index_folder_is_absent",
        "2": "nothing_names_quarry_index",
        "3": "quarry_index_compiler_does_not_import",
    },
    "6935a4a71f93": {
        "1": "post_commit_chain_paths_are_absent",
        "2": "nothing_names_the_post_commit_chain",
        "3": "the_post_commit_chain_does_not_import",
        "4": "no_post_commit_hook_is_installed",
    },
    "7778e24dd82e": {
        "1": "instanceizer_paths_are_absent",
        "2": "nothing_names_the_instanceizer",
        "3": "the_instanceizer_does_not_import",
        "4": "no_declaration_stands_in_instance_space",
    },
    "6208d0a27d6e": {
        "1": "liveness_paths_are_absent",
        "2": "nothing_names_liveness",
        "3": "liveness_does_not_import",
        "4": "no_liveness_record_in_the_ground_loop_home",
    },
}

FAILURES: list[str] = []

# names written split, so this file never matches its own search
_QI_MODULE = "cairn.machines." + "quarry_index"
_QI_PATH = "cairn/machines/" + "quarry_index"


def _check(name: str, ok: bool, detail: str = "") -> None:
    # the label is the tooth's PROVES name: the hollow reading reads green teeth by it
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


_RECORDS = ("history.json", "state.json")


def _naming(needles: tuple[str, ...]) -> list[str]:
    """Repo files whose text holds any needle. Skipped: this proof, __pycache__, egg-info, every
    dot-file and dot-folder (.git, .pytest_cache, .artifact-journal.jsonl), and each component's
    records of truth: history.json, state.json, everything under validations/ (ticket
    80df7712b8c5 FIXME 1) and a stored chart verdict (verdict-*.json, ticket 6208d0a27d6e). Those are append-only records and caches that name what passed
    through, never callers."""
    hits: list[str] = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("__pycache__", "cairn.egg-info", "validations")]
        for f in files:
            if f.startswith(".") or f in _RECORDS or (f.startswith("verdict-") and f.endswith(".json")):
                continue
            p = Path(root) / f
            if p.resolve() == SELF:
                continue
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if any(n in text for n in needles):
                hits.append(str(p.relative_to(REPO)))
    return hits


def _gone(name: str, folder: str, module: str, runnable: str) -> None:
    """The three retirement teeth for one component."""
    p = REPO / folder
    _check(PROVES_NAME[name][0], not p.exists(), f"{folder} still exists")
    hits = _naming((module, folder))
    _check(PROVES_NAME[name][1], not hits, "named by: " + ", ".join(hits[:12]))
    # import, never -m: running the module while it still stands would run it
    r = subprocess.run([sys.executable, "-c", f"import {runnable}"], cwd=REPO,
                       capture_output=True, text=True, timeout=60)
    _check(PROVES_NAME[name][2], r.returncode != 0 and "No module named" in r.stderr,
           f"rc={r.returncode} stderr={r.stderr[-300:]!r}")


# the post-commit chain, spelled split for the same reason
_PC_MODULES = ("cairn.tools." + "post_commit", "cairn.machines." + "counting_block",
               "cairn.devices.codemother." + "post_commit")
_PC_IMPORTS = (_PC_MODULES[0] + ".fanout", _PC_MODULES[1] + ".block", _PC_MODULES[2])
_CM = "cairn/devices/" + "codemother/"
_PC_PATHS = ("cairn/tools/" + "post_commit", "cairn/machines/" + "counting_block",
             _CM + "post_commit" + ".py", _CM + "hooks/post" + "-commit",
             _CM + "probes/commit_fires" + "_activations.py",
             _CM + "proofs/test_a_commit_reaches" + "_the_watcher.py")
_PC_NEEDLES = _PC_MODULES + _PC_PATHS[:2] + (_CM + "post_commit",)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)


def _post_commit_chain() -> None:
    """The four teeth for 6935a4a71f93: nothing hangs off the git post-commit hook."""
    names = PROVES["6935a4a71f93"]
    standing = [p for p in _PC_PATHS if (REPO / p).exists()]
    tracked = [p for p in _git("ls-files", "--", "*/hooks/post-commit").stdout.split() if p]
    _check(names["1"], not standing and not tracked,
           f"standing={standing} tracked_hooks={tracked}")
    hits = _naming(_PC_NEEDLES)
    _check(names["2"], not hits, "named by: " + ", ".join(hits[:12]))
    loads = []
    for mod in _PC_IMPORTS:
        r = subprocess.run([sys.executable, "-c", f"import {mod}"], cwd=REPO,
                           capture_output=True, text=True, timeout=60)
        if not (r.returncode != 0 and "No module named" in r.stderr):
            loads.append(f"{mod}: rc={r.returncode} {r.stderr[-160:]!r}")
    _check(names["3"], not loads, "; ".join(loads))
    common = _git("rev-parse", "--git-common-dir").stdout.strip()
    hook = (REPO / common / "hooks" / "post-commit") if common else None
    _check(names["4"], hook is not None and not hook.exists(),
           f"installed hook at {hook}" if hook else "git rev-parse --git-common-dir answered nothing")


# the instance-izer, spelled split for the same reason
_IZ = "instance" + "izer"
_IZ_MODULE = "cairn.tools." + _IZ
_IZ_PATHS = ("cairn/tools/" + _IZ, "cairn/devices/cairn/machines/bus/proofs/test_folder_mail" + "_lands_late.py")
_IZ_DECL = _IZ + ".json"
_IZ_NEEDLES = (_IZ_MODULE, _IZ_PATHS[0], _IZ_DECL, "_try_folder" + "_delivery", "_instance" + "_folder",
               "_folder" + "_recorders", "address." + "folder_path", "def " + "folder_path")


def _instanceizer() -> None:
    """The four teeth for 7778e24dd82e: only devices are on the bus."""
    names = PROVES["7778e24dd82e"]
    standing = [p for p in _IZ_PATHS if (REPO / p).exists()]
    _check(names["1"], not standing, f"standing={standing}")
    hits = _naming(_IZ_NEEDLES)
    _check(names["2"], not hits, "named by: " + ", ".join(hits[:12]))
    r = subprocess.run([sys.executable, "-c", f"import {_IZ_MODULE}.{_IZ}"], cwd=REPO,
                       capture_output=True, text=True, timeout=60)
    _check(names["3"], r.returncode != 0 and "No module named" in r.stderr,
           f"rc={r.returncode} stderr={r.stderr[-300:]!r}")
    sys.path.insert(0, str(REPO))
    from cairn.tools.base import address
    inst = Path(address.ROOTS["instance"])
    decls = [str(Path(root) / f) for root, _d, files in os.walk(inst) for f in files if f == _IZ_DECL]
    folders = inst / "folders"
    _check(names["4"], not decls and not folders.exists(),
           f"declarations={decls[:6]} folders_root_exists={folders.exists()}")


# the live-ness tool, spelled split for the same reason
_LV = "live" + "ness"
_LV_MODULE = "cairn.tools." + _LV
_LV_PATHS = ("cairn/tools/" + _LV,
             "cairn/devices/cairn/machines/ground_loop/proofs/test_the_ground_loop_reads" + "_the_tools_cadence.py")
_LV_NEEDLES = (_LV_MODULE, _LV_PATHS[0], "read_" + _LV, "write_" + _LV, _LV + "_pane_data",
               "STALENESS" + "_THRESHOLD_S")


def _liveness() -> None:
    """The four teeth for 6208d0a27d6e: the ground loop owns its record; up is its held lock."""
    names = PROVES["6208d0a27d6e"]
    standing = [p for p in _LV_PATHS if (REPO / p).exists()]
    _check(names["1"], not standing, f"standing={standing}")
    hits = _naming(_LV_NEEDLES)
    _check(names["2"], not hits, "named by: " + ", ".join(hits[:12]))
    r = subprocess.run([sys.executable, "-c", f"import {_LV_MODULE}.{_LV}"], cwd=REPO,
                       capture_output=True, text=True, timeout=60)
    _check(names["3"], r.returncode != 0 and "No module named" in r.stderr,
           f"rc={r.returncode} stderr={r.stderr[-300:]!r}")
    sys.path.insert(0, str(REPO))
    from cairn.tools.base import address
    record = (Path(address.ROOTS["instance"]) / "devices" / "cairn" / "0" / "machines"
              / "ground_loop" / (_LV + ".json"))
    _check(names["4"], not record.exists(), f"{record} still stands")


PROVES_NAME = {
    "quarry_index": [PROVES["80df7712b8c5"][k] for k in ("1", "2", "3")],
}


def check() -> list[str]:
    FAILURES.clear()
    _gone("quarry_index", _QI_PATH, _QI_MODULE, _QI_MODULE + ".compiler")
    _post_commit_chain()
    _instanceizer()
    _liveness()
    return list(FAILURES)


def main() -> int:
    fails = check()
    print(f"retired components proofs: {'all green' if not fails else f'{len(fails)} red'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

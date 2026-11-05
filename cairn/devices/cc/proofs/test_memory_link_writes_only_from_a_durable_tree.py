#!/usr/bin/env python3
"""Proof that memory_link writes nothing into ~/.claude from a transient tree (ticket 089ad920fcc5).

Measured 2026-11-05 (Akien's Stop-hook error): ~/.claude/settings.json's SessionStart and Stop
hooks named memory_sync.py inside a deleted hollow worktree under /tmp, and six
~/.claude/projects/-tmp-cairn-hollow-scratch-* folders held memory links. A proof launched
superclaude with the live HOME; superclaude runs memory_link from its own tree, and memory_link
writes its own path into the hooks. The guard sits at the writer, so no caller has to remember.

One tooth, run three ways over a COPY of the script under a scratch HOME (never the live one):
  (1) the script's tree under the transient root: no settings.json is written;
  (2) nothing under the transient root: both hooks name the copy's memory_sync.py, and the
      launch folder's memory links to the clone — the guard is not "never write";
  (3) the launch folder under the transient root: no link is made for it.

    PYTHONPATH=. python3 cairn/devices/cc/proofs/test_memory_link_writes_only_from_a_durable_tree.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_SCRIPTS = _REPO / "cairn" / "devices" / "cc" / "scripts"

PROVES = {"089ad920fcc5": {
    "1": "test_memory_link_writes_only_from_a_durable_tree",
    "2": "test_memory_link_writes_only_from_a_durable_tree",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _slug(folder: Path) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "-", str(folder.resolve()))


def _run(script: Path, home: Path, clone: Path, launch: Path, transient: Path) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CAIRN_CC_MEMORY")}
    env.update({"HOME": str(home), "USERPROFILE": str(home),
                "CAIRN_CC_MEMORY_TRANSIENT_ROOT": str(transient)})
    home.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(script), "--clone", str(clone), str(launch)],
                       env=env, capture_output=True, text=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    return f"rc={r.returncode} out={r.stdout.strip()!r} err={r.stderr.strip()!r}"


def test_memory_link_writes_only_from_a_durable_tree() -> None:
    lacks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="memlink-proof-") as d:
        s = Path(d).resolve()
        scripts = s / "tree" / "cairn" / "devices" / "cc" / "scripts"
        scripts.mkdir(parents=True)
        for name in ("memory_link.py", "memory_sync.py"):
            shutil.copy2(_SCRIPTS / name, scripts / name)
        script, sync = scripts / "memory_link.py", (scripts / "memory_sync.py").as_posix()
        clone, launch = s / "clone", s / "launch"
        (clone / ".git").mkdir(parents=True)
        launch.mkdir()

        # (1) the script's own tree is transient: nothing lands in settings.json.
        h1 = s / "home1"
        said = _run(script, h1, clone, launch, s / "tree")
        if (h1 / ".claude" / "settings.json").exists():
            lacks.append(f"run 1 (script under the transient root) wrote settings.json: "
                         f"{(h1 / '.claude' / 'settings.json').read_text()[:300]} [{said}]")

        # (2) nothing transient: both hooks name the copy, and the launch folder links.
        h2 = s / "home2"
        said = _run(script, h2, clone, launch, s / "elsewhere")
        settings = h2 / ".claude" / "settings.json"
        if not settings.exists():
            lacks.append(f"run 2 (nothing transient) wrote no settings.json [{said}]")
        else:
            hooks = json.loads(settings.read_text()).get("hooks", {})
            for event, verb in (("SessionStart", "pull"), ("Stop", "push")):
                cmds = [x.get("command", "") for h in hooks.get(event, []) for x in h.get("hooks", [])]
                if not any(sync in c and f" {verb} " in c for c in cmds):
                    lacks.append(f"run 2: {event} has no {verb} hook naming {sync}: {cmds}")
        mem = h2 / ".claude" / "projects" / _slug(launch) / "memory"
        if not (mem.is_symlink() and mem.resolve() == clone):
            lacks.append(f"run 2: {mem} is not a link to {clone} [{said}]")

        # (3) the launch folder is transient: no link is made for it.
        h3 = s / "home3"
        said = _run(script, h3, clone, launch, s)
        mem3 = h3 / ".claude" / "projects" / _slug(launch) / "memory"
        if mem3.exists() or mem3.is_symlink():
            lacks.append(f"run 3 (launch folder under the transient root) linked {mem3} [{said}]")

    check("test_memory_link_writes_only_from_a_durable_tree", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    try:
        test_memory_link_writes_only_from_a_durable_tree()
    except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
        check("test_memory_link_writes_only_from_a_durable_tree", False,
              f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

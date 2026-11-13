"""bin/cairn's floor links a class verb that landed after the box's first wiring walk.

Measured 2026-11-12 (ticket 96c1c2ea5ce9): on akienasus every ~/.cairn/devices/*/0/bin link was
laid at one moment (2026-11-11 15:29:12, the reinstall's first walk); web_server's was laid by
hand on 11-12, and librarian/0/bin/question — a class verb that landed 11-12 — had no instance
link at all. On akiendelllinux web_server's absence redded cairn/tools/base/proofs/test_cli_reaches.py.
The cause: the floor ran cairn_wire_instances only when cairn/0 was absent or the superclaude
launcher was not executable, so after the first walk nothing linked a new verb.

PROVES (teeth below):
  (1) with cairn/0 and the superclaude launcher present and a class verb's instance link absent,
      one bin/cairn run links that verb to its class file;
  (2) a hand-placed real file at a class verb's instance address is left untouched by that run.

Every tooth runs under a scratch instance root, a scratch socket dir and a stand-in `sudo` (the
env of bin/proofs/test_superclaude_is_never_refused_by_the_floor.py), so the live instance, venv,
db and host are never touched.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import sys
_REPO_FOR_ARGV = Path(__file__).resolve().parents[2]
if str(_REPO_FOR_ARGV) not in sys.path:
    sys.path.insert(0, str(_REPO_FOR_ARGV))
from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAIRN = ROOT / "bin" / "cairn"
CLASS = ROOT / "cairn" / "devices"

PROVES = {"96c1c2ea5ce9": {
    "1": "test_a_late_verb_is_linked_by_the_next_run",
    "2": "test_a_hand_placed_file_is_left_as_it_was",
}}

_failures: list[str] = []


def _scratch() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("floor-links-late-verb-")


def _env(home: Path) -> dict:
    d = home / "fakebin"
    d.mkdir(exist_ok=True)
    (d / "sudo").write_text("#!/bin/sh\necho 'sudo: a password is required' >&2\nexit 1\n")
    (d / "sudo").chmod(0o755)
    # the box owns its bus (FIXME 1, 2026-11-13): no CAIRN_BUS_* rides in from the caller, so a
    # scratch box never dials a far or live bus (the other-root eviction 50ca14d4489e measured)
    env = {k: v for k, v in os.environ.items() if not k.startswith("CAIRN_BUS_")}
    env["CAIRN_BUS_HOME"] = str(home / "bus")
    env["PATH"] = f"{d}:{env.get('PATH', '')}"
    env["CAIRN_INSTANCE_ROOT"] = str(home / "devices")
    env.setdefault("CAIRN_VENV", str(Path.home() / ".cairn" / "venv"))
    (home / "nosock").mkdir(exist_ok=True)
    env["CAIRN_PG_SOCKET_DIR"] = str(home / "nosock")
    env["CAIRN_BOOT_LOG"] = str(home / "boot")
    for k in ("CAIRN_SUDO_PW", "SUDO_ASKPASS", "CAIRN_FLOOR_FINDINGS", "CAIRN_CLASS_ROOT"):
        env.pop(k, None)
    return env


def _run(env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([*bash_script_argv(CAIRN), "superclaude", "--dry-run"], env=env, capture_output=True,
                          text=True, timeout=300, cwd="/", stdin=subprocess.DEVNULL)


def _wired_box() -> tuple[Path, dict]:
    """A scratch box past its first walk: cairn/0 made by another writer, then one launch lays all."""
    home = _scratch()
    (home / "devices" / "cairn" / "0").mkdir(parents=True)
    env = _env(home)
    r = _run(env)
    assert r.returncode == 0, f"first launch rc={r.returncode} err={r.stderr[-300:]!r}"
    assert (home / "devices" / "superclaude" / "0" / "bin" / "superclaude").exists(), "superclaude unwired"
    return home, env


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def _late(home: Path, device: str, verb: str) -> tuple[Path, Path]:
    cls = CLASS / device / "0" / "bin" / verb
    assert cls.is_file() and os.access(cls, os.X_OK), f"{cls} is no executable class verb — vacuous"
    at = home / "devices" / device / "0" / "bin" / verb
    assert at.is_symlink(), f"the first walk laid no link at {at} — vacuous"
    at.unlink()  # the verb "lands late": its instance link is absent on a box already walked
    return cls, at


def test_a_late_verb_is_linked_by_the_next_run() -> None:
    home, env = _wired_box()
    cls, at = _late(home, "web_server", "web_server")
    r = _run(env)
    check("test_a_late_verb_is_linked_by_the_next_run",
          r.returncode == 0 and at.is_symlink() and at.resolve() == cls.resolve(),
          f"rc={r.returncode} linked={at.is_symlink()} err={r.stderr[-300:]!r}")


def test_a_hand_placed_file_is_left_as_it_was() -> None:
    home, env = _wired_box()
    _late(home, "web_server", "web_server")  # a real gap, so the walk must run over the hand file
    _, hand = _late(home, "librarian", "question")
    body = b"#!/bin/sh\necho placed by hand\n"
    hand.write_bytes(body)
    r = _run(env)
    ws = home / "devices" / "web_server" / "0" / "bin" / "web_server"
    check("test_a_hand_placed_file_is_left_as_it_was",
          r.returncode == 0 and ws.is_symlink() and not hand.is_symlink() and hand.read_bytes() == body,
          f"rc={r.returncode} walk_ran={ws.is_symlink()} hand_is_link={hand.is_symlink()}")


def main() -> int:
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(name, False, f"raised {type(exc).__name__}: {exc}")
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

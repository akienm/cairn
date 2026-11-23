#!/usr/bin/env python3
"""Proof for ticket 0b7a3f1d53f0: bin/cairn.py dispatches `superclaude` to cairn/devices/cc/superclaude.py
and runs it in the dispatcher's own console.

Measured 2026-11-22 on akiendell: `cairn superclaude` ran the bash launcher (WSL's bash.exe, exit 127),
and _run starts every verb with CREATE_NO_WINDOW, which gives an interactive claude a hidden console.

  1. _wire_instances over scratch roots links cc/superclaude.py as <instance>/superclaude/0/bin/superclaude,
     replaces a link or a copy of the bash, and _wiring_gap names a stale entry until it is wired.
  2. _run on that verb calls subprocess.call with [sys.executable, <the file>] and no creationflags, stdin,
     stdout or stderr keyword, while another verb keeps the windowless keywords.
  3. A script with a shell shebang, with no shell on PATH, returns 126 naming the script.

bin/cairn.py is loaded from its file with CAIRN_CLASS_ROOT and CAIRN_INSTANCE_ROOT pointing at a scratch
tree, so nothing under ~/.cairn is touched.

    python3 bin/proofs/test_cairn_dispatches_superclaude_py.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

PROVES = {"0b7a3f1d53f0": {
    "1": "test_wiring_lays_the_python_launcher_and_replaces_the_bash",
    "2": "test_superclaude_runs_in_this_console_and_other_verbs_stay_windowless",
    "3": "test_a_shell_script_with_no_shell_is_refused_126_by_name",
}}

BASH_TEXT = "#!/usr/bin/env bash\necho the bash launcher\n"
PY_TEXT = "#!/usr/bin/env python3\nprint('the python launcher')\n"


@contextlib.contextmanager
def _fixture():
    with tempfile.TemporaryDirectory(prefix="cairn-dispatch-") as d:
        root = Path(d)
        cc = root / "class" / "cc"
        cc.mkdir(parents=True)
        (cc / "superclaude").write_text(BASH_TEXT, encoding="utf-8", newline="\n")
        (cc / "superclaude.py").write_text(PY_TEXT, encoding="utf-8", newline="\n")
        saved = {k: os.environ.get(k) for k in ("CAIRN_CLASS_ROOT", "CAIRN_INSTANCE_ROOT")}
        os.environ["CAIRN_CLASS_ROOT"] = str(root / "class")
        os.environ["CAIRN_INSTANCE_ROOT"] = str(root / "inst")
        try:
            spec = importlib.util.spec_from_file_location("cairn_bin_under_proof", REPO / "bin" / "cairn.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            yield mod, root
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def _entry(root: Path) -> Path:
    return root / "inst" / "superclaude" / "0" / "bin" / "superclaude"


def _is_the_py(entry: Path, root: Path) -> bool:
    py = root / "class" / "cc" / "superclaude.py"
    if entry.is_symlink():
        return entry.resolve() == py.resolve()
    return entry.is_file() and entry.read_bytes() == py.read_bytes()


def test_wiring_lays_the_python_launcher_and_replaces_the_bash():
    with _fixture() as (cairn, root):
        cairn._wire_instances()
        assert _is_the_py(_entry(root), root), "the verb superclaude does not point at superclaude.py"
        assert not cairn._wiring_gap(), "a wired box still reports a wiring gap"
        # a stale copy of the bash is replaced
        at = _entry(root)
        if at.is_symlink():
            at.unlink()
        else:
            at.unlink()
        at.write_bytes((root / "class" / "cc" / "superclaude").read_bytes())
        assert cairn._wiring_gap(), "a copy of the bash is a wiring gap and was not named"
        cairn._wire_instances()
        assert _is_the_py(_entry(root), root), "a copy of the bash was left standing"
        assert not cairn._wiring_gap()
        # a stale link at the bash is repointed
        at.unlink()
        try:
            os.symlink(root / "class" / "cc" / "superclaude", at)
        except OSError:
            return
        assert cairn._wiring_gap(), "a link at the bash is a wiring gap and was not named"
        cairn._wire_instances()
        assert _is_the_py(_entry(root), root), "a link at the bash was not repointed"


def test_superclaude_runs_in_this_console_and_other_verbs_stay_windowless():
    with _fixture() as (cairn, root):
        cairn._wire_instances()
        other = root / "inst" / "other" / "0" / "bin"
        other.mkdir(parents=True)
        (other / "other").write_text(PY_TEXT, encoding="utf-8", newline="\n")
        seen = []

        def fake_call(argv, **kw):
            seen.append((list(argv), dict(kw)))
            return 0

        cairn.subprocess.call = fake_call
        assert cairn._run(_entry(root), ["--dry-run"]) == 0
        argv, kw = seen[-1]
        assert argv[0] == sys.executable and argv[-1] == "--dry-run", argv
        assert Path(argv[1]).read_bytes() == (root / "class" / "cc" / "superclaude.py").read_bytes(), argv
        assert kw == {}, f"superclaude was spawned with {sorted(kw)}: it must inherit this console"
        assert cairn._run(other / "other", []) == 0
        assert seen[-1][1] == cairn.windowless_kwargs(given=()), "another verb lost its windowless keywords"
        assert "stdout" not in seen[0][1] and "creationflags" not in seen[0][1]


def test_a_shell_script_with_no_shell_is_refused_126_by_name():
    with _fixture() as (cairn, root):
        script = root / "class" / "cc" / "superclaude"
        said = []
        cairn.shutil.which = lambda name, *a, **k: None
        cairn._say = said.append
        cairn.subprocess.call = lambda *a, **k: (_ for _ in ()).throw(AssertionError("a shell script was spawned"))
        assert cairn._run(script, []) == 126
        assert any(script.name in m for m in said), said


TEETH = [test_wiring_lays_the_python_launcher_and_replaces_the_bash,
         test_superclaude_runs_in_this_console_and_other_verbs_stay_windowless,
         test_a_shell_script_with_no_shell_is_refused_126_by_name]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

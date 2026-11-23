"""Proof of the class_verbs_are_executable sieve (ticket edea73e1b281).

Measured 2026-11-23 on akiendelllinux: 60de22e64, a build made on Windows, created
cairn/devices/cc/superclaude.py as 100644. The floor (bin/cairn.py _wire_instances) links it as the
live superclaude verb, the dispatch refuses a file without the exec bit, and `cairn superclaude`
answered 127 for ten hours. A script born on Windows lands 100644 because Windows has no exec bit.

  1. A device whose x/0/bin/v is git mode 100644 reads one finding naming the path and 100644.
  2. The same repo with v at 100755 reads none.
  3. cc's superclaude.py at 100644 reds cc's row the same way.
  4. The sieve is registered in SIEVES and has its descriptor under sieves/.

Every mode is set with ``git update-index --add --chmod=±x``, never chmod: on Windows core.fileMode is
false, so a chmod'd file reads 100644 and a tooth goes hollow. The proof builds scratch repos through
the scratch door and never reads the house's index.

    python3 cairn/devices/codemother/machines/build_inspector/proofs/test_class_verbs_are_executable.py
"""
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


class _Late:
    """Names resolved AT CALL TIME so a hollow revert of inspector.py reads red tooth by tooth."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.devices.codemother.machines.build_inspector.inspector")
_HERE = Path(__file__).resolve().parents[1]

PROVES = {"edea73e1b281": {"1": "a_verb_at_100644_reads_a_finding_naming_path_and_mode",
                           "2": "the_same_verb_at_100755_reads_no_finding",
                           "3": "cc_superclaude_at_100644_reds_cc_the_same_way",
                           "4": "the_sieve_is_registered_and_has_its_descriptor"}}

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 -- a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _repo(files: dict[str, str]) -> Path:
    """A scratch git repo; ``files`` maps path -> '644' | '755'. The mode is set in the INDEX."""
    root = Path(scratch_dir("class_verbs_fixture_"))
    _git(root, "init", "-q")
    for rel, mode in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#!/bin/sh\ntrue\n", encoding="utf-8", newline="\n")
        _git(root, "update-index", "--add", f"--chmod={'+x' if mode == '755' else '-x'}", rel)
    return root


def _sieve(root: Path, device: str) -> list[dict]:
    comp_dir = root / "cairn" / "devices" / device
    comp_dir.mkdir(parents=True, exist_ok=True)
    row = {"component": f"cairn/devices/{device}", "dir": f"devices/{device}"}
    return _inspector.class_verbs_are_executable(row, comp_dir)


def a_verb_at_100644_reads_a_finding_naming_path_and_mode():
    root = _repo({"cairn/devices/x/0/bin/v": "644"})
    got = _sieve(root, "x")
    assert len(got) == 1, got
    about = got[0]["about"]
    assert "cairn/devices/x/0/bin/v" in about and "100644" in about, about
    assert got[0]["method"] == "class_verbs_are_executable", got[0]


def the_same_verb_at_100755_reads_no_finding():
    root = _repo({"cairn/devices/x/0/bin/v": "755"})
    got = _sieve(root, "x")
    assert got == [], got
    mixed = _repo({"cairn/devices/x/0/bin/ok": "755", "cairn/devices/x/0/bin/bad": "644"})
    got = _sieve(mixed, "x")
    assert len(got) == 1 and "bin/bad" in got[0]["about"], got


def cc_superclaude_at_100644_reds_cc_the_same_way():
    root = _repo({"cairn/devices/cc/superclaude.py": "644"})
    got = _sieve(root, "cc")
    assert len(got) == 1 and "cairn/devices/cc/superclaude.py" in got[0]["about"] \
        and "100644" in got[0]["about"], got
    root = _repo({"cairn/devices/cc/superclaude.py": "755"})
    assert _sieve(root, "cc") == []
    other = _repo({"cairn/devices/y/superclaude.py": "644"})
    assert _sieve(other, "y") == [], "only cc's row carries superclaude.py"


def the_sieve_is_registered_and_has_its_descriptor():
    assert "class_verbs_are_executable" in _inspector.SIEVES
    d = json.loads((_HERE / "sieves" / "class_verbs_are_executable.json").read_text(encoding="utf-8"))
    assert d["name"] == "class_verbs_are_executable" and d["band_name"] == "record", d


TEETH = [a_verb_at_100644_reads_a_finding_naming_path_and_mode,
         the_same_verb_at_100755_reads_no_finding,
         cc_superclaude_at_100644_reds_cc_the_same_way,
         the_sieve_is_registered_and_has_its_descriptor]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

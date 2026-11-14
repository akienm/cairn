"""Proof of the every_spawn_site_takes_the_helper sieve: every spawn site in cairn/ takes its Popen
keywords from windowless_spawn and builds no flag by hand.

Before 2026-11-14 the repo-wide form of this check sat in windowless_spawn's own proofs, which
scanned every component's code (RULE 1: a ticket's proofs measure only its own component). The
tool now proves its scanner over fixtures, and this sieve keeps the whole-tree coverage.

Each tooth builds its own fixture tree through the scratch door. The sieve is bound at call time
(_Late), so a hollow revert of inspector.py reds tooth by tooth instead of dying at import. The
last tooth runs the sieve over every live component row.

    python3 cairn/machines/build_inspector/proofs/test_every_spawn_site_takes_the_helper.py   # exit 0 = green
"""
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


class _Late:
    """The build's names are resolved AT CALL TIME, never bound at import."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {"ad42bd1e7476": {
    "1": "a_hand_built_site_reds_on_its_components_row",
    "2": "a_helped_site_and_a_proof_read_clean",
    "3": "a_nested_components_site_is_its_own_row",
    "4": "every_live_component_takes_the_helper",
}}

SIEVE = "every_spawn_site_takes_the_helper"
PASS = 0
FAIL = 0
_TMP: list[str] = []

_CHARTER = json.dumps({"what": "a fixture component", "why": "a fixture component"})
_HELPED = ("from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs\n"
           "import subprocess\nsubprocess.Popen(['a'], **detached_kwargs())\n")
_HAND = "import subprocess\nsubprocess.Popen(['a'], creationflags=subprocess.CREATE_NO_WINDOW)\n"


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _tree(files: dict[str, str]) -> Path:
    root = Path(str(scratch_dir("spawn_site_fixture_")))
    _TMP.append(str(root))
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def _judge(root: Path, component_dir: str) -> list[dict]:
    row = {"dir": component_dir, "component": Path(component_dir).name}
    return _inspector.run_sieve(SIEVE, row, root / "cairn" / component_dir)


def a_hand_built_site_reds_on_its_components_row():
    root = _tree({"cairn/tools/t/intention+why.json": _CHARTER, "cairn/tools/t/hand.py": _HAND})
    found = _judge(root, "tools/t")
    assert found, "a hand-built CREATE_NO_WINDOW read clean"
    assert all(f["method"] == SIEVE and f["component"] == "t" for f in found), found
    assert {f["values"]["file"] for f in found} == {"cairn/tools/t/hand.py"}, found
    assert any("hand-builds CREATE_NO_WINDOW" in f["about"] for f in found), found
    assert any("without taking keywords from the helper" in f["about"] for f in found), found


def a_helped_site_and_a_proof_read_clean():
    root = _tree({"cairn/tools/t/intention+why.json": _CHARTER, "cairn/tools/t/ok.py": _HELPED,
                  "cairn/tools/t/proofs/test_x.py": _HAND})
    assert _judge(root, "tools/t") == [], _judge(root, "tools/t")


def a_nested_components_site_is_its_own_row():
    root = _tree({"cairn/devices/d/intention+why.json": _CHARTER,
                  "cairn/devices/d/ok.py": _HELPED,
                  "cairn/devices/d/machines/m/intention+why.json": _CHARTER,
                  "cairn/devices/d/machines/m/hand.py": _HAND})
    holder = _judge(root, "devices/d")
    assert holder == [], f"the holder was charged with its nested machine's site: {holder}"
    nested = _judge(root, "devices/d/machines/m")
    assert {f["values"]["file"] for f in nested} == {"cairn/devices/d/machines/m/hand.py"}, nested
    assert all(f["component"] == "m" for f in nested), nested


def every_live_component_takes_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    cairn = _REPO_ROOT / "cairn"
    rows = sorted(p.parent for p in cairn.rglob("intention+why.json")
                  if "proofs" not in p.relative_to(cairn).parts)
    assert len(rows) > 20, f"only {len(rows)} live component rows: the live tooth would be hollow"
    found = []
    for d in rows:
        found += _judge(_REPO_ROOT, d.relative_to(cairn).as_posix())
    assert not found, "\n".join(f["about"] for f in found)
    # whole-tree coverage: no site the scanner sees sits outside every row
    assert unhelped_sites(_REPO_ROOT) == [], unhelped_sites(_REPO_ROOT)
    print(f"    (live: {len(rows)} component rows, no spawn site builds its own flags)")


TEETH = [a_hand_built_site_reds_on_its_components_row, a_helped_site_and_a_proof_read_clean,
         a_nested_components_site_is_its_own_row, every_live_component_takes_the_helper]


if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

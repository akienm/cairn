"""Proof (import_sieve, measured 2026-11-14 on Windows): the sieve names modules and devices by the graph's own '/' keys on every box.

``module_name`` and the device_isolation sieve split a graph key on ``os.sep``, but ``import_graph`` always spells its keys with
'/', so on Windows every module name stayed one slash-bearing token, no import ever matched a module, and ``reaches()`` answered an
empty closure for every start. Every sieve built on it (unreachable, fire_path_unreachable, importers_of, device_isolation) then read
green by vacuity: 9 of this component's own 35 teeth were red on Windows and nobody saw it, because the walk it fails is the walk that
returns nothing. These teeth read no OS feature, so they run on any box.

    python <this file>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.import_sieve import sieve  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "bd008e7e9084": {
        "1": "a_module_name_agrees_for_a_slash_and_a_backslash_spelling",
        "2": "reaches_is_not_empty_for_a_known_start_over_a_real_tree",
        "3": "a_walk_over_a_graph_that_resolves_none_of_its_own_imports_is_loud_not_green",
    },
}


def a_module_name_agrees_for_a_slash_and_a_backslash_spelling() -> None:
    for spelling in ("cairn/tools/base/probe.py", "cairn\\tools\\base\\probe.py"):
        assert sieve.module_name(spelling) == "cairn.tools.base.probe", f"{spelling!r} -> {sieve.module_name(spelling)!r}"
    for spelling in ("cairn/tools/base/__init__.py", "cairn\\tools\\base\\__init__.py"):
        assert sieve.module_name(spelling) == "cairn.tools.base", f"{spelling!r} -> {sieve.module_name(spelling)!r}"


def reaches_is_not_empty_for_a_known_start_over_a_real_tree() -> None:
    tmp = Path(str(scratch_dir("import_sieve_os_sep_")))
    try:
        (tmp / "a").mkdir()
        (tmp / "a" / "start.py").write_text("import a.mid\n", encoding="utf-8", newline="\n")
        (tmp / "a" / "mid.py").write_text("import a.leaf\n", encoding="utf-8", newline="\n")
        (tmp / "a" / "leaf.py").write_text("import json\n", encoding="utf-8", newline="\n")
        graph = sieve.import_graph(str(tmp))
        assert "a/start.py" in graph, f"import_graph keys are not '/'-spelled: {sorted(graph)}"
        got = sieve.reaches(graph, "a/start.py")
        assert set(got) == {"a/mid.py", "a/leaf.py"}, f"the closure over a real tree on this box is {sorted(got)}"
        assert got["a/leaf.py"] == ["a/start.py", "a/mid.py", "a/leaf.py"], got
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_walk_over_a_graph_that_resolves_none_of_its_own_imports_is_loud_not_green() -> None:
    # 30 files each importing an in-tree name that is no file: not one edge resolves, which is what the os.sep defect looked like
    hollow = {f"cairn/m{i}.py": {f"cairn.missing{i}"} for i in range(30)}
    try:
        sieve.reaches(hollow, "cairn/m0.py")
    except sieve.HollowScan as e:
        assert "resolved" in str(e), e
    else:
        raise AssertionError("a walk over a graph that resolves none of its in-tree imports answered, and would read as clean")
    # and the ordinary dead end stays quiet: one start importing a name nobody scanned, in a graph whose other edges resolve
    ok = {f"cairn/m{i}.py": {f"cairn.m{i + 1}"} for i in range(29)}
    ok["cairn/m29.py"] = {"json", "cairn.denied.door"}
    assert sieve.reaches(ok, "cairn/m28.py") == {"cairn/m29.py": ["cairn/m28.py", "cairn/m29.py"]}


TEETH = [a_module_name_agrees_for_a_slash_and_a_backslash_spelling,
         reaches_is_not_empty_for_a_known_start_over_a_real_tree,
         a_walk_over_a_graph_that_resolves_none_of_its_own_imports_is_loud_not_green]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:300]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

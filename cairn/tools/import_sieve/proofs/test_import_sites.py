"""Proof for import_sieve.import_sites — where an import LANDS, and on which line.

import_graph answers "what names does this file write"; that is enough for a stdlib rule
and not enough for RULE 1 (ticket 8e3474a6ae43), whose question is "which component's
file does this import execute". The six teeth are the falsifier's six clauses, each over
a scratch tree so the answer is known before the scan runs:

  1. `from p import m` with m a MODULE lands on p/m.py, not on the package;
  2. `from p import X` with X a NAME lands on p/__init__.py;
  3. a relative import resolves against the importing file's package;
  4. a literal importlib.import_module("p.m") is a site, kind 'dynamic';
  5. a computed import_module(x) is RETURNED as opaque — never silently dropped,
     because a dropped site reads exactly like an import that was never written;
  6. a stdlib import lands on nothing in the tree and is not returned.

    python3 cairn/tools/import_sieve/proofs/test_import_sites.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir

# The falsifier's six numbered clauses, one tooth each (ticket a907458344ba).
PROVES = {
    "a907458344ba": {
        "1": "test_from_import_of_a_module_lands_on_the_submodule",
        "2": "test_from_import_of_a_name_lands_on_the_package",
        "3": "test_relative_imports_resolve_against_the_package",
        "4": "test_a_literal_import_module_is_a_dynamic_site",
        "5": "test_a_computed_import_module_is_returned_opaque",
        "6": "test_a_stdlib_import_is_not_a_site",
    },
}


def _tree(files: dict[str, str]) -> str:
    root = str(scratch_dir("encapsulation_fixture_import_sites_"))
    for rel, src in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
    return root


def _sites(root: str, file: str) -> list[dict]:
    # Through the package's public face (RULE 1), resolved at call time: with the build taken
    # away the import fails INSIDE the tooth, so every tooth reports red instead of the whole
    # proof dying at import — the hollow check needs to see a tooth red, not a crash.
    from cairn.tools.import_sieve import import_sites
    return [s for s in import_sites(root) if s["file"] == file]


def test_from_import_of_a_module_lands_on_the_submodule():
    root = _tree({"p/__init__.py": "", "p/m.py": "", "a.py": "from p import m\n"})
    sites = _sites(root, "a.py")
    assert sites == [{"file": "a.py", "line": 1, "module": "p.m",
                      "target": os.path.join("p", "m.py"), "kind": "from"}], sites


def test_from_import_of_a_name_lands_on_the_package():
    root = _tree({"p/__init__.py": "X = 1\n", "a.py": "from p import X\n"})
    sites = _sites(root, "a.py")
    assert len(sites) == 1, sites
    assert sites[0]["module"] == "p", sites
    assert sites[0]["target"] == os.path.join("p", "__init__.py"), sites


def test_relative_imports_resolve_against_the_package():
    root = _tree({"p/__init__.py": "", "p/q.py": "Y = 1\n",
                  "p/r.py": "from . import q\nfrom .q import Y\n"})
    sites = _sites(root, os.path.join("p", "r.py"))
    by_line = {s["line"]: s for s in sites}
    assert set(by_line) == {1, 2}, sites
    for line in (1, 2):
        assert by_line[line]["target"] == os.path.join("p", "q.py"), sites
        assert by_line[line]["module"] == "p.q", sites


def test_a_literal_import_module_is_a_dynamic_site():
    root = _tree({"p/__init__.py": "", "p/m.py": "",
                  "a.py": 'import importlib\nimportlib.import_module("p.m")\n'})
    sites = [s for s in _sites(root, "a.py") if s["line"] == 2]
    assert len(sites) == 1, sites
    assert sites[0]["kind"] == "dynamic", sites
    assert sites[0]["target"] == os.path.join("p", "m.py"), sites


def test_a_computed_import_module_is_returned_opaque():
    root = _tree({"a.py": "import importlib\nimportlib.import_module(name)\n"})
    sites = [s for s in _sites(root, "a.py") if s["line"] == 2]
    assert sites == [{"file": "a.py", "line": 2, "module": None,
                      "target": None, "kind": "opaque"}], sites


def test_a_stdlib_import_is_not_a_site():
    root = _tree({"a.py": "import os, json\nfrom collections import deque\n"})
    assert _sites(root, "a.py") == [], _sites(root, "a.py")


def _main() -> int:
    checks = [
        test_from_import_of_a_module_lands_on_the_submodule,
        test_from_import_of_a_name_lands_on_the_package,
        test_relative_imports_resolve_against_the_package,
        test_a_literal_import_module_is_a_dynamic_site,
        test_a_computed_import_module_is_returned_opaque,
        test_a_stdlib_import_is_not_a_site,
    ]
    failed = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:              # noqa: BLE001 — every tooth reports, none hides the next
            failed += 1
            print(f"  RED   {check.__name__}: {type(exc).__name__}: {exc}")
    if failed:
        print(f"red — import_sites: {failed} of {len(checks)} teeth")
        return 1
    print(f"green — import_sites: {len(checks)} teeth; an import resolves to the file it "
          "executes, a computed one is named opaque, and the stdlib is not the tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

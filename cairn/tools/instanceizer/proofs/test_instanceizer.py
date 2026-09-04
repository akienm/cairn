#!/usr/bin/env python3
"""Proof for cairn/tools/instanceizer — the class-space/instance-space bridge.

TEETH A HOLLOW BUILD COULD NOT PASS (Law 8):

  1. MISSING DECLARATION IS LOUD. load() on a folder with no instanceizer.json
     must raise FileNotFoundError, not silently return None — a silent None
     routes bus delivery into nothing.

  2. LOAD INSTANTIATES THE DECLARED CLASS. A valid declaration names a class
     load() can import and instantiate with the declared config. The returned
     object is an instance of that class.

  3. CONFIG IS FORWARDED. A declaration with config kwargs passes them through
     to the tool class constructor.

  4. DATA_PATH IS FORWARDED. A declaration with data_path sets base_dir on the
     instantiated tool.

  5. ENSURE PROVISIONS ONCE. ensure() creates instanceizer.json when absent.
     A second ensure() with different arguments does NOT overwrite — the
     holder's existing config is preserved.

  6. BARE NAME IS REFUSED. _import_class('Foo') with no module path raises
     ValueError — a class with no address cannot be imported.

  7. UNRESOLVABLE CLASS IS LOUD. load() with a tool_class that names a module
     or class that does not exist raises, not silently succeeds.

    python3 cairn/tools/instanceizer/proofs/test_instanceizer.py   # exit 0 = green
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.tools.instanceizer.instanceizer import load, ensure, _import_class  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        msg = f"  FAIL  {label}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        FAILURES.append(label)


def _main() -> int:
    with tempfile.TemporaryDirectory(prefix="instanceizer_proof_") as tmp:
        root = Path(tmp)

        # --- tooth 1: missing declaration is loud ---
        empty_folder = root / "no_decl"
        empty_folder.mkdir()
        try:
            load(empty_folder)
            check("load_missing_raises", False, "load() returned instead of raising")
        except FileNotFoundError:
            check("load_missing_raises", True)
        except Exception as exc:
            check("load_missing_raises", False, f"wrong exception: {type(exc).__name__}: {exc}")

        # --- tooth 2: load instantiates the declared class ---
        good_folder = root / "good"
        good_folder.mkdir()
        decl = {
            "tool_class": "collections.OrderedDict",
            "data_path": "data",
            "config": {},
        }
        (good_folder / "instanceizer.json").write_text(json.dumps(decl) + "\n")
        from collections import OrderedDict
        obj = load(good_folder)
        check("load_instantiates_class", isinstance(obj, OrderedDict),
              f"got {type(obj).__name__}, expected OrderedDict")

        # --- tooth 3: config kwargs forwarded ---
        config_folder = root / "with_config"
        config_folder.mkdir()
        decl_config = {
            "tool_class": "collections.OrderedDict",
            "config": {"a": 1, "b": 2},
        }
        (config_folder / "instanceizer.json").write_text(json.dumps(decl_config) + "\n")
        obj_c = load(config_folder)
        check("config_forwarded", obj_c.get("a") == 1 and obj_c.get("b") == 2,
              f"got {dict(obj_c)}")

        # --- tooth 4: data_path sets base_dir ---
        dp_folder = root / "with_data_path"
        dp_folder.mkdir()
        decl_dp = {
            "tool_class": "collections.OrderedDict",
            "data_path": "my_data",
            "config": {},
        }
        (dp_folder / "instanceizer.json").write_text(json.dumps(decl_dp) + "\n")
        obj_dp = load(dp_folder)
        expected_base = str(dp_folder / "my_data")
        check("data_path_sets_base_dir", obj_dp.get("base_dir") == expected_base,
              f"base_dir={obj_dp.get('base_dir')!r}, expected {expected_base!r}")

        # --- tooth 5: ensure provisions once, does not overwrite ---
        prov_folder = root / "provision"
        result = ensure(prov_folder, tool_class="collections.OrderedDict", data_path="data")
        check("ensure_creates", (prov_folder / "instanceizer.json").exists())

        first_content = (prov_folder / "instanceizer.json").read_text()

        result2 = ensure(prov_folder, tool_class="collections.Counter",
                         data_path="other", config={"x": 99})
        second_content = (prov_folder / "instanceizer.json").read_text()
        check("ensure_no_overwrite", first_content == second_content,
              "ensure() overwrote existing declaration")

        # --- tooth 6: bare name refused ---
        try:
            _import_class("Foo")
            check("bare_name_refused", False, "_import_class accepted a bare name")
        except ValueError:
            check("bare_name_refused", True)
        except Exception as exc:
            check("bare_name_refused", False, f"wrong exception: {type(exc).__name__}")

        # --- tooth 7: unresolvable class is loud ---
        bad_folder = root / "bad_class"
        bad_folder.mkdir()
        decl_bad = {
            "tool_class": "no.such.module.NoSuchClass",
            "config": {},
        }
        (bad_folder / "instanceizer.json").write_text(json.dumps(decl_bad) + "\n")
        try:
            load(bad_folder)
            check("unresolvable_class_raises", False, "load() returned with bogus class")
        except (ModuleNotFoundError, AttributeError, ImportError):
            check("unresolvable_class_raises", True)
        except Exception as exc:
            check("unresolvable_class_raises", False, f"unexpected: {type(exc).__name__}: {exc}")

    print()
    total = CHECKS
    green = total - len(FAILURES)
    print(f"{total} checks · {green} green · {len(FAILURES)} red")
    if FAILURES:
        print(f"FAILURES: {', '.join(FAILURES)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

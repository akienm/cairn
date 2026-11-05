"""The restart skill's proof reaches no device (ticket e9c29538b7fb) — teeth a hollow build could not pass.

RULE 1: nothing outside a device reaches into its code, skills included. The selector proof's
tooth (i) imported the cc device's probe module to check the skill's WATCHME probe; it now asks
the WATCHME gate's own public measure, ``cairn.tools.base.watchme_spec.armed_error``, by berth
path. This proof holds that no skills/restart file imports a device (an ``import_module`` string
included), that the selector proof's ``_probe_armed`` still JUDGES (a PROBE with no ``enough``
and a file with no PROBE are both refused), and that it passes the real probe.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

_SKILL = Path(__file__).resolve().parents[1]
_ROOT = _SKILL.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

PROVES = {
    "e9c29538b7fb": {
        "1": "test_no_restart_file_reaches_a_device",
        "2": "test_the_armed_check_reds_an_unarmed_berth",
        "3": "test_the_armed_check_passes_the_real_probe",
    },
}

_BERTH = _ROOT / "cairn" / "devices" / "cc" / "probes" / "a_restart_leaves_a_slate_behind_it.py"


def _selector_proof():
    """The sibling proof module, loaded at call time: a build without _probe_armed reds a tooth."""
    if str(_SKILL) not in sys.path:
        sys.path.insert(0, str(_SKILL))
    spec = importlib.util.spec_from_file_location(
        "_restart_selector_proof", _SKILL / "proofs" / "test_restart_selector.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _reaches() -> list[str]:
    out = []
    for path in sorted(_SKILL.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.Call):
                fn = node.func
                fname = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                first = node.args[0] if node.args else None
                if fname == "import_module" and isinstance(first, ast.Constant) and isinstance(first.value, str):
                    names = [first.value]
                else:
                    continue
            else:
                continue
            for name in names:
                if name.startswith("cairn.devices."):
                    out.append(f"{path.relative_to(_ROOT)}:{node.lineno} reaches {name}")
    return out


def test_no_restart_file_reaches_a_device():
    reaches = _reaches()
    assert not reaches, "skills/restart reaches into a device: " + "; ".join(reaches)


def test_the_armed_check_reds_an_unarmed_berth():
    from cairn.tools.scratch.scratch import scratch_dir

    mod = _selector_proof()
    folder = Path(scratch_dir("testing-e9c29538b7fb-"))
    unarmed = folder / "unarmed.py"
    unarmed.write_text(_BERTH.read_text(encoding="utf-8")
                       + "\nimport dataclasses\nPROBE = dataclasses.replace(PROBE, enough=None)\n",
                       encoding="utf-8")
    noprobe = folder / "noprobe.py"
    noprobe.write_text("X = 1\n", encoding="utf-8")
    for path in (unarmed, noprobe):
        err = mod._probe_armed(path)
        assert isinstance(err, str) and err, f"_probe_armed passed {path.name}, which is not armed"
    assert "enough" in mod._probe_armed(unarmed), "the unarmed berth's refusal does not name its missing enough"


def test_the_armed_check_passes_the_real_probe():
    mod = _selector_proof()
    err = mod._probe_armed()
    assert err is None, f"the real probe is not armed: {err}"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {exc}")
    sys.exit(1 if failed else 0)

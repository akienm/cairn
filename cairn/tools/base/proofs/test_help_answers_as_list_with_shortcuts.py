"""Proof for ticket 2d6c1c36f3bd — help answers as list, and list carries the device's bin shortcuts.

Akien 2026-11-05: "help can just call list. help is specifically an anticipation of the behavior
of the other monkeys in my species." Help is asked from anywhere, so it is everywhere, defined
once (outline 8.4.3.2). Teeth, one per falsifier clause:

  1. ROOT_VERB_SEMANTICS carries help, and its meaning names it the word people type for list.
  2. for a fixture shim, resolve(['help']) and resolve(['list']) return identical text, data and
     exit.
  3. list's data carries 'shortcuts' — each executable in the device's instance bin with its first
     comment line, a non-executable file absent — and its text a 'shortcuts:' section.
  4. a module-level cold_list(device_id, instance_root) returns the root verbs with their
     semantics and the bin shortcuts while constructing no shim and opening no bus (driven in a
     subprocess where the bus modules are unimportable and BaseShim.__init__ raises).
  5. test_root_verb_vocabulary passes over the seven.

Everything runs under a scratch HOME and a scratch CAIRN_INSTANCE_ROOT from the scratch door;
nothing reads or writes ~/.cairn. The subject (shim.py's help, cold_list, shortcuts) is bound at
call time inside each tooth, so a hollow reading reds the teeth by name.

    python3 cairn/tools/base/proofs/test_help_answers_as_list_with_shortcuts.py   # exit 0 = green
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "2d6c1c36f3bd": {
        "1": "clause_1_help_is_in_the_semantics",
        "2": "clause_2_help_answers_as_list",
        "3": "clause_3_list_carries_the_bin_shortcuts",
        "4": "clause_4_cold_list_needs_no_shim_and_no_bus",
        "5": "clause_5_the_vocabulary_proof_passes_over_seven",
    },
}

FIXTURE = "2d6c-fixture"
FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1200]}", flush=True)
        FAILURES.append(name)


def _world() -> tuple[Path, Path]:
    """A scratch HOME and its instance root, with the fixture device's bin holding two
    executables (one with a shebang before its comment) and one non-executable file."""
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("2d6c-home-")
    root = home / ".cairn" / "devices"
    b = root / FIXTURE / "0" / "bin"
    b.mkdir(parents=True)
    (b / "frob").write_text("#!/usr/bin/env bash\n# frob — turns the fixture's crank\necho frob\n")
    (b / "zap").write_text("#!/usr/bin/env python3\n\n# zap the fixture, twice\nprint('zap')\n")
    (b / "notes.txt").write_text("# not a shortcut: not executable\n")
    os.chmod(b / "frob", 0o755)
    os.chmod(b / "zap", 0o755)
    os.chmod(b / "notes.txt", 0o644)
    return home, root


WANT = [{"name": "frob", "about": "frob — turns the fixture's crank"},
        {"name": "zap", "about": "zap the fixture, twice"}]


def _drive(home: Path, root: Path, mode: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, HOME=str(home), CAIRN_INSTANCE_ROOT=str(root), PYTHONPATH=str(REPO))
    return subprocess.run([sys.executable, __file__, "--drive", mode], env=env, capture_output=True,
                          text=True, timeout=120, cwd=str(REPO))


def clause_1_help_is_in_the_semantics() -> None:
    from cairn.tools.base import shim
    table = getattr(shim, "ROOT_VERB_SEMANTICS", {})
    meaning = table.get("help", "")
    lacks = []
    if "help" not in table:
        lacks.append("ROOT_VERB_SEMANTICS carries no help")
    elif "list" not in meaning.lower() or "type" not in meaning.lower():
        lacks.append(f"help's meaning does not name it the word people type for list: {meaning!r}")
    if "help" not in getattr(shim, "ROOT_VERBS", ()):
        lacks.append("ROOT_VERBS (derived) carries no help")
    _check("clause_1_help_is_in_the_semantics", not lacks, "; ".join(lacks))


def clause_2_help_answers_as_list(world) -> None:
    r = _drive(*world, "pair")
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        _check("clause_2_help_answers_as_list", False, f"driver rc={r.returncode}: {r.stdout} {r.stderr}")
        return
    h, li = out["help"], out["list"]
    lacks = []
    if li["exit"] != 0:
        lacks.append(f"list exit {li['exit']}: {li['text']}")
    for k in ("exit", "text", "data", "cached"):
        if h.get(k) != li.get(k):
            lacks.append(f"help's {k} differs from list's: {h.get(k)!r} vs {li.get(k)!r}")
    _check("clause_2_help_answers_as_list", not lacks, "; ".join(lacks))


def clause_3_list_carries_the_bin_shortcuts(world) -> None:
    r = _drive(*world, "pair")
    try:
        li = json.loads(r.stdout.strip().splitlines()[-1])["list"]
    except (ValueError, IndexError):
        _check("clause_3_list_carries_the_bin_shortcuts", False, f"driver rc={r.returncode}: {r.stderr}")
        return
    data, text = li.get("data") or {}, li.get("text") or ""
    lacks = []
    if data.get("shortcuts") != WANT:
        lacks.append(f"data['shortcuts'] is {data.get('shortcuts')!r}, want {WANT!r}")
    lines = [ln.strip() for ln in text.splitlines()]
    if "shortcuts:" not in lines:
        lacks.append("the text carries no 'shortcuts:' section")
    else:
        tail = lines[lines.index("shortcuts:") + 1:]
        for w in WANT:
            if not any(ln.startswith(w["name"]) and w["about"] in ln for ln in tail):
                lacks.append(f"the shortcuts section does not show {w['name']} with {w['about']!r}")
        if any("notes.txt" in ln for ln in tail):
            lacks.append("a non-executable file is listed as a shortcut")
    _check("clause_3_list_carries_the_bin_shortcuts", not lacks, "; ".join(lacks))


def clause_4_cold_list_needs_no_shim_and_no_bus(world) -> None:
    r = _drive(*world, "cold")
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        _check("clause_4_cold_list_needs_no_shim_and_no_bus", False,
               f"driver rc={r.returncode}: {r.stdout[-600:]} {r.stderr[-900:]}")
        return
    from cairn.tools.base import shim
    lacks = []
    if out.get("error"):
        lacks.append(out["error"])
    else:
        res, envres = out["explicit"], out["env"]
        d = res.get("data") or {}
        if res.get("exit") != 0:
            lacks.append(f"cold_list exit {res.get('exit')}: {res.get('text')}")
        if d.get("verbs") != list(shim.ROOT_VERBS):
            lacks.append(f"verbs {d.get('verbs')!r}")
        if d.get("semantics") != dict(shim.ROOT_VERB_SEMANTICS):
            lacks.append("semantics are not the root table")
        if d.get("shortcuts") != WANT:
            lacks.append(f"shortcuts {d.get('shortcuts')!r}")
        if "shortcuts:" not in (res.get("text") or ""):
            lacks.append("cold_list's text carries no shortcuts: section")
        if envres != res:
            lacks.append("cold_list(device, None) does not honour CAIRN_INSTANCE_ROOT")
        if out.get("bus_modules_loaded"):
            lacks.append(f"bus modules loaded: {out['bus_modules_loaded']}")
    _check("clause_4_cold_list_needs_no_shim_and_no_bus", not lacks, "; ".join(lacks))


def clause_5_the_vocabulary_proof_passes_over_seven() -> None:
    proof = REPO / "cairn" / "tools" / "base" / "proofs" / "test_root_verb_vocabulary.py"
    src = proof.read_text()
    lacks = []
    if '"help"' not in src.split("_RULED =", 1)[-1].split("\n", 1)[0]:
        lacks.append("test_root_verb_vocabulary's _RULED does not name help — it still pins six")
    r = subprocess.run([sys.executable, str(proof)], capture_output=True, text=True, timeout=900,
                       cwd=str(REPO), env=dict(os.environ, PYTHONPATH=str(REPO)))
    if r.returncode != 0:
        lacks.append(f"test_root_verb_vocabulary exits {r.returncode}: {(r.stdout + r.stderr)[-900:]}")
    _check("clause_5_the_vocabulary_proof_passes_over_seven", not lacks, "; ".join(lacks))


# --- the driver: what each subprocess runs ------------------------------------------------------

def _fixture_shim():
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    class _Dev(BaseDevice):
        @property
        def device_id(self) -> str:
            return FIXTURE

        def intention(self) -> dict:
            return {"what": "fixture", "why": "proof 2d6c1c36f3bd"}

        def state(self) -> dict:
            return {}

        def settings(self) -> dict:
            return {}

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return FIXTURE

        def _start_device(self):
            return _Dev()

    return _Shim


def _drive_main(mode: str) -> int:
    if mode == "pair":
        s = _fixture_shim()()
        print(json.dumps({"help": s.resolve(["help"]), "list": s.resolve(["list"])}, sort_keys=True))
        return 0
    # cold: the bus modules cannot be imported, and constructing any shim raises
    import importlib.abc

    class _NoBus(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name.startswith(("cairn.tools.bus_client", "cairn.devices.cairn.machines.bus")):
                raise ImportError(f"{name} is unimportable in this proof")
            return None

    sys.meta_path.insert(0, _NoBus())
    from cairn.tools.base import shim

    def _refuse(self, *a, **k):
        raise AssertionError("cold_list constructed a shim")

    shim.BaseShim.__init__ = _refuse
    fn = getattr(shim, "cold_list", None)
    if fn is None:
        print(json.dumps({"error": "shim.py has no module-level cold_list"}))
        return 0
    try:
        explicit = fn(FIXTURE, os.environ["CAIRN_INSTANCE_ROOT"])
        env = fn(FIXTURE, None)
    except Exception as exc:  # noqa: BLE001 — the tooth reports it by name
        print(json.dumps({"error": f"cold_list raised {type(exc).__name__}: {exc}"}))
        return 0
    loaded = sorted(m for m in sys.modules if m.startswith(("cairn.tools.bus_client", "cairn.devices.cairn.machines.bus")))
    print(json.dumps({"explicit": explicit, "env": env, "bus_modules_loaded": loaded}, sort_keys=True))
    return 0


def main() -> int:
    print("2d6c1c36f3bd — help answers as list, and list carries the device's bin shortcuts")
    world = _world()
    try:
        for tooth in (clause_1_help_is_in_the_semantics,
                      lambda: clause_2_help_answers_as_list(world),
                      lambda: clause_3_list_carries_the_bin_shortcuts(world),
                      lambda: clause_4_cold_list_needs_no_shim_and_no_bus(world),
                      clause_5_the_vocabulary_proof_passes_over_seven):
            name = getattr(tooth, "__name__", "tooth")
            try:
                tooth()
            except Exception as exc:  # noqa: BLE001 — each tooth reports even when one raises
                _check(name, False, f"raised {type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(world[0], ignore_errors=True)
    print(f"{'GREEN' if not FAILURES else 'RED'}: {len(FAILURES)} failing: {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--drive":
        sys.exit(_drive_main(sys.argv[2]))
    raise SystemExit(main())

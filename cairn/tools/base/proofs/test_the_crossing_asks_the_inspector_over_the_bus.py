"""PROOF for ticket 17d570c10390: a crossing asks the inspector over codemother's bus verb.

build_inspector moves inside codemother (ticket 4c4addb09adb), and RULE 1 lets code outside her
reach her only through the bus plus the tool she publishes (inspect_wire). Measured 2026-11-13:
transitions.py imported 18 judges from cairn.machines.build_inspector, and nine other code sites
imported it too. They now ask her ``inspect`` verb through ``transitions.ask_inspector``.

  1. no file in the code-site list imports cairn.machines.build_inspector or
     cairn.devices.codemother.machines.build_inspector (AST read; preflight.sh's inline python
     is read as text);
  2. a crossing walked over a scratch bus with codemother present reaches the verdict it reached
     before: a drifted workflow is refused as MalformedWorkflow, a legal kick-back crosses and
     journals 'back', and each was answered by an ``inspect`` ask;
  3. the same crossing with codemother absent refuses as InspectRefused, naming the absent
     answer, and moves nothing: no history, no state.

    python3 cairn/tools/base/proofs/test_the_crossing_asks_the_inspector_over_the_bus.py
"""
from __future__ import annotations

import ast
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import transitions  # noqa: E402
from cairn.devices.codemother.tools.inspect_wire import inspect_wire as iw  # noqa: E402

PROVES = {"17d570c10390": {
    "1": "test_no_code_site_imports_the_inspector",
    "2": "test_a_crossing_over_the_bus_reaches_the_verdict_it_reached_before",
    "3": "test_with_codemother_absent_the_crossing_refuses_and_moves_nothing",
}}

_SITES = (
    "cairn/tools/base/transitions.py",
    "cairn/devices/tester/hollow.py",
    "cairn/machines/corrosion/probes/the_comparison_is_read.py",
    "cairn/tools/base/probes/gate_parameters_adjust_from_feedback.py",
    "cairn/tools/base/probes/the_seed_versus_living_delta.py",
    "cairn/tools/gate/gate.py",
    "cairn/tools/question/probes/both_ends_agree.py",
    "skills/design/door.py",
    "skills/intent/door.py",
    "skills/sorted/door.py",
)
_SHELL = "cairn/devices/cc/scripts/preflight.sh"
_BANNED = ("cairn.machines.build_inspector", "cairn.devices.codemother.machines.build_inspector")

_DRIFTED = "code-seam@v1: THINKME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
_AT_PROVE = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"


def _banned(name: str) -> bool:
    return any(name == b or name.startswith(b + ".") for b in _BANNED)


def _imports(path: Path) -> list[str]:
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [f"{node.lineno}:{a.name}" for a in node.names if _banned(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module and _banned(node.module):
            out.append(f"{node.lineno}:{node.module}")
    return out


def test_no_code_site_imports_the_inspector():
    reaches = {s: _imports(_REPO_ROOT / s) for s in _SITES}
    text = (_REPO_ROOT / _SHELL).read_text(encoding="utf-8")
    reaches[_SHELL] = [f"{n}:{line.strip()}" for n, line in enumerate(text.splitlines(), 1)
                       if re.search(r"(from|import)\s+(" + "|".join(map(re.escape, _BANNED)) + r")\b",
                                    line)]
    left = {s: r for s, r in reaches.items() if r}
    assert not left, f"code sites still import the inspector: {left}"


def _spy(monkeypatch) -> list[str]:
    asked: list[str] = []
    real = iw.ask

    def ask(judge, *a, **k):
        asked.append(judge)
        return real(judge, *a, **k)
    monkeypatch.setattr(iw, "ask", ask)
    return asked


def test_a_crossing_over_the_bus_reaches_the_verdict_it_reached_before(monkeypatch):
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-17d5-present")
    asked = _spy(monkeypatch)
    try:
        transitions.emit(_DRIFTED, "PROVEME")
    except transitions.MalformedWorkflow as exc:
        assert "does not conform" in str(exc), f"the red's words did not cross: {exc}"
    else:
        raise AssertionError("a drifted workflow crossed: the red verdict was lost over the bus")
    assert "crossing_rules" in asked, f"the red crossing asked nothing over the bus: {asked}"
    asked.clear()
    from cairn.tools.charter import projector
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.emit(_AT_PROVE, "BUILDME", history_path=hist, state_path=state)
        assert "[BUILDME:waiting]" in new, f"the green kick-back did not move the cursor: {new}"
        rec = projector.read_history(hist)[0]
        assert rec["direction"] == "back", f"the green crossing journaled {rec}"
    assert "crossing_rules" in asked, f"the green crossing asked nothing over the bus: {asked}"


def test_with_codemother_absent_the_crossing_refuses_and_moves_nothing(monkeypatch):
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus
    from cairn.tools.bus_client import bus_client
    monkeypatch.delenv(transitions.PROOF_ENV, raising=False)
    monkeypatch.setattr(iw, "_HELD", {})
    monkeypatch.setattr(transitions, "INSPECT_TIMEOUT", 3.0)
    with scratch_bus("testing_17d5_absent") as bus, tempfile.TemporaryDirectory() as d:
        monkeypatch.setattr(bus_client, "reach", lambda *devices: bus)
        hist, state = Path(d) / "history.json", Path(d) / "state.json"
        try:
            transitions.emit(_AT_PROVE, "BUILDME", history_path=str(hist), state_path=str(state))
        except iw.InspectRefused as exc:
            assert "no answer from codemother" in str(exc), f"the refusal names nothing: {exc}"
        else:
            raise AssertionError("with codemother absent the crossing moved")
        assert not hist.exists() and not state.exists(), (
            f"a refused crossing wrote: {sorted(p.name for p in Path(d).iterdir())}")


class _MP:
    def __init__(self):
        self.undo = []

    def setattr(self, obj, name, value):
        self.undo.append(("a", obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def setenv(self, name, value):
        import os
        self.undo.append(("e", os.environ, name, os.environ.get(name)))
        os.environ[name] = value

    def delenv(self, name, raising=True):
        import os
        self.undo.append(("e", os.environ, name, os.environ.get(name)))
        os.environ.pop(name, None)

    def close(self):
        for kind, obj, name, v in reversed(self.undo):
            if kind == "a":
                setattr(obj, name, v)
            elif v is None:
                obj.pop(name, None)
            else:
                obj[name] = v


def _main() -> int:
    failed = 0
    for name in PROVES["17d570c10390"].values():
        fn = globals()[name]
        mp = _MP()
        try:
            fn(mp) if fn.__code__.co_argcount else fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
        finally:
            mp.close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

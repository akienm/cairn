"""Proof for ticket 93a9cc0f7677 — a trouble raise refuses a detail that is not a mapping.

Measured 2026-10-11: a raise whose ``detail`` was a string landed on disk, and every trouble
drain since refused it at the fold, holding harbor_master's raise watermark. The refusal
belongs at the raiser, loud, before anything is written.

1. raise_trouble('x', why='w', detail='text') raises TroubleRaiseRefused naming 'str' and
   writes no emission file;
2. detail=None and detail={'a': 1} still emit.

Every tooth raises from a fixture device into a SCRATCH log home. ``diagnostic`` is imported
inside the teeth, so the hollow reading reds tooth 1 by name.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_raise_detail_is_a_mapping.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "93a9cc0f7677": {
        "1": "a_text_detail_is_refused_and_nothing_is_written",
        "2": "a_none_or_mapping_detail_still_emits",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail}")
    if not ok:
        FAILURES.append(name)


def _device(tmp: str):
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    d = _Fixture()
    d.set_diagnostic_roots({k: Path(tmp) for k in ("repo", "commons", "instance")})
    return d


def _raises(tmp: str) -> list[dict]:
    from cairn.tools.base.address import log_path
    home = Path(log_path("a_fixture_component", 0, {k: Path(tmp) for k in ("repo", "commons", "instance")}))
    if not home.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(home.glob("*.raise_trouble.json"))]


def test_1() -> None:
    from cairn.tools.base.diagnostic import TroubleRaiseRefused
    name = PROVES["93a9cc0f7677"]["1"]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _device(tmp).raise_trouble("x", why="w", detail="text")
        except TroubleRaiseRefused as exc:
            check(name, "str" in str(exc) and not _raises(tmp), f"{exc}; files={len(_raises(tmp))}")
        except Exception as exc:  # noqa: BLE001
            check(name, False, f"{type(exc).__name__}: {exc}")
        else:
            check(name, False, f"admitted; files={len(_raises(tmp))}")


def test_2() -> None:
    name = PROVES["93a9cc0f7677"]["2"]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            d = _device(tmp)
            d.raise_trouble("x", why="w", detail=None)
            d.raise_trouble("y", why="w", detail={"a": 1})
            details = sorted((r["pointer"], json.dumps(r["values"]["detail"])) for r in _raises(tmp))
            check(name, details == [("x", "{}"), ("y", '{"a": 1}')], repr(details))
        except Exception as exc:  # noqa: BLE001
            check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    test_1()
    test_2()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

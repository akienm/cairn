"""Proof for ticket c2172127d7a4 — a clear carries the clearer's measured hand.

A clear's ``by`` is typed by whoever sends it; the hand is MEASURED, in the clearer's own
process, with the same ``caller()`` the artifact journal uses. And a clear is never lost to
its own measurement: when ``caller()`` raises, the clear still emits, with the error on it.

1. clear_trouble(...) from this process writes an emission whose values.hand.class equals
   cairn.tools.artifact.artifact.caller()['class'] measured here, with a non-empty ancestry;
2. with caller monkeypatched to raise OSError, the emission still lands, with hand.class
   'unknown' and the error named.

Emissions go into a SCRATCH log root. ``diagnostic`` is imported inside the teeth.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_clear_carries_the_clearers_hand.py
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
    "c2172127d7a4": {
        "1": "the_clear_carries_the_measured_hand",
        "2": "a_failed_measure_still_clears",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _clear(tmp: str) -> list[dict]:
    """One clear from a fixture component into ``tmp``; returns the clear emissions there."""
    from cairn.tools.base.address import log_path
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
    d = _Fixture()
    d.set_diagnostic_roots(roots)
    d.clear_trouble("a-fixture-defect", by="cc", what_changed="the proof cleared it")
    home = Path(log_path("a_fixture_component", 0, roots))
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(home.glob("*.clear_trouble.json"))]


def test_1() -> None:
    from cairn.tools.artifact import artifact
    name = PROVES["c2172127d7a4"]["1"]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            landed = _clear(tmp)
            want = artifact.caller()["class"]
            hand = (landed[0]["values"].get("hand") if len(landed) == 1 else None) or {}
            check(name, hand.get("class") == want and bool(hand.get("ancestry"))
                  and landed[0]["values"].get("by") == "cc",
                  f"want class {want!r}; hand={json.dumps(hand)}")
        except Exception as exc:  # noqa: BLE001
            check(name, False, f"{type(exc).__name__}: {exc}")


def test_2() -> None:
    from cairn.tools.artifact import artifact
    name = PROVES["c2172127d7a4"]["2"]
    real = artifact.caller

    def _broken():
        raise OSError("no /proc here")

    artifact.caller = _broken
    try:
        with tempfile.TemporaryDirectory() as tmp:
            landed = _clear(tmp)
            hand = (landed[0]["values"].get("hand") if len(landed) == 1 else None) or {}
            check(name, hand.get("class") == "unknown" and "OSError" in str(hand.get("error"))
                  and "no /proc here" in str(hand.get("error")),
                  f"landed={len(landed)}; hand={json.dumps(hand)}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"the clear was lost: {type(exc).__name__}: {exc}")
    finally:
        artifact.caller = real


def main() -> int:
    test_1()
    test_2()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

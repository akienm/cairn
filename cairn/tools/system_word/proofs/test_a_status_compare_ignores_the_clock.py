"""Proof for ticket 4fb08cadf1be: the sudo relay's case-fold tooth compares output with the clock removed.

Measured 2026-11-13 (the orchestrator's Linux reseal): test_system_word.py's
test_sudo_relay_takes_uppercase_status_flag compared the stdout of `cairn sudorelay --status` and
`--STATUS` byte for byte, but every line carries an ISO timestamp
("[sudo_relay] 2026-11-13T00:46:49  no live daemon ..."). It read red at 00:29:29 against
00:29:30: a coin toss whenever the second turns over between the two calls.

  1. test_untimed_drops_only_the_clock: test_system_word._untimed makes two lines that differ
     only in their timestamp equal, and keeps two lines that differ in their words unequal;
  2. test_the_relay_tooth_compares_untimed: the relay tooth's own source compares through
     _untimed, and the tooth, run, passes.

    bin/cairn test cairn/tools/system_word/proofs/test_a_status_compare_ignores_the_clock.py
"""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

_SUBJECT = Path(__file__).resolve().parent / "test_system_word.py"

PROVES = {"4fb08cadf1be": {
    "1": "test_untimed_drops_only_the_clock",
    "2": "test_the_relay_tooth_compares_untimed",
}}

_failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def _subject():
    spec = importlib.util.spec_from_file_location("_system_word_subject", _SUBJECT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_untimed_drops_only_the_clock() -> None:
    u = _subject()._untimed
    a = "[sudo_relay] 2026-11-13T00:29:29  no live daemon\n"
    b = "[sudo_relay] 2026-11-13T00:29:30  no live daemon\n"
    c = "[sudo_relay] 2026-11-13T00:29:30  a live daemon\n"
    check("test_untimed_drops_only_the_clock", u(a) == u(b) and u(b) != u(c),
          f"{u(a)!r} {u(b)!r} {u(c)!r}")


def test_the_relay_tooth_compares_untimed() -> None:
    mod = _subject()
    tooth = mod.test_sudo_relay_takes_uppercase_status_flag
    src = inspect.getsource(tooth)
    try:
        tooth()
        ran = ""
    except Exception as exc:  # noqa: BLE001
        ran = f"{type(exc).__name__}: {str(exc)[:200]}"
    check("test_the_relay_tooth_compares_untimed", "_untimed(" in src and not ran,
          f"untimed_in_source={'_untimed(' in src} ran={ran!r}")


def main() -> int:
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(name, False, f"raised {type(exc).__name__}: {exc}")
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

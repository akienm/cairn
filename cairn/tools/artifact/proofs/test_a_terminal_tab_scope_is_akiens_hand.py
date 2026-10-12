#!/usr/bin/env python3
"""Proof that a scope nested inside a terminal's scope is Akien's hand (b63f5bbbef89).

Measured 2026-10-12: Akien ran the who-writes-what clear script in Konsole and all nine
clears landed partially_cleared with hand class 'unknown'. His cgroup was
``.../app.slice/app-org.kde.konsole-78471.scope/tab(3360690).scope`` — this Konsole nests
each tab in a sub-scope — and ``classify()`` read only the leaf. It now walks the segments
from the leaf outward and the innermost class-naming segment decides.

Teeth, one per falsifier clause (PROVES below):
  (1) the measured Konsole tab path is akien, unit app-org.kde.konsole-78471.scope;
  (2) a sub-scope under superclaude-42.scope is cc, one under cairn-web-server.service is gate;
  (3) the existing classify cases in test_artifact_door.py read as they did.
Hollow: today's leaf-only classify reds 1 and 2.

    bin/cairn test cairn/tools/artifact/proofs/test_a_terminal_tab_scope_is_akiens_hand.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"b63f5bbbef89": {
    "1": "test_a_konsole_tab_is_akien",
    "2": "test_nested_scopes_keep_their_class",
    "3": "test_the_existing_cases_stand",
}}

APP = "/user.slice/user-1000.slice/user@1000.service/app.slice"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _classify(path):
    # Bound at call time: a reverted subject reds the teeth instead of crashing the reader.
    from cairn.tools.artifact.artifact import classify
    return classify(path)


def test_a_konsole_tab_is_akien() -> None:
    got = _classify(f"{APP}/app-org.kde.konsole-78471.scope/tab(3360690).scope")
    check("test_a_konsole_tab_is_akien",
          got["class"] == "akien" and got["unit"] == "app-org.kde.konsole-78471.scope", str(got))


def test_nested_scopes_keep_their_class() -> None:
    cc = _classify(f"{APP}/superclaude-42.scope/tab(1).scope")
    gate = _classify(f"{APP}/cairn-web-server.service/worker.scope")
    check("test_nested_scopes_keep_their_class",
          (cc["class"], cc["unit"], gate["class"], gate["unit"])
          == ("cc", "superclaude-42.scope", "gate", "cairn-web-server.service"),
          f"cc: {cc}; gate: {gate}")


def test_the_existing_cases_stand() -> None:
    cases = [
        (f"{APP}/cairn-web-server.service", "gate"),
        (f"{APP}/superclaude-42.scope", "cc"),
        (f"{APP}/app-org.kde.konsole-7e5c.scope", "akien"),
        ("/user.slice/user-1000.slice/session-2.scope", "akien"),
        ("/user.slice/user-1000.slice/user@1000.service", "unknown"),
        (None, "unknown"),
        ("/a/cairn-web.scope", "unknown"),
    ]
    wrong = [(p, want, _classify(p)["class"]) for p, want in cases if _classify(p)["class"] != want]
    check("test_the_existing_cases_stand", not wrong, f"wrong: {wrong}")


def main() -> int:
    for tooth in (test_a_konsole_tab_is_akien, test_nested_scopes_keep_their_class,
                  test_the_existing_cases_stand):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

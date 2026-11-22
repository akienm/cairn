#!/usr/bin/env python3
"""Proof: import_sieve carries only rule kinds something declares (ticket 27f5ad6f62dc).

Measured 2026-11-13 on akienyoga9i, and again 2026-11-22 on akiendelllinux: git grep finds
the device_isolation rule kind only in sieve.py and its own three tests. No rule set, charter
or caller declares it. RULE 1's physics is build_inspector's encapsulation_holds (ticket
124c0312c2d8). The kind split '/'-keyed graph paths on os.sep, so on Windows it found no
devices and read green without looking. The orchestrator ruled: delete it.

  1. a rule of kind device_isolation is refused as an unknown kind (ValueError, never a
     list), and the refusal names no such kind.
  2. the kinds still in use still catch: a sole_path rule over a planted dialer reds it, and
     the same rule over the same graph without the dialer is clean (paired, per the charter's
     gates, so a sieve gutted by the deletion cannot pass).

    python3 cairn/tools/import_sieve/proofs/test_the_device_isolation_kind_is_gone.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.import_sieve import sieve

PROVES = {"27f5ad6f62dc": {
    "1": "test_a_device_isolation_rule_is_refused_as_unknown",
    "2": "test_sole_path_still_catches_a_planted_dialer",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_a_device_isolation_rule_is_refused_as_unknown() -> None:
    graph = {"web_server/listener.py": {"cairn.devices.librarian.shim"},
             "librarian/shim.py": set()}
    rule = {"kind": "device_isolation", "capability": "cross-device import",
            "device_prefix": "", "module_prefix": "cairn.devices.", "exempt": ("db_domain",)}
    try:
        got = sieve.catches(graph, rule, floor=1)
    except ValueError as exc:
        text = str(exc)
        check("test_a_device_isolation_rule_is_refused_as_unknown",
              "unknown" in text and "device_isolation" not in text.split("—", 1)[-1],
              f"refusal: {text}")
        return
    check("test_a_device_isolation_rule_is_refused_as_unknown", False,
          f"the kind was accepted and returned {got!r}")


def test_sole_path_still_catches_a_planted_dialer() -> None:
    rule = {"kind": "sole_path", "capability": "the inference host",
            "modules": ("socket", "urllib.request"), "only": "cairn/devices/inferenceproxy/"}
    door = {"cairn/devices/inferenceproxy/host.py": {"urllib.request"}}
    planted = dict(door, **{"skills/rogue/probe.py": {"socket"}})
    caught = sieve.catches(planted, rule, floor=1)
    clean = sieve.catches(door, rule, floor=1)
    ok = len(caught) == 1 and "skills/rogue/probe.py" in caught[0] and clean == []
    check("test_sole_path_still_catches_a_planted_dialer", ok,
          f"planted caught {caught}; without the dialer caught {clean}")


def main() -> int:
    for tooth in (test_a_device_isolation_rule_is_refused_as_unknown,
                  test_sole_path_still_catches_a_planted_dialer):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

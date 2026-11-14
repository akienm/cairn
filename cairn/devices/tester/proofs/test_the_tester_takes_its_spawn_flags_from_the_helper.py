"""Proof (ticket bce45318b2e0): every spawn site in the tester takes its flags from windowless_spawn.

Measured 2026-11-14 on yoga: tester/runs.py's run_owned hand-built CREATE_NO_WINDOW for the
child it holds in a Windows job, which is the duplicate the helper exists to end. The tester now
asks windowless_spawn.windowless_kwargs for those flags.

RULE 1: this tooth scans only the tester's own subtree, cairn/devices/tester/, using the scanner
windowless_spawn publishes. The tool's own proofs prove that scanner over fixtures, and the
build_inspector sieve asks the same question of the whole tree. Reads files, spawns nothing,
runs on any host.

    python3 cairn/devices/tester/proofs/test_the_tester_takes_its_spawn_flags_from_the_helper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TESTER = "cairn/devices/tester"

PROVES = {"bce45318b2e0": {
    "5": "test_no_tester_site_hand_builds_its_spawn_flags",
}}


def test_no_tester_site_hand_builds_its_spawn_flags():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / TESTER / "runs.py").is_file(), "tester/runs.py is gone: the scan would be hollow"
    bad = unhelped_sites(ROOT, TESTER)
    assert not bad, "a tester site builds its own spawn flags:\n" + "\n".join(bad)


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

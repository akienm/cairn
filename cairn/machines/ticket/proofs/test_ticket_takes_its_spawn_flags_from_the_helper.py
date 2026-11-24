"""Proof (ticket 9ac392308962): every spawn site in cairn/machines/ticket takes its flags from windowless_spawn.

Measured 2026-11-23 on akiendell: ticket.py called subprocess with neither detached_kwargs nor
windowless_kwargs, so each opened a console window on Windows while Akien worked. It now asks
windowless_spawn.windowless_kwargs.

RULE 1: this scans only cairn/machines/ticket/, through the scanner windowless_spawn publishes.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/machines/ticket"

PROVES = {"9ac392308962": {
    "1": "test_no_ticket_site_spawns_without_the_helper",
    "2": "test_ticket_still_imports_and_names_the_helper_keywords",
}}


def test_no_ticket_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "ticket.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a ticket site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_ticket_still_imports_and_names_the_helper_keywords():
    src = (ROOT / CC / "ticket.py").read_text(encoding="utf-8")
    assert "windowless_kwargs" in src, "ticket.py never takes the keywords"
    import importlib
    importlib.import_module("cairn.machines.ticket.ticket")


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

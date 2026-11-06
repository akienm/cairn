"""The bus_client's command mouth — a line a shell can say to any device (ticket 95c919b5f4aa).

    python3 -m cairn.tools.bus_client <device | module:Class> <words...>

Akien 2026-11-05 (Q#27, outline 8.4.2): "if there's a script for it, run it, else get on the
bus" — this is the "else". The words are resolved on the instance's one bus process against
the device's shim; the text goes to stdout on exit 0 and to stderr otherwise, and the process
exits with the line's own code — the same contract ``cli_main`` gives a self-named launcher.

Exits beyond the line's own code:
  2 — no shim answers to the name (said on stderr, naming it; no bus is started for it);
  1 — the bus could not be reached or refused (the cause on stderr, never a traceback).

A token holding ":" is a shim address (``module:Class``) and is passed as is; a bare name is
resolved to its shim through ``_device_shim_module`` (rack's ``shim_of``) before any bus is
asked, so a misspelt device costs no bus start.
"""
from __future__ import annotations

import sys

USAGE = "usage: python3 -m cairn.tools.bus_client <device|module:Class> <words...>"


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE, file=sys.stderr)
        return 2
    target, words = argv[0], list(argv[1:])
    if ":" not in target:
        from cairn.tools.bus_client.bus_client import _device_shim_module
        if _device_shim_module(target) is None:
            print(f"bus_client: no shim answers to {target!r} (no cairn/devices/{target}/shim.py "
                  "and no held machine of that name)", file=sys.stderr)
            return 2
    from cairn.tools.bus_client.remote import RemoteBus, ensure_bus
    try:
        ensure_bus()
        result = RemoteBus().verbs(target, words)
    except LookupError as exc:
        print(f"bus_client: {target}: {exc}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"bus_client: the bus process did not answer for {target} — "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    text = result.get("text")
    code = result.get("exit")
    if not isinstance(code, int):
        print(f"bus_client: {target} answered without an exit code: {result!r}", file=sys.stderr)
        return 1
    if text:
        print(text, file=sys.stdout if code == 0 else sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

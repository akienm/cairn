"""heartbeat — what one beat of the ground loop does, with no clock in it (ticket bae622881f03).

Akien, 2026-09-30: on start the loop records its own files' timestamps; on each beat it
compares them and restarts if they changed; then it calls every device's ground loop
trigger file and records which it called; then it writes that to one JSON. "Not
everything we MIGHT need, everything we KNOW WE NEED."

WHY MTIMES AND NOT BYTECODE. Until this ticket the loop asked whether the code objects it
held still matched a fresh compile of each file (staleness.py). On Python 3.14 a nested
``__annotate__`` const collided by ``co_name`` with the function's own, so an untouched tree
read as stale after beat 1 and the loop restarted itself 61 times. An mtime compare over
the loop's own folder answers the only question the restart needs: did someone change
this code since I started?

The runner (__main__.py) owns the clock, the claim, the flags and the exec. Everything here
is callable from a proof with temp trees.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.devices.cairn.machines.ground_loop.discovery import load_pulse

HERE = Path(__file__).resolve().parent


def own_files(folder: Path | None = None) -> list[Path]:
    """The loop's own files: the top-level ``*.py`` in its folder (proofs/ and the rest are not
    the running code)."""
    folder = Path(folder) if folder is not None else HERE
    return sorted(p for p in folder.glob("*.py") if p.is_file())


def mtimes(paths) -> dict[str, float]:
    """``{path: st_mtime}``; a file that vanished between the glob and the stat is omitted,
    which ``changed`` reports as removed."""
    out: dict[str, float] = {}
    for p in paths:
        try:
            out[str(p)] = Path(p).stat().st_mtime
        except OSError:
            continue
    return out


def changed(recorded: dict, current: dict) -> list[str]:
    """Every path added, removed, or with a different mtime. Empty means unchanged."""
    return sorted(p for p in set(recorded) | set(current) if recorded.get(p) != current.get(p))


class Triggers:
    """Calls ``on_pulse(now, {})`` on each pulse.py site, holding each loaded module against
    its mtime. A module is loaded once and kept, because pulse modules keep module-level state
    between beats (codemother's last-seen HEAD); it is re-loaded when its file changes."""

    def __init__(self) -> None:
        self._held: dict[str, tuple[float, object]] = {}

    def fire(self, now, sites) -> list[dict]:
        calls: list[dict] = []
        for site in sites:
            path = Path(site["path"])
            entry = {"device_id": site["device_id"], "level": site["level"], "path": str(path)}
            try:
                mtime = path.stat().st_mtime
                held = self._held.get(str(path))
                if held is None or held[0] != mtime:
                    _, module = load_pulse(path)
                    self._held[str(path)] = (mtime, module)
                module = self._held[str(path)][1]
                # Through JSON once, so whatever a trigger returns can land in the record.
                entry["result"] = json.loads(json.dumps(module.on_pulse(now, {}), default=str))
                entry["ok"] = True
            except Exception as exc:  # noqa: BLE001 — one trigger never stops the rest
                entry["ok"] = False
                entry["error"] = f"{type(exc).__name__}: {exc}"
            calls.append(entry)
        return calls

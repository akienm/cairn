"""gate_probes — a gate's certification fires the probes standing at that gate (ticket 32f500e517d7).

THE MODEL IS AKIEN'S (2026-10-27, open-a89d15043c7c): a ticket asks a gate; the gate's inspector
issues a finding; the finding certifies, and "that certification being completed is an event".
Certification IS a gated, ticket-carrying crossing journaled by ``transitions.emit``, so emit is
where the event is heard — right after the journal append, never before it. No orchestrator: the
gate does not know who listens. Each device that wants to hear a gate adds a probe to it ("each
device can add probes to a gate").

A DATA PROBE IS A JSON FILE in the gate's folder in instance-space:

    <instance>/devices/codemother/0/machines/gate/<gate>/probes/<stem>.json
    {"to": "cc", "event": "certified", "message": "{event} on {ticket}"}

Every probe whose ``event`` is ``certified`` fires one 'personal' bus envelope to its ``to``
(sender ``cairn``, verb the event, ``why`` the rendered message). A missing or empty folder
fires nothing. A malformed probe is named on stderr and skipped; its siblings still fire. The
template renders with ``event`` and ``ticket`` only. A code probe (``cairn.tools.base.probe``)
is the other kind Akien named and is not built here.

THE POST NEVER GATES (D5, Law 7). The journal is the crossing's record of truth and it is
written before this runs; every failure here is caught and leaves one stderr line naming the
ticket. The post goes through the one bus process (``RemoteBus``), never a private ring — the
reason ticket 48519f4789b1 D14 removed the old harbor_master post. Only class-space crossings
fire: a proof's temp history names no component, so no proof reaches the live bus.

    python3 -m cairn.tools.base.gate_probes seed <device>    # one probe into each of the six gates
    python3 -m cairn.tools.base.gate_probes clear <device>   # remove every probe addressed to it
    python3 -m cairn.tools.base.gate_probes list [<device>]
"""
from __future__ import annotations

import json
import os
import string
import sys
from pathlib import Path

from cairn.tools.base.address import instance_path, resolve

# The gates, named by what they certify (Akien approved the names 2026-10-27).
GATES = ("build", "prove", "fix", "watch", "ticket", "proved")
_ENTERED = {"BUILDME": "build", "PROVEME": "prove", "FIXME": "fix", "WATCHME": "watch",
            "TICKETME": "ticket", "PROVED": "proved"}
EVENT = "certified"
_KEYS = {"event", "ticket"}


def gate_for(target: str) -> str | None:
    """The gate a crossing INTO ``target`` certifies at, or None. ``WATCHME(<object>)`` is WATCHME."""
    return _ENTERED.get(str(target).split("(", 1)[0])


def probes_dir(gate: str, roots: dict | None = None) -> Path:
    return instance_path("codemother", 0, roots) / "machines" / "gate" / gate / "probes"


def _malformed(probe) -> str | None:
    if not isinstance(probe, dict):
        return "not a JSON object"
    for key in ("to", "event", "message"):
        if not isinstance(probe.get(key), str) or not probe[key]:
            return f"{key!r} is missing or not a string"
    try:
        fields = {f for _, f, _, _ in string.Formatter().parse(probe["message"]) if f is not None}
    except ValueError as exc:
        return f"message template: {exc}"
    if fields - _KEYS:
        return f"message template names {sorted(fields - _KEYS)}; only {sorted(_KEYS)} render"
    return None


def load(gate: str, roots: dict | None = None) -> tuple[list[tuple[str, dict]], list[str]]:
    """``(probes, errors)``: each well-formed probe as ``(stem, dict)`` in filename order, and
    one line per file that is not."""
    folder = probes_dir(gate, roots)
    probes: list[tuple[str, dict]] = []
    errors: list[str] = []
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            probe = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
            continue
        why = _malformed(probe)
        if why:
            errors.append(f"{path}: {why}")
        else:
            probes.append((path.stem, probe))
    return probes, errors


def fire(*, ticket: str, component: str, from_: str, to: str, direction: str, fingerprint: str,
         roots: dict | None = None, bus=None) -> int:
    """Post one envelope per certified probe at the gate ``to`` enters. Returns the count posted.
    Never raises: a failure is one stderr line naming the ticket."""
    try:
        gate = gate_for(to)
        if gate is None:
            return 0
        probes, errors = load(gate, roots)
        for line in errors:
            print(f"gate_probes: {ticket}: skipped malformed probe {line}", file=sys.stderr)
        probes = [(stem, p) for stem, p in probes if p["event"] == EVENT]
        if not probes:
            return 0
        if bus is None:
            from cairn.tools.bus_client.remote import RemoteBus
            bus = RemoteBus()
        crossing = {"ticket": ticket, "component": component, "from": from_, "to": to,
                    "direction": direction, "fingerprint": fingerprint}
        test_id = os.environ.get("CAIRN_TESTER_TEST_ID")
        posted = 0
        for stem, probe in probes:
            message = probe["message"].format(event=probe["event"], ticket=ticket)
            body = {**crossing, "probe": stem, "message": message}
            if test_id:
                from cairn.tools.base.testing_mark import FIELD, mark
                body[FIELD] = mark(test_id)
            bus.post(sender="cairn", to=probe["to"], channel="personal", why=message,
                     verb=probe["event"], body=body)
            posted += 1
        return posted
    except Exception as exc:  # noqa: BLE001 — the post never gates (D5); loud, never raised
        print(f"gate_probes: {ticket}: certification notice not posted: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 0


def fire_crossing(record: dict, history_path: str | None, ticket, *, roots: dict | None = None,
                  bus=None) -> int:
    """emit's one call: fire for a journaled crossing when it is a class-space crossing that
    carries a ticket. A pathless, ticketless or temp-dir crossing fires nothing (D12)."""
    if not history_path or not ticket:
        return 0
    repo = resolve("repo", roots).resolve()
    try:
        component = Path(history_path).resolve().parent.relative_to(repo)
    except ValueError:
        return 0
    return fire(ticket=str(ticket), component=str(component), from_=record.get("from"),
                to=record.get("to"), direction=record.get("direction"),
                fingerprint=record.get("fingerprint"), roots=roots, bus=bus)


def seed(device: str, roots: dict | None = None) -> list[Path]:
    """Write ``<device>.json`` into all six gates, addressed to ``device``; an existing file is
    left alone. Run once, by hand (D10A). Returns the paths written."""
    written = []
    for gate in GATES:
        path = probes_dir(gate, roots) / f"{device}.json"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"to": device, "event": EVENT, "message": "{event} on {ticket}"},
                                   indent=2) + "\n")
        written.append(path)
    return written


def _all_probe_files(roots: dict | None = None) -> list[Path]:
    return sorted(resolve("instance/devices", roots).glob("*/*/machines/gate/*/probes/*.json"))


def clear(device: str, roots: dict | None = None) -> list[Path]:
    """Delete every gate probe, at any holder, whose ``to`` is ``device``. Returns what it deleted."""
    removed = []
    for path in _all_probe_files(roots):
        try:
            to = json.loads(path.read_text()).get("to")
        except (OSError, ValueError, AttributeError):
            continue
        if to == device:
            path.unlink()
            removed.append(path)
    return removed


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    verb, rest = (args[0], args[1:]) if args else ("", [])
    if verb in ("seed", "clear") and len(rest) == 1:
        for path in (seed if verb == "seed" else clear)(rest[0]):
            print(path)
        return 0
    if verb == "list" and len(rest) <= 1:
        for path in _all_probe_files():
            try:
                to = json.loads(path.read_text()).get("to")
            except (OSError, ValueError, AttributeError):
                to = "(malformed)"
            if not rest or to == rest[0]:
                print(f"{path}  -> {to}")
        return 0
    print("usage: python3 -m cairn.tools.base.gate_probes seed|clear <device> | list [<device>]",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

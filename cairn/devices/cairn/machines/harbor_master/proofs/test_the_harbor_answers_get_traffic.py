#!/usr/bin/env python3
"""Proof that the harbor master answers ``get traffic`` and ``show traffic`` (ticket cd36b8e86cd3).

The traffic image (voyage.traffic_image: the emergent gates, at anchor, berthed) was reachable
only by importing voyage, which is how bus_client handed it to the web server, a RULE 1 reach.
Outline 9.4.1.5 gives the harbor status queries (show, get); the traffic image is now one of
its declared views, answered over the device's own fleet register.

Teeth a hollow build could not pass:
  (1) declared_views names ``traffic`` and ``get traffic`` is accepted with data EQUAL to
      voyage.traffic_image over the device's register (pinned, so the tooth is exact). A build
      without the view is refused 'no view'; one returning the map or a static dict differs.
  (2) ``show traffic`` is accepted and carries the same data plus a text rendering.
  (3) the ``get traffic`` data survives a JSON round trip unchanged: the bus carries JSON.

    bin/cairn test cairn/devices/cairn/machines/harbor_master/proofs/test_the_harbor_answers_get_traffic.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"cd36b8e86cd3": {"1": "test_get_traffic_answers_the_traffic_image",
                           "2": "test_show_traffic_renders_the_same_data",
                           "3": "test_the_traffic_image_crosses_the_bus_whole"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _envelope(verb: str, what: str) -> dict:
    return {"id": "proof", "sender": "proof", "to": "harbor_master",
            "verb": verb, "body": {"what": what}}


_PINNED: dict = {}


def _device():
    """A harbor master whose fleet cache is pinned to one register read, so the expected image
    is computed over exactly the register the view reads."""
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    from cairn.devices.cairn.machines.harbor_master.register import register
    if not _PINNED:
        _PINNED.update(register())
    dev = HarborMasterDevice()
    dev._fleet_cache = json.loads(json.dumps(_PINNED))
    return dev


def _expected() -> dict:
    from cairn.devices.cairn.machines.harbor_master import voyage
    return voyage.traffic_image(json.loads(json.dumps(_PINNED)))


def test_get_traffic_answers_the_traffic_image() -> None:
    dev = _device()
    named = "traffic" in dev.declared_views()
    reply = dev._handle_get(_envelope("get", "traffic"))
    ok = named and reply.get("accepted") is True and reply.get("data") == _expected()
    check("test_get_traffic_answers_the_traffic_image", ok,
          "" if ok else f"views {sorted(dev.declared_views())}; reply {str(reply)[:200]}")


def test_show_traffic_renders_the_same_data() -> None:
    dev = _device()
    reply = dev._handle_show(_envelope("show", "traffic"))
    ok = (reply.get("accepted") is True and reply.get("data") == _expected()
          and isinstance(reply.get("text"), str) and bool(reply["text"].strip()))
    check("test_show_traffic_renders_the_same_data", ok, "" if ok else str(reply)[:200])


def test_the_traffic_image_crosses_the_bus_whole() -> None:
    reply = _device()._handle_get(_envelope("get", "traffic"))
    data = reply.get("data")
    try:
        round_trip = json.loads(json.dumps(data))
    except (TypeError, ValueError) as exc:
        check("test_the_traffic_image_crosses_the_bus_whole", False, f"not JSON: {exc}")
        return
    ok = reply.get("accepted") is True and isinstance(data, dict) and round_trip == data \
        and {"gates", "at_anchor", "berthed", "counts"} <= set(data)
    check("test_the_traffic_image_crosses_the_bus_whole", ok, "" if ok else str(reply)[:200])


TEETH = (test_get_traffic_answers_the_traffic_image, test_show_traffic_renders_the_same_data,
         test_the_traffic_image_crosses_the_bus_whole)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

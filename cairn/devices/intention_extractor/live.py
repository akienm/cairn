"""live.py — the extractor against the real host, through the bus.

This is the FIRST live wiring of the resolve seam outside inference_domain's own proofs:
``bus.request(to="inference_domain", verb="resolve", ...)`` — the metered, cached path.
extractor.py stays import-pure — its proof pins that; this thin wrapper is where the bus
composes with the extractor's machinery, exactly as daemon.py is web_server's socket and
sudo_relay's privilege live at their own edges.

The bus is the sole path for inter-device inference (ticket 87a7f1c7ae21). The extractor
never imports inference_domain directly — it posts requests on the bus.

The cache interplay is the point, not a side effect: the same source builds the same
prompt, canonicalizes to the same key, and the second run is a HIT — the host untouched,
the saving landing in the yield view. The parsimonious-prompt aim, on the meter.

    python3 -m cairn.devices.intention_extractor.live <source-file> [model]
    # exit 0 = PASS, 1 = REFUSED (findings printed), 2 = usage
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.tools.base.bus_client import connect_bus
from cairn.devices.intention_extractor.extractor import IntentionExtractorDevice

DEFAULT_MODEL = "qwen2.5:7b"
_SENDER = "intention_extractor"


def _wire_bus():
    """Minimal bus for CLI scripts — inference_domain registered for resolve verbs."""
    return connect_bus(devices=["inference_domain"])


def _bus_resolve(bus: BusDevice, request: dict) -> dict:
    """Post a resolve request to inference_domain via the bus and return the result."""
    reply = bus.request(
        sender=_SENDER, to="inference_domain", verb="resolve",
        why="extractor resolve", body=request,
    )
    return reply["body"]


def _bus_yield(bus: BusDevice) -> dict:
    """Get inference_domain's yield report via the bus get verb."""
    reply = bus.request(
        sender=_SENDER, to="inference_domain", verb="get",
        why="yield report", body={"what": "yield"},
    )
    return reply.get("body", {}).get("data", {})


def extract_live(source: str, *, model: str = DEFAULT_MODEL,
                 bus: BusDevice | None = None) -> tuple[dict, str]:
    """One live extraction: draft via ollama through inference_domain, judged, breadcrumbed.

    Returns ``(result, trail)`` — the trail being the FILE the crossings landed in, not a list
    of them. It returned ``dev.held_diagnostics()`` until 2026-08-18 (ticket
    a-device-logs-without-being-wired), which was the right answer while an un-wired device held
    its records in memory: nobody had wired this driver, so printing the list was the only way
    the crossing was ever seen, and it vanished with the process. The device now writes its own
    trail, so what a caller needs is the address of the record rather than a copy of it — and a
    live run against the real inference host is precisely the run whose crossings should outlive
    the terminal they scrolled past."""
    if bus is None:
        bus = _wire_bus()
    dev = IntentionExtractorDevice()
    result = dev.extract(source, resolve=lambda req: _bus_resolve(bus, req))
    return result, str(dev.diagnostic_trail())


def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    bus = _wire_bus()
    source = Path(argv[0]).read_text(encoding="utf-8")
    result, trail = extract_live(source, model=argv[1] if len(argv) > 1 else DEFAULT_MODEL,
                                 bus=bus)
    print(json.dumps({**result, "trail": trail,
                      "yield": _bus_yield(bus)}, indent=2, default=str))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

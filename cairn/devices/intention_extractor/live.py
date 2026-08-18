"""live.py — the extractor against the real host, through the one door.

This is the FIRST live wiring of the resolve seam outside inference_domain's own proofs:
``domain.resolve`` (metered, cached) wrapping ``host.ollama_resolver`` (the one place that
opens the host). extractor.py stays import-pure — its proof pins that; this thin wrapper
is where the doors compose, exactly as daemon.py is web_server's socket and sudo_relay's
privilege live at their own edges.

The cache interplay is the point, not a side effect: the same source builds the same
prompt, canonicalizes to the same key, and the second run is a HIT — the host untouched,
the saving landing in ``yield_report()``. The parsimonious-prompt aim, on the meter.

    python3 -m cairn.devices.intention_extractor.live <source-file> [model]
    # exit 0 = PASS, 1 = REFUSED (findings printed), 2 = usage
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cairn.devices.inference_domain import domain, host
from cairn.devices.intention_extractor.extractor import IntentionExtractorDevice

DEFAULT_MODEL = "qwen2.5:7b"


def extract_live(source: str, *, model: str = DEFAULT_MODEL) -> tuple[dict, str]:
    """One live extraction: draft via ollama through inference_domain, judged, breadcrumbed.

    Returns ``(result, trail)`` — the trail being the FILE the crossings landed in, not a list
    of them. It returned ``dev.held_diagnostics()`` until 2026-08-18 (ticket
    a-device-logs-without-being-wired), which was the right answer while an un-wired device held
    its records in memory: nobody had wired this driver, so printing the list was the only way
    the crossing was ever seen, and it vanished with the process. The device now writes its own
    trail, so what a caller needs is the address of the record rather than a copy of it — and a
    live run against the real inference host is precisely the run whose crossings should outlive
    the terminal they scrolled past."""
    resolver = host.ollama_resolver(model=model)
    dev = IntentionExtractorDevice()
    result = dev.extract(source, resolve=lambda req: domain.resolve(req, resolver=resolver))
    return result, str(dev.diagnostic_trail())


def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    source = Path(argv[0]).read_text(encoding="utf-8")
    result, trail = extract_live(source, model=argv[1] if len(argv) > 1 else DEFAULT_MODEL)
    print(json.dumps({**result, "trail": trail,
                      "yield": domain.yield_report()}, indent=2, default=str))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

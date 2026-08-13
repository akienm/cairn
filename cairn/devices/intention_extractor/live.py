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


def extract_live(source: str, *, model: str = DEFAULT_MODEL) -> tuple[dict, list]:
    """One live extraction: draft via ollama through inference_domain, judged, breadcrumbed.
    Returns ``(result, breadcrumbs)`` — the breadcrumbs so a caller without a wired
    receiver still sees the crossing (Law 7: held, never dropped)."""
    resolver = host.ollama_resolver(model=model)
    dev = IntentionExtractorDevice()
    result = dev.extract(source, resolve=lambda req: domain.resolve(req, resolver=resolver))
    return result, dev.held_diagnostics()


def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    source = Path(argv[0]).read_text(encoding="utf-8")
    result, crumbs = extract_live(source, model=argv[1] if len(argv) > 1 else DEFAULT_MODEL)
    print(json.dumps({**result, "breadcrumbs": crumbs,
                      "yield": domain.yield_report()}, indent=2, default=str))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

"""intention_extractor — the first cocoon stage, moved upstream: raw design prose in,
a CANDIDATE intention out, judged before it is believed.

Akien, 2026-07-24, verbatim: "the librarian will have you build something, and you and i
can move, say, intention extraction to an agent. then when you get the build ticket, you
do the build... and then go back and run the inspection over the initial intention
extraction... until initial intention extraction is a settled issue." Deliberately built
AFTER CC's tooling ring (his re-ordering, 2026-07-27: "we start with CC and work
outwards") so the extractor arrives to find its judge already seated: an extraction is
graded by deterministic CHECKS and, downstream, by whether the build it fed proves out —
never by CC's opinion, the least independent witness.

THE CONTRACT
  - The DRAFT comes from the resolver seam — ``resolve(request)`` in
    ``inference_domain.resolve``'s shape, injected by the caller (the sole path to the
    host; metered, cached — the same prompt for the same source is a genuine cache hit,
    and the parsimonious-prompt aim has a meter). This module never opens the host.
  - The JUDGMENT is deterministic. Every extracted claim must stand on ANCHORS — verbatim
    quotes from the source. What the source does not literally say goes under ``read``,
    labeled inference, never mixed into what/why. The checks refuse a draft that breaks
    this; the refusal carries every finding first-pass (Law 7).
  - Every check carries PROVENANCE: the caught failure that seeded it (learns-its-gates).
    Founding failure: 2026-07-26 — "the graph type is a coordinate, not a class" was CC's
    inference recorded as Akien's ruling; of the embedding claim, only seven words were
    his. Fabricated attribution is the extraction defect this device exists to end.
  - A refused draft is a VERDICT, not an anomaly — returned with its findings for the
    caller (CC today, the librarian later) to dispose. Growth rule: a bad extraction a
    check could have caught becomes a check, and the class stops recurring (Law 1).

Live wiring lives in ``live.py`` (through inference_domain, the one door). This module is
import-pure — the proofs pin that it cannot dial out on its own.
"""

from __future__ import annotations

import hashlib
import json

from cairn.tools.base.device import BaseDevice

# The floor under a source: an "intention" extracted from a handful of characters is pure
# invention wearing an anchor's clothes (the census-of-nowhere lesson — a clean-looking
# empty world is the proxy error). Refused before the host is ever touched.
_MIN_SOURCE_CHARS = 30

# The four fields a candidate carries — exactly these, like the VALIDATION's exactly-eight:
# an extra field is drift, a missing one is a hole, and ``read`` being REQUIRED (even when
# empty) is force-the-why-structurally applied to inference-labeling — the draft cannot
# skip the decision of what it inferred.
class ExtractionRefused(RuntimeError):
    """An extraction that cannot honestly proceed refuses loudly (Law 7) — never guesses."""


def source_digest(source: str) -> str:
    """The breadcrumb pointer: a stable, short handle on WHICH source crossed."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def extraction_prompt(source: str) -> str:
    """The draft prompt — deterministic per source, so ``inference_domain``'s structural
    canonicalization makes the same source a cache HIT (the parsimonious-prompt aim,
    metered by yield_report). Kept small on purpose: 'part of what we're doing here is
    trying to find the most parsimonious prompts that can be effective' (Akien, 2026-07-27)."""
    return (
        "Extract the INTENTION from the SOURCE below as one strict JSON object with exactly "
        'these fields: {"what": "the thing intended, 1-2 sentences", '
        '"why": "the reason it is wanted, 1-2 sentences", '
        '"anchors": ["verbatim quotes from the SOURCE the what and why stand on"], '
        '"read": "anything you inferred that the SOURCE does not literally say; empty string if nothing"}. '
        "Rules: every anchor must be copied character-for-character from the SOURCE. "
        "Inference the SOURCE does not support goes in read, never in what or why. "
        "Output ONLY the JSON object.\n\nSOURCE:\n" + source
    )


def parse_draft(raw: str) -> dict | None:
    """The draft as a dict, or None if it is not one JSON object.

    The single tolerated presentation quirk: a markdown code fence around the object is
    stripped (models add it; it is wrapping, not content). Anything else that fails to
    parse is the model failing the contract — the caller refuses loudly with the raw
    draft carried WHOLE (complete diagnostic on first pass), never silently repaired.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -3]
    try:
        draft = json.loads(text)
    except ValueError:
        return None
    return draft if isinstance(draft, dict) else None


# ── the checks: HELD, NOT HOUSED ─────────────────────────────────────────────
# They berth as this device's own machine (machines/judge/), and the reason is a
# measurement, not tidiness: converting them to the shared proof record made them import
# the gate tool, and bin/cmd/determinism — which reads gate-ness as a DIRECT-import fact
# — reported a VIOLATION that had been true since the device was built. A gate may not
# have an oracle at fire time or at SLEEP, and live.py is a sleep seam. The builder and
# skills/chart both already answered this the same way: the seam stays, the gates berth
# as machines. Re-exported here because the names are this module's published surface.
from cairn.devices.intention_extractor.machines.judge.judge import (  # noqa: E402
    CANDIDATE_FIELDS,
    CHECKS,
    INSPECTORS,
    anchors_verbatim,
    findings_of,
    normalized as _norm,
    record_shape,
)



# ── the device ───────────────────────────────────────────────────────────────


class IntentionExtractorDevice(BaseDevice):
    """The extraction stage as a device (carries CP1-CP6; reports the Form v0 #2 surface).

    ``extract(source, resolve=...)`` runs one crossing: draft through the injected seam,
    judge with every check, breadcrumb the verdict, return candidate + findings. It owns
    no store — a candidate is DATA handed back to the caller; where it berths (a charter,
    a ticket, a commons intention) is the caller's disposition, not this device's write.
    """

    def __init__(self) -> None:
        super().__init__()
        self._extractions = 0
        self._verdicts = {"PASS": 0, "REFUSED": 0, "UNPARSEABLE": 0}
        self._last_digest: str | None = None

    @property
    def device_id(self) -> str:
        return "intention_extractor"

    def extract(self, source: str, *, resolve) -> dict:
        """One extraction crossing. Returns ``{"source_digest", "candidate", "verdict"
        ("PASS"|"REFUSED"), "findings", "checks_run", "hit"}``.

        Refuses BEFORE the host is touched (no breadcrumb — nothing crossed) on: no
        injected seam (the sole path is inference_domain.resolve or nothing — a
        fabricated extraction from no model is the founding defect itself), or a source
        under the floor (an intention from near-nothing is invention). Refuses AFTER
        (breadcrumb first — tokens were spent, the crossing happened) on an unparseable
        draft, carrying the raw draft whole.
        """
        if not callable(resolve):
            raise ExtractionRefused(
                "extract: no resolve seam injected — the draft comes through "
                "inference_domain.resolve or not at all (sole path). Refusing to invent "
                "an extraction from nothing."
            )
        if not isinstance(source, str) or len(_norm(source)) < _MIN_SOURCE_CHARS:
            raise ExtractionRefused(
                f"extract: source is {len(_norm(source)) if isinstance(source, str) else 'not a string'}"
                f" normalized chars — floor is {_MIN_SOURCE_CHARS}. An intention extracted "
                "from near-nothing is pure invention; the resolver was not called."
            )

        digest = source_digest(source)
        result = resolve({"kind": "generate", "prompt": extraction_prompt(source)})
        raw = result["answer"]["text"]
        draft = parse_draft(raw)

        if draft is None:
            # The crossing HAPPENED — tokens were spent — so it breadcrumbs before the
            # loud refusal (Law 7, both halves: the record and the noise).
            self._extractions += 1
            self._verdicts["UNPARSEABLE"] += 1
            self._last_digest = digest
            self.emit("extract", pointer=digest,
                      values={"verdict": "UNPARSEABLE", "checks_failed": []})
            raise ExtractionRefused(
                "extract: the draft is not one JSON object — the model failed the "
                f"contract. Raw draft, carried whole (first-pass diagnostic): {raw!r}"
            )

        record = []
        for inspector in INSPECTORS.values():
            record.extend(inspector(draft, source))
        findings = findings_of(record)
        verdict = "PASS" if not findings else "REFUSED"

        # GATE CONTACT (DiagnosticBase): a source CROSSED the extraction stage and came
        # back judged — per crossing, emitted after the judgment lands. A REFUSED verdict
        # breadcrumbs the same as a PASS: a refusal is the checks working, not an anomaly
        # of the extractor (the tester's red-and-green-alike rule). Thin: the pointer is
        # the source digest, the values the verdict and which checks refused.
        self._extractions += 1
        self._verdicts[verdict] += 1
        self._last_digest = digest
        # WHAT RAN RIDES THE BREADCRUMB, not only what objected. ``checks_failed`` alone
        # was the same two words whether every lane agreed or a lane had been dropped —
        # and this is the surface a later reader grades the extractor by.
        self.emit("extract", pointer=digest,
                  values={"verdict": verdict,
                          "checks_proved": len(record),
                          "lanes": [e["identity"] for e in record],
                          "checks_failed": sorted({f["check"] for f in findings})})
        return {
            "source_digest": digest,
            "candidate": draft,
            "verdict": verdict,
            "findings": findings,
            "checks_run": sorted(CHECKS),
            "hit": bool(result.get("hit")),
        }

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The first cocoon stage as a device: raw design prose in, a CANDIDATE "
            "intention (what + why + verbatim anchors + labeled inference) out — drafted "
            "through the inference seam, judged by deterministic checks before anyone "
            "believes it.",
            "why": "CC is the most expensive resolver; moving extraction upstream spends "
            "it parsimoniously (Law 1 on the pipeline). Built after CC's tooling ring so "
            "the judge was seated first: a draft is graded by checks and, downstream, by "
            "whether the build it fed proves out — never by CC's opinion. The founding "
            "defect it ends: fabricated attribution (2026-07-26).",
        }

    def state(self) -> dict:
        return {
            "extractions": self._extractions,
            "verdicts": dict(self._verdicts),
            "last_source_digest": self._last_digest,
        }

    def settings(self) -> dict:
        return {
            "checks": sorted(CHECKS),
            "min_source_chars": _MIN_SOURCE_CHARS,
            "seam": "resolve is injected by the caller (inference_domain.resolve — the "
                    "sole path to the host; live wiring in live.py, never here)",
            "owns": "no store — a candidate is DATA returned to the caller; its berth "
                    "(charter / ticket / commons) is the caller's disposition",
        }

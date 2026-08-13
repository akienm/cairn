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
CANDIDATE_FIELDS = ("what", "why", "anchors", "read")


class ExtractionRefused(RuntimeError):
    """An extraction that cannot honestly proceed refuses loudly (Law 7) — never guesses."""


def _norm(s: str) -> str:
    """Whitespace-collapsed form for anchor comparison: a line-wrap difference is not a
    fabrication; a changed word is."""
    return " ".join(s.split())


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


# ── the checks: deterministic judgment, each seeded by a caught failure ──────


def record_shape(draft: dict, source: str) -> list[dict]:
    """The candidate carries exactly CANDIDATE_FIELDS, with a non-empty what and why and
    at least one anchor.

    Provenance: 2026-07-14, the charter design — the filename ``intention+why.json``
    forces the why (CP3 as schema, not a field someone can leave blank); and the
    VALIDATION record's exactly-eight rule (2026-07-17), where an extra field is drift
    and a missing one a hole. ``read`` is required even when empty: the labeling decision
    cannot be silently skipped (force-the-why-structurally, applied to inference).
    """
    findings = []
    keys = set(draft)
    required = set(CANDIDATE_FIELDS)
    if keys != required:
        findings.append({
            "check": "record_shape",
            "finding": "field-set is not exactly the four",
            "evidence": {"missing": sorted(required - keys), "extra": sorted(keys - required)},
        })
    for field in ("what", "why"):
        v = draft.get(field)
        if not isinstance(v, str) or not v.strip():
            findings.append({
                "check": "record_shape",
                "finding": f"{field} is empty or not a string — silence is not a valid answer",
                "evidence": {field: v},
            })
    anchors = draft.get("anchors")
    if not isinstance(anchors, list) or not anchors or not all(
        isinstance(a, str) and a.strip() for a in anchors
    ):
        findings.append({
            "check": "record_shape",
            "finding": "anchors must be a non-empty list of non-empty strings — an "
                       "unanchored intention is invention",
            "evidence": {"anchors": anchors},
        })
    if not isinstance(draft.get("read"), str):
        findings.append({
            "check": "record_shape",
            "finding": "read must be a string ('' when nothing was inferred) — the "
                       "inference-labeling decision cannot be skipped",
            "evidence": {"read": draft.get("read")},
        })
    return findings


def _unwrap_quotes(anchor: str) -> str:
    """One symmetric outer quote pair is WRAPPING, not content — stripped before the
    verbatim comparison, exactly as a markdown fence is stripped from the draft.

    Live-caught 2026-07-27, the extractor's FIRST live fire: qwen2.5:7b quoted the
    source character-for-character and wrapped every anchor in literal quotation marks;
    all three honest quotes were refused as fabricated. A check that fires on every
    honest draft gets trained away by its own noise (the leak-scan lesson) — so the
    wrapping is normalized and the CONTENT still must match verbatim.
    """
    s = anchor.strip()
    if len(s) >= 2 and (s[0], s[-1]) in {('"', '"'), ("'", "'"), ("“", "”"),
                                         ("‘", "’")}:
        return s[1:-1]
    return s


def anchors_verbatim(draft: dict, source: str) -> list[dict]:
    """Every anchor the draft claims from the source appears in the source VERBATIM
    (whitespace-normalized — a line-wrap is not a fabrication; a changed word is; one
    symmetric outer quote pair is wrapping, see ``_unwrap_quotes``).

    Provenance: 2026-07-26 — 'the graph type is a coordinate, not a class' was recorded
    as Akien's ruling and was CC's inference (notes/held-librarian.json); of the
    embedding claim, only seven words were his, and everything after 'Consequence:' was
    CC's inference presented as though it followed. Fabricated attribution is the
    founding extraction defect: a quote that is not in the source is refused, named,
    and carried whole in the finding.
    """
    findings = []
    anchors = draft.get("anchors")
    if not isinstance(anchors, list):
        return findings  # record_shape owns that refusal; no double-count
    haystack = _norm(source)
    for a in anchors:
        if isinstance(a, str) and a.strip() and _norm(_unwrap_quotes(a)) not in haystack:
            findings.append({
                "check": "anchors_verbatim",
                "finding": "anchor is not verbatim in the source — fabricated attribution",
                "evidence": {"anchor": a},
            })
    return findings


CHECKS = {"record_shape": record_shape, "anchors_verbatim": anchors_verbatim}


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

        findings = []
        for check in CHECKS.values():
            findings.extend(check(draft, source))
        verdict = "PASS" if not findings else "REFUSED"

        # GATE CONTACT (DiagnosticBase): a source CROSSED the extraction stage and came
        # back judged — per crossing, emitted after the judgment lands. A REFUSED verdict
        # breadcrumbs the same as a PASS: a refusal is the checks working, not an anomaly
        # of the extractor (the tester's red-and-green-alike rule). Thin: the pointer is
        # the source digest, the values the verdict and which checks refused.
        self._extractions += 1
        self._verdicts[verdict] += 1
        self._last_digest = digest
        self.emit("extract", pointer=digest,
                  values={"verdict": verdict,
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

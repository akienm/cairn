"""judge/judge.py — THE DETERMINISTIC JUDGE the extraction is graded by.

WHY IT IS ITS OWN MACHINE, and the measurement that forced the move (2026-08-13). The
device's charter has always said the same two things: the DRAFT comes from an oracle
through a caller-injected seam, and the JUDGMENT is deterministic — "never by CC's
opinion, the least independent witness". Both halves lived in one component, which was
survivable only because nothing could SEE the second half. Converting the checks to the
shared proof record made them import ``cairn.tools.gate``, and ``bin/cmd/determinism``
— which reads gate-ness as a DIRECT-import fact — immediately reported what had been
true since the device was built:

    VIOLATION  cairn/devices/intention_extractor   MOSTLY DETERMINISTIC
        gate via .../extractor.py
        REACHES AN ORACLE: ... via .../live.py

The instrument was right and was not softened. A gate may not have an oracle at fire
time OR at sleep, and a component that holds both is one refactor away from a judge
that consults the thing it is judging. The in-house answer already existed, twice: the
builder is PURE DETERMINISTIC while holding eight gate machines, and skills/chart keeps
its sleep seam while its gates berth as machines. So the judge berths as one too — the
device holds it, the device does the dialing, and neither can reach the other's half.

WHAT LIVES HERE: the checks and nothing else. No parsing, no prompt, no device, no
digest — those are the extraction's, not the judgment's. This module imports ``json``
for nothing at all and does not import it; its whole outbound surface is the gate tool.

Every check carries PROVENANCE: the caught failure that seeded it (learns-its-gates).
Founding failure: 2026-07-26 — "the graph type is a coordinate, not a class" was CC's
inference recorded as Akien's ruling; of the embedding claim, only seven words were his.
Fabricated attribution is the extraction defect this judge exists to end.

A bad extraction a check could have caught becomes a check, and the class stops
recurring (Law 1).
"""

from __future__ import annotations

from cairn.tools.gate import gate

CANDIDATE_FIELDS = ("what", "why", "anchors", "read")


def normalized(s: str) -> str:
    """Whitespace-collapsed form for anchor comparison: a line-wrap difference is not a
    fabrication; a changed word is.

    Public because the device measures its source floor with the same ruler. One
    implementation, one mouth — the alternative was a second three-line copy that could
    quietly diverge from the one the anchors are compared under.
    """
    return " ".join(s.split())



def _lane(identity, check, *, expected, actual, evidence, finding=None):
    """One entry of an extraction's proof record, in the seed's shape. ``finding`` is the
    sentence this lane refuses with — carried on the entry so the finding list below can
    be READ OUT of the record rather than built beside it."""
    return gate.proved(
        identity=identity, location="the draft", code="extractor.py:%s" % identity,
        source="intention_extractor.%s" % check,
        expected=expected, actual=actual,
        findings=([] if finding is None else
                  [{"check": check, "finding": finding, "evidence": evidence}]),
        evidence=evidence)


def inspect_record_shape(draft: dict, source: str) -> list[dict]:
    """THE PROOF RECORD for the candidate's shape: one entry per rule that RAN, EXPECTED
    beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND
    LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    Why the record: a findings list is empty both when a draft satisfied every rule and
    when a rule was quietly dropped, and the device's ``checks_failed`` breadcrumb read
    the same silence. The record's LENGTH is the ruleset's size, so a rule that stops
    running makes the crossing's evidence SHORTER — visible — rather than cleaner.

    The candidate carries exactly CANDIDATE_FIELDS, with a non-empty what and why and
    at least one anchor.

    Provenance: 2026-07-14, the charter design — the filename ``intention+why.json``
    forces the why (CP3 as schema, not a field someone can leave blank); and the
    VALIDATION record's exactly-eight rule (2026-07-17), where an extra field is drift
    and a missing one a hole. ``read`` is required even when empty: the labeling decision
    cannot be silently skipped (force-the-why-structurally, applied to inference).
    """
    keys, required = set(draft), set(CANDIDATE_FIELDS)
    record = [_lane(
        "the_field_set_is_exactly_the_four", "record_shape",
        expected=sorted(required), actual=sorted(keys),
        evidence={"missing": sorted(required - keys), "extra": sorted(keys - required)},
        finding=None if keys == required else "field-set is not exactly the four")]

    for field in ("what", "why"):
        v = draft.get(field)
        ok = isinstance(v, str) and bool(v.strip())
        record.append(_lane(
            "the_%s_says_something" % field, "record_shape",
            expected="a non-empty string",
            actual="a non-empty string" if ok else "empty or not a string",
            evidence={field: v},
            finding=None if ok else
            f"{field} is empty or not a string — silence is not a valid answer"))

    anchors = draft.get("anchors")
    anchored = (isinstance(anchors, list) and bool(anchors)
                and all(isinstance(a, str) and a.strip() for a in anchors))
    record.append(_lane(
        "the_draft_is_anchored_at_all", "record_shape",
        # BOTH SIDES READ THE SAME SENTENCE WHEN IT PASSES — a lane whose ACTUAL is a
        # count can never be == its EXPECTED, so it would red on every healthy draft.
        # The count rides in the evidence, where a reader still sees it.
        expected="a non-empty list of non-empty strings",
        actual=("a non-empty list of non-empty strings" if anchored
                else "not a non-empty list of non-empty strings"),
        evidence={"anchors": anchors,
                  "n": len(anchors) if isinstance(anchors, list) else None},
        finding=None if anchored else
        "anchors must be a non-empty list of non-empty strings — an unanchored "
        "intention is invention"))

    labeled = isinstance(draft.get("read"), str)
    record.append(_lane(
        "the_inference_labeling_decision_was_made", "record_shape",
        expected="a string ('' when nothing was inferred)",
        actual=("a string ('' when nothing was inferred)" if labeled
                else "a %s" % type(draft.get("read")).__name__),
        evidence={"read": draft.get("read")},
        finding=None if labeled else
        "read must be a string ('' when nothing was inferred) — the "
        "inference-labeling decision cannot be skipped"))
    return record


def record_shape(draft: dict, source: str) -> list[dict]:
    """A VIEW OVER ``inspect_record_shape``, DERIVED AND NEVER PARALLEL — the findings
    read out of the record, so the refusal and the record cannot come to disagree."""
    return [f for e in inspect_record_shape(draft, source) if not gate.passed(e)
            for f in e["values"]["findings"]]



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


def inspect_anchors_verbatim(draft: dict, source: str) -> list[dict]:
    """THE PROOF RECORD for attribution: one lane, carrying its POPULATION — every anchor
    the draft claims as EXPECTED, the ones actually found in the source as ACTUAL.

    GUARDED, and the guard is what the old ``return findings`` said without recording it:
    a draft whose ``anchors`` is not a list has nothing to walk, so this lane is ABSENT
    rather than green, and ``the_draft_is_anchored_at_all`` above has already refused.

    Every anchor the draft claims from the source appears in the source VERBATIM
    (whitespace-normalized — a line-wrap is not a fabrication; a changed word is; one
    symmetric outer quote pair is wrapping, see ``_unwrap_quotes``).

    Provenance: 2026-07-26 — 'the graph type is a coordinate, not a class' was recorded
    as Akien's ruling and was CC's inference (notes/held-librarian.json); of the
    embedding claim, only seven words were his, and everything after 'Consequence:' was
    CC's inference presented as though it followed. Fabricated attribution is the
    founding extraction defect: a quote that is not in the source is refused, named,
    and carried whole in the finding.
    """
    anchors = draft.get("anchors")
    if not isinstance(anchors, list):
        return []                      # record_shape owns that refusal; no double-count
    haystack = normalized(source)
    claimed = [a for a in anchors if isinstance(a, str) and a.strip()]
    found = [a for a in claimed if normalized(_unwrap_quotes(a)) in haystack]
    fabricated = [a for a in claimed if a not in found]
    return [gate.proved(
        identity="every_anchor_appears_verbatim_in_the_source",
        location="the draft.anchors", code="extractor.py:anchors_verbatim",
        source="intention_extractor.anchors_verbatim",
        expected=claimed, actual=found,
        findings=[{"check": "anchors_verbatim",
                   "finding": "anchor is not verbatim in the source — fabricated "
                              "attribution",
                   "evidence": {"anchor": a}} for a in fabricated],
        evidence={"fabricated": fabricated})]


def anchors_verbatim(draft: dict, source: str) -> list[dict]:
    """A VIEW OVER ``inspect_anchors_verbatim``, DERIVED AND NEVER PARALLEL."""
    return [f for e in inspect_anchors_verbatim(draft, source) if not gate.passed(e)
            for f in e["values"]["findings"]]


INSPECTORS = {"record_shape": inspect_record_shape,
              "anchors_verbatim": inspect_anchors_verbatim}
# The findings-only registry, DERIVED from the inspectors above so a check can never be
# on one list and off the other. Kept because callers read it by name.
CHECKS = {"record_shape": record_shape, "anchors_verbatim": anchors_verbatim}


def findings_of(record: list[dict]) -> list[dict]:
    """The findings a proof record refuses with — the ONE reading of "did a lane fail",
    and it lives here rather than at the caller because the caller is a DEVICE with a
    sleep seam. A gate's verdict and the tool that decides what passing means must stay
    on the same side of that seam, or the device would import the gate tool and be a
    gate again (bin/cmd/determinism, 2026-08-13).

    Not a filter over the findings lists alone: an entry that FAILS while carrying no
    finding is a lane that refused without saying why, and that is louder here than a
    silent drop at the caller.
    """
    out = []
    for entry in record:
        if gate.passed(entry):
            continue
        found = entry["values"]["findings"]
        out.extend(found or [{
            "check": entry["source"].split(".")[-1],
            "finding": "lane %s refused and named no finding — a refusal with no "
                       "sentence is the silence the record exists to end"
                       % entry["identity"],
            "evidence": {"expected": entry["expected"], "actual": entry["actual"]},
        }])
    return out

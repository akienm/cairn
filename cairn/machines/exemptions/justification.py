"""Does an exemption entry's DECLARED justification resolve?

Two kinds, and the kind is DECLARED — this module never reads English to decide
which test applies, and never judges the quality of a no-other-way statement.
That is what keeps it deterministic (Akien's standing rule: nothing in an
inspector or a gate may be an LLM), and it is also the honest bound: whether an
impossibility argument is a GOOD one stays the model's judgment, not a sieve's.

  ruling        evidence is a decision id under CairnCommons/decisions/ that
                resolves, is kind "ruling", and is confirmed.
  no-other-way  evidence is a non-empty statement of the impossibility.

THE STORE IS CORROSION'S, NOT A SECOND ONE. ``citation._rulings_store`` and
``citation.ruling_covers_path`` are composed rather than reimplemented — there
is one answer in this system to "where do confirmed rulings live", and a second
copy of it would be the exact drift this component exists to catch.

WHY A PATH-COVERING CHECK IS NOT ENOUGH ON ITS OWN, measured 2026-09-10: the
ruling behind the device-isolation exemption is
``2026-08-31-no-cross-device-imports``, whose ``what_conforms`` spells its paths
repo-prefixed (``cairn/cairn/machines/build_inspector/inspector.py``) while the
set spells them repo-relative. ``ruling_covers_path`` therefore answers None for
a citation that is real. So the entry names the decision ID and this module
resolves it directly; path-covering is accepted as a SECOND way to pass, never
as the only one.
"""
from __future__ import annotations

import json

from cairn.machines.corrosion.citation import _rulings_store, ruling_covers_path

LEGAL_KINDS = ("ruling", "no-other-way")


def ruling_resolves(decision_id: str) -> tuple[bool, str]:
    """Does this decision id open as a CONFIRMED ruling? Returns (ok, why_not)."""
    if not isinstance(decision_id, str) or not decision_id.strip():
        return False, "evidence is empty — a ruling kind must name a decision id"
    store = _rulings_store()
    path = store / (decision_id.strip() + ".json")
    if not path.is_file():
        return False, "no decision file at %s" % path.name
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, "decision file unreadable: %s" % e
    if not isinstance(record, dict):
        return False, "decision file is not an object"
    if record.get("kind") != "ruling":
        return False, "decision is kind %r, not 'ruling'" % record.get("kind")
    if not record.get("confirmed"):
        return False, "ruling is not confirmed"
    return True, ""


def justification_lack(entry: dict) -> str:
    """The reason this entry's declared justification does not stand, or "".

    Returns the LACK rather than a boolean, so a caller reporting a red can say
    which of the several ways it failed — the same choice ``exemption_of`` made
    one rung down, and for the same reason.
    """
    if not isinstance(entry, dict):
        return "entry is not an object"
    eid = entry.get("id")
    if not isinstance(eid, str) or not eid.strip():
        return "entry carries no id"
    path = entry.get("path")
    if not isinstance(path, str) or not path.strip():
        return "entry carries no path — an exemption with no site is unjudgeable"
    kind = entry.get("justification_kind")
    if kind not in LEGAL_KINDS:
        return ("justification_kind is %r — it must be one of %s; an exemption "
                "that declares neither cites a ruling nor states an "
                "impossibility" % (kind, " or ".join(repr(k) for k in LEGAL_KINDS)))
    evidence = entry.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return "evidence is missing or empty for justification_kind %r" % kind
    if kind == "ruling":
        ok, why = ruling_resolves(evidence)
        if ok:
            return ""
        covering = ruling_covers_path(path)
        if covering:
            return ""
        return "declared ruling does not resolve: %s" % why
    return ""

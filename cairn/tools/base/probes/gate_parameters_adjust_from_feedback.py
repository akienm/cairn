"""PROBE — gate parameters adjust from feedback.

Berth for the WATCHME that ticket scheduled-llm-gate-inspection (b0c0c47835c1)
carries. Fires when structured gate feedback accumulates past a threshold,
sends the feedback to Hex (through a resolver injected in context — no
inference_domain import from tool-space), and routes adjustment proposals
through TransitionGate.adjust().

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge
that re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.base.transitions import BUILD_GATE

_OWNING_TICKET = "scheduled-llm-gate-inspection"
_MIN_FEEDBACK = 5
_SEEDS_DIR = Path(__file__).resolve().parents[3] / "machines" / "build_inspector" / "sieves"


def _read_feedback() -> list[dict]:
    fb_dir = BUILD_GATE._feedback_dir
    if fb_dir is None or not fb_dir.is_dir():
        return []
    records = []
    for f in sorted(fb_dir.glob("*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return records


def _current_dials() -> dict:
    tree = BUILD_GATE._tree
    if tree is None or not tree.is_dir():
        return {}
    dials = {}
    for f in sorted(tree.glob("*.json")):
        if f.name == "feedback":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("dials"):
                dials[data["name"]] = data["dials"]
        except (json.JSONDecodeError, OSError, KeyError):
            continue
    return dials


def build_prompt(records: list[dict], dials: dict) -> str:
    lines = [
        "You are reviewing gate inspection feedback for the Cairn build system.",
        "Below is accumulated feedback from %d gate firings." % len(records),
        "",
        "Each record shows the gate name, verdict (green/red), check counts,",
        "and mismatches (on red). Your task: propose parameter adjustments to",
        "sieve dials that would improve the inspection quality.",
        "",
        "Current sieve parameters (dials — empty means no adjustments yet):",
        json.dumps(dials, indent=2),
        "",
        "Feedback records:",
        json.dumps(records, indent=2),
        "",
        "Respond with a JSON array of adjustment proposals:",
        '[{"sieve": "<name>", "dial": "<dial_name>", "value": <new_value>, '
        '"reason": "<why this adjustment>"}]',
        "",
        "Return [] if no adjustment is needed.",
    ]
    return "\n".join(lines)


def parse_proposals(response: str) -> list[dict]:
    text = response.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < 0:
        return []
    try:
        proposals = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    valid = []
    for p in proposals:
        if not isinstance(p, dict):
            continue
        if not all(k in p for k in ("sieve", "dial", "value")):
            continue
        valid.append(p)
    return valid


def inspect(records: list[dict], resolver) -> dict:
    """Call Hex with accumulated feedback, return adjustment results.

    resolver: callable(prompt_str) -> response_str. Injected by the shim from
    inference_domain — this module never imports it (no cross-device import from
    tool-space).
    """
    dials = _current_dials()
    prompt = build_prompt(records, dials)
    response = resolver(prompt)
    proposals = parse_proposals(response)
    adjustments = []
    for p in proposals:
        try:
            result = BUILD_GATE.adjust(p["sieve"], p["dial"], p["value"])
            result["reason"] = p.get("reason", "")
            adjustments.append(result)
        except ValueError as e:
            adjustments.append({"error": str(e), "proposal": p})
    return {
        "records_inspected": len(records),
        "proposals": proposals,
        "adjustments": adjustments,
    }


def _trigger(now, context: dict) -> bool:
    return len(_read_feedback()) >= context.get("min_feedback", _MIN_FEEDBACK)


def _carry(context: dict) -> dict:
    records = _read_feedback()
    resolver = context.get("resolver")
    if resolver is None:
        return {
            "error": "no resolver in context — inference_domain not injected",
            "records_count": len(records),
            "ticket": owning_ticket(_OWNING_TICKET),
        }
    result = inspect(records, resolver)
    result["ticket"] = owning_ticket(_OWNING_TICKET)
    return result


def _enough(context: dict) -> bool:
    tree = BUILD_GATE._tree
    if tree is None or not tree.is_dir():
        return False
    count = 0
    for seed_file in sorted(_SEEDS_DIR.glob("*.json")):
        living = tree / seed_file.name
        if not living.exists():
            continue
        try:
            seed_data = json.loads(seed_file.read_text(encoding="utf-8"))
            live_data = json.loads(living.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if seed_data.get("dials", {}) != live_data.get("dials", {}):
            count += 1
    return count >= 3


PROBE = Probe(
    why="does the LLM inspection loop produce parameter adjustments from gate feedback? "
        "fires when feedback accumulates, sends it to Hex, and routes proposals through "
        "TransitionGate.adjust() — the founding question of whether calibration learns",
    trigger=_trigger,
    to=BUILD_GATE.notifies,
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)

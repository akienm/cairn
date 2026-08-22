"""Watchme probe: the inference ticket comes back whole.

Reads the standing `inference_calls` log and judges each row's wholeness:
does the answer carry the host's raw response body?

Rows predating the build (no body on the answer) are UNKNOWABLE with a per-row
why — the honest starting reading is expected to be zero countable, and that is
a starting state, not a green.

The probe carries no authority (Law 6). It deposits a finding and pokes.

    python3 cairn/devices/inference_domain/probes/the_ticket_comes_back_whole.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain import domain
from cairn.tools.base.probe import Probe, owning_ticket


def judge_rows(rows: list[dict]) -> dict:
    """Judge a population of inference_calls rows for wholeness.

    Returns a summary with per-row readings so the watch can count and classify.
    """
    whole = []
    unknowable = []
    broken = []

    for row in rows:
        answer = row.get("answer")
        verdict = row.get("verdict", "")
        canonical = (row.get("canonical") or "")[:80]

        if answer is None:
            unknowable.append({
                "canonical": canonical,
                "why": f"answer is NULL (verdict={verdict})",
            })
        elif not isinstance(answer, dict):
            broken.append({
                "canonical": canonical,
                "why": f"answer is {type(answer).__name__}, not a dict",
            })
        elif "body" in answer:
            whole.append({"canonical": canonical})
        else:
            unknowable.append({
                "canonical": canonical,
                "why": "answer carries no 'body' key — predates the build",
            })

    return {
        "total": len(rows),
        "whole": len(whole),
        "unknowable": len(unknowable),
        "unknowable_rows": unknowable,
        "broken": len(broken),
        "broken_rows": broken,
    }


def main() -> int:
    try:
        tickets = domain.read_ticket(table=domain.CACHE)
    except Exception as e:
        print(f"cannot read the standing log: {e}")
        print("FINDING — the reader cannot reach inference_calls")
        return 1

    result = judge_rows(tickets)

    print(f"inference_calls population: {result['total']}")
    print(f"  whole:       {result['whole']}")
    print(f"  unknowable:  {result['unknowable']}")
    print(f"  broken:      {result['broken']}")

    if result["unknowable_rows"]:
        print(f"\nunknowable rows ({result['unknowable']}):")
        for u in result["unknowable_rows"][:10]:
            print(f"  {u['canonical']}  — {u['why']}")
        if result["unknowable"] > 10:
            print(f"  ... and {result['unknowable'] - 10} more")

    if result["broken_rows"]:
        print(f"\nbroken rows ({result['broken']}):")
        for b in result["broken_rows"]:
            print(f"  {b['canonical']}  — {b['why']}")

    if result["broken"]:
        print(f"\nFINDING — {result['broken']} broken row(s)")
        return 1

    if result["whole"] == 0:
        print("\nSTARTING STATE — zero whole rows; the probe has nothing to count yet")
        return 0

    print(f"\nGREEN — {result['whole']} whole, {result['unknowable']} unknowable (pre-build)")
    return 0


_OWNING_TICKET = "the-inference-ticket-comes-back-whole"
_HORIZON = 1000


def _read_population():
    try:
        return domain.read_ticket(table=domain.CACHE)
    except Exception:
        return []


def _trigger(now, context: dict) -> bool:
    result = judge_rows(_read_population())
    return result["broken"] > 0


def _enough(context: dict) -> bool:
    result = judge_rows(_read_population())
    return result["whole"] > 0 and result["broken"] == 0


def _carry(context: dict) -> dict:
    result = judge_rows(_read_population())
    return {
        "finding": f"{result['broken']} broken row(s) in inference_calls",
        "total": result["total"],
        "whole": result["whole"],
        "unknowable": result["unknowable"],
        "broken": result["broken"],
        "broken_rows": result["broken_rows"][:10],
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the inference ticket must come back whole — every answer carries the host's "
        "raw response body so the reader can inspect what the host actually said",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    raise SystemExit(main())

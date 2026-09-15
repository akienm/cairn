"""PROBE — does the review lane hold ONLY what his head has to settle?

Berth for the WATCHME(the_lane_holds_only_his_decisions) that ticket fb988505c5cb
measurement-drains-the-review-lane carries. Berthed beside cairn/tools/operator_inbox
because that is WHAT IT WATCHES: the ARTIFACTS AWAITING REVIEW lane the banner and the
inbox print — the lane that, since this ticket, drains by measurement (a berth whose
ticket has crossed into a terminal cursor is not awaiting his review; Law 9's ruling
2026-08-15, "anything settled by measurment trumps approvals by even me").

THE MEASUREMENT. Two counts, both against the ticket's falsifier:

  (a) pending berths whose ticket was terminal at render — MUST BE 0. Read the lane as
      Akien sees it (``pending_reviews()``), then independently map every pending berth to
      the cursors of the tickets that name it (``berth_ticket_cursors``) and ask
      ``is_terminal`` of each. A berth in the lane with a terminal ticket is the drain
      failing to drain.
  (b) drained berths later re-raised by Akien — MUST BE 0. The WRONG-INTENT clause of the
      falsifier: "Akien reports a decision he needed to see drained — one instance reds
      the ticket." Measured as questions bound to this ticket that HE raised (raised_by
      not the cc caller class) after the build — the one channel his correction rides
      (ticket 9adc6fddf185: a decision is an open question bound to its ticket).

TRIGGER: every heartbeat pulse (the ground loop's discovery walk pulses any
``probes/*.py`` with a module-level PROBE — ``cairn/devices/cairn/machines/ground_loop/
discovery.py``). The ticket's decision line 9 said "poked by the inbox after it computes
the lane"; the standing physics is that the beat pulses it, and one pulse IS one render
of the lane through the same function the inbox calls. Fires when either count is
non-zero.

ENOUGH: twenty consecutive clean renders (both counts 0) — then the probe reports enough
and stops counting. Or the first lack, which names itself and stops.

CARRIER: a verdict-shaped dict against the ticket's falsifier: the lane size, the full
census size, the drained count, the terminal-in-lane berths (with cursors), the re-raised
questions.

ROOTS. Every read takes its roots from the pulse ``context`` when present (``root``,
``reviewed_path``, ``tickets``, ``ideas``, ``questions``) so a proof can hand it a scratch
world; absent those it reads what ``pending_reviews`` reads — never the live commons under
a scratch root (ticket decision line 8).

AUTHORITY: none. This probe deposits and pokes; codemother, as owner of the care of the
code, reads it (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "fb988505c5cb"
_ENOUGH_RENDERS = 20
_CC_CALLER = "cc"

_consecutive_clean = 0
_lack_seen: dict | None = None


def _questions_root(context: dict) -> Path | None:
    given = context.get("questions")
    if given:
        return Path(given)
    from cairn.tools.question.question import QUESTIONS_DIR
    return Path(QUESTIONS_DIR)


def _re_raised(context: dict) -> list[dict]:
    """Questions bound to this ticket that Akien raised — his correction channel."""
    qdir = _questions_root(context)
    if qdir is None or not qdir.exists():
        return []
    out: list[dict] = []
    for p in sorted(qdir.glob("open-*.json")):
        try:
            doc = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict) or doc.get("ticket") != _OWNING_TICKET:
            continue
        raised_by = str(doc.get("raised_by", "")).strip().lower()
        if raised_by.startswith(_CC_CALLER):
            continue
        out.append({"id": doc.get("id", p.stem), "raised_by": doc.get("raised_by"),
                    "question": str(doc.get("question", ""))[:160]})
    return out


def _measure(context: dict) -> dict:
    from cairn.machines.skill_block.skill_block import berth_ticket_cursors, pending_reviews
    from cairn.tools.base.transitions import is_terminal

    roots = {k: context[k] for k in ("root", "reviewed_path", "tickets", "ideas") if context.get(k)}
    for k in ("root", "reviewed_path", "tickets", "ideas"):
        if k in roots:
            roots[k] = Path(roots[k])
    lane = pending_reviews(**roots)
    census = pending_reviews(drain=False, **roots)
    cursors = berth_ticket_cursors(tickets=roots.get("tickets"), ideas=roots.get("ideas"))

    terminal_in_lane = []
    for entry in lane:
        key = str(Path(entry["path"]).resolve())
        states = cursors.get(key, [])
        if any(is_terminal(s) for s in states):
            terminal_in_lane.append({"berth": entry["path"], "cursors": states})

    re_raised = _re_raised(context)
    return {
        "lane": len(lane),
        "census": len(census),
        "drained": len(census) - len(lane),
        "terminal_in_lane": terminal_in_lane,
        "re_raised": re_raised,
        "clean": not terminal_in_lane and not re_raised,
    }


def _trigger(now, context: dict) -> bool:
    global _lack_seen
    result = _measure(context)
    if not result["clean"]:
        _lack_seen = result
        return True
    return False


def _enough(context: dict) -> bool:
    global _consecutive_clean
    if _lack_seen:
        return True                      # the first lack names itself and stops
    result = _measure(context)
    if not result["clean"]:
        _consecutive_clean = 0
        return True
    _consecutive_clean += 1
    return _consecutive_clean >= _ENOUGH_RENDERS


def _carry(context: dict) -> dict:
    result = _measure(context)
    if result["terminal_in_lane"]:
        first = result["terminal_in_lane"][0]
        finding = (f"{len(result['terminal_in_lane'])} berth(s) in his lane with a terminal "
                   f"ticket; first {first['berth']} cursors={first['cursors']}")
    elif result["re_raised"]:
        first = result["re_raised"][0]
        finding = (f"Akien re-raised a drained decision: {first['id']} — {first['question']}")
    else:
        finding = (f"lane {result['lane']} of census {result['census']} "
                   f"({result['drained']} drained by measurement); zero terminal in lane, "
                   f"zero re-raised")
    return {
        "finding": finding,
        "measurement": result,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the review lane holds only what his head has to settle: a berth whose ticket "
        "measurement has already closed is not his to click, and a drained decision he "
        "had to re-raise is the wrong intent (Akien 2026-09-15: buried in things he has "
        "to look at again)",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "codemother", "kind": "efficacy",
          "falsifier_tooth": "fb988505c5cb (5) + WRONG INTENT: terminal-ticket berths in "
                             "the lane must be 0; drained decisions re-raised must be 0"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)


if __name__ == "__main__":
    print(json.dumps(_measure({}), indent=2, default=str))

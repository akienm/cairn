"""sail.py — CC charts, crosses and closes a ticket through the ticket machine (ticket 91a27edfdd81).

    python3 cairn/devices/cc/scripts/sail.py draft   <id> <spec.json>
    python3 cairn/devices/cc/scripts/sail.py chart   <id>
    python3 cairn/devices/cc/scripts/sail.py cross   <id> [TARGET --why W [--proven-by P ...] [--missing M ...]]
    python3 cairn/devices/cc/scripts/sail.py verdict <id> --observation "<what showed each criterion can fail>"

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10, Q#80/Q#81): a ticket crosses a gate by sending its
fileref to ``codemother``'s ``machines/<gate>/queueme``; the gate's own instance does the
work. This script is CC's hand on that: it drafts the plan, and then the TICKET asks the gate
(``cairn.machines.ticket.ticket.Ticket``) with CC as the sender. It imports nothing of
CodeMother's (RULE 1) — the three helpers it replaces (cross.py, chart_ticket.py,
verdict_ticket.py) each imported her machines and called them in CC's process.

- ``draft`` turns CC's chart spec into one draft per stage on the plan's ``chart`` — the
  fields each stage's door reads, never the ticket claim or the earlier berth, which the gate
  fills from the ticket itself.
- ``chart`` queues the ticket at orient through validate in turn (``Ticket.chart``).
- ``cross`` with no target queues it at the clearance gate, which derives the next step and
  the proofs. A TARGET is only FIXME or a disposition of the ticket's class — the back-edges
  and dispositions no gate makes — and rides ``cairn.tools.base.cross``; a forward TARGET is
  refused, because a forward crossing is the clearance gate's.
- ``verdict`` drafts the verdict from the validate berth's criteria, each claimed ``pass``,
  and queues it at the verdict gate, which runs every instrument and disposes every
  hypothesis itself; a claim its re-run disagrees with is refused there.

Every refusal exits 1 with the gate's own words.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.diagnostic import DiagnosticBase  # noqa: E402

SENDER = "CC"
HOLDER = "codemother"
CHART = ("orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate")
CONFIDENCE = 0.85
# The longest a gate may take to answer: the verdict gate runs every instrument (the bus
# socket itself waits 900 s, cairn/tools/bus_client/remote.py _TIMEOUT_S).
VERDICT_TIMEOUT_S = 890.0
# A chart waits as long as a gate's answer can take too: codemother's constrain gate runs every
# proof of the component as instruments, which took many minutes for the tester (2026-11-12),
# so a 120 s wait gave up while she kept going and the caller retried (ticket 8b171277190c).
CHART_TIMEOUT_S = 890.0
GATE_TIMEOUT_S = 120.0


class Asker(DiagnosticBase):
    """The participant CC hands a Ticket: a bus that asks codemother, with CC as the sender."""

    def __init__(self, bus=None) -> None:
        super().__init__()
        self._bus = bus

    def _dial(self):
        if self._bus is None:
            from cairn.tools.bus_client import reach
            self._bus = reach(HOLDER)
        return self._bus

    def request(self, **kw):
        kw.pop("channel", None)
        return self._dial().request(sender=SENDER, channel="personal", **kw)

    def post(self, **kw):
        kw.pop("channel", None)
        return self._dial().post(sender=SENDER, channel="personal", **kw)


def _ticket(tid: str, tickets_dir=None):
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(tid, tickets_dir=tickets_dir)


def drafts_of(spec: dict) -> dict:
    """``{stage: draft}`` for orient through validate, from CC's chart spec."""
    pieces = spec["pieces"]
    whats = [p["what"] for p in pieces]
    orient = {"request": spec["request"], "intent": spec["intent"], "scope": spec["scope"],
              "unknowns": list(spec.get("unknowns") or []), "confidence": CONFIDENCE,
              "provenance": {"intent": "claude", "scope": "claude"}}
    if spec.get("domain"):
        # An address off the complexity axis (bin/, for one) has no floor domain, so the
        # spec authors it; the door derives its provenance (2026-11-12, c3f5e1a0d924).
        orient["domain"] = spec["domain"]
    return {
        "orient": orient,
        "constrain": {"constraints": spec["constraints"], "bounds": spec["bounds"],
                      "unknowns": [], "confidence": CONFIDENCE,
                      "provenance": {"intent_ref": "floor", "bounds": "claude"}},
        "survey": {"sought": spec["sought"], "holdings": spec["holdings"],
                   "absences": spec["absences"], "unknowns": [], "confidence": CONFIDENCE,
                   "provenance": {"constrain_ref": "floor", "sought": "claude",
                                  "holdings": "claude", "absences": "claude",
                                  "unknowns": "claude"}},
        "decompose": {"sub_problems": [{k: p[k] for k in ("what", "why", "kind", "fills", "uses",
                                                            "writes_to")} for p in pieces],
                      "unknowns": [], "confidence": CONFIDENCE,
                      "provenance": {"survey_ref": "floor", "sub_problems": "claude",
                                     "unknowns": "claude"}},
        "triage": {"order": [{"what": p["what"], "why_now": p["why_now"]} for p in pieces],
                   "unknowns": [], "confidence": CONFIDENCE,
                   "provenance": {"decompose_ref": "floor", "order": "claude",
                                  "unknowns": "claude"}},
        "hypothesize": {"hypotheses": [{"piece": p["what"], "expect": p["expect"],
                                        "falsifier": p["falsifier"],
                                        "instrument": p["instrument"]} for p in pieces],
                        "unknowns": [], "confidence": CONFIDENCE,
                        "provenance": {"triage_ref": "floor", "hypotheses": "claude",
                                       "unknowns": "claude"}},
        "validate": {"criteria": [dict(c, covers=list(whats)) for c in spec["criteria"]],
                     "unknowns": [], "confidence": CONFIDENCE,
                     "provenance": {"hypothesize_ref": "floor", "criteria": "claude",
                                    "unknowns": "claude"}},
    }


def draft(tid: str, spec: dict, *, tickets_dir=None, out=print) -> int:
    t = _ticket(tid, tickets_dir)
    for stage, packet in drafts_of(spec).items():
        t.draft(stage, packet, why=f"{tid}: CC drafts chart.{stage} for its gate")
    out(f"{tid}: drafted {', '.join(CHART)}")
    return 0


def _said(reply: dict) -> str:
    if reply.get("lacks"):
        return "; ".join(f"[{x.get('kind')}] {x.get('why')}" for x in reply["lacks"])
    return str(reply.get("reason") or reply.get("error") or reply.get("after_crossing") or reply)


def chart(tid: str, *, participant=None, tickets_dir=None, out=print, err=None) -> int:
    err = err or (lambda s: print(s, file=sys.stderr))
    got = _ticket(tid, tickets_dir).chart(participant=participant or Asker(),
                                          timeout=CHART_TIMEOUT_S, stages=CHART)
    for one in got["stages"]:
        if one["passed"]:
            out(f"{one['stage']}: {one['reply'].get('berth')}")
    if not got["charted"]:
        last = got["stages"][-1]
        err(f"refused at {got['stopped_at']}: {_said(last['reply'])}")
        return 1
    return 0


def cross(tid: str, target: str | None = None, *, why: str | None = None, proven_by=None,
          missing=None, participant=None, tickets_dir=None, crosser=None, out=print,
          err=None) -> int:
    err = err or (lambda s: print(s, file=sys.stderr))
    t = _ticket(tid, tickets_dir)
    if target is None:
        got = t.queueme("clearance", participant=participant or Asker(), timeout=GATE_TIMEOUT_S)
        reply = got["reply"]
        if not got["queued"] or not reply.get("workflow") or reply.get("after_crossing"):
            err(f"clearance refused {tid}: {_said(reply)}")
            return 1
        out(reply["workflow"])
        return 0
    from cairn.tools.base import transitions
    wf = transitions.parse_workflow(t.workflow)
    class_def = transitions.load_class_def(wf.node_class)
    tgt = transitions.canon_target(wf, target, class_def)
    if tgt != "FIXME" and not transitions.is_disposition(tgt, class_def):
        err(f"{tgt} is a forward crossing: it queues at the clearance gate "
            f"(sail.py cross {tid}), never by name")
        return 1
    if not why:
        err(f"a crossing into {tgt} needs --why")
        return 1
    if crosser is None:
        from cairn.tools.base.cross import cross as crosser
    kw = {"actor": SENDER, "why": why, "proven_by": list(proven_by or []) or None,
          "missing": list(missing or []) or None}
    if tickets_dir is not None:
        kw["tickets_dir"] = Path(tickets_dir)
    try:
        new = crosser(tid, tgt, **kw)
    except Exception as exc:  # noqa: BLE001 — every refusal is said, verbatim, and writes nothing
        err(f"refused: {type(exc).__name__}: {exc}")
        return 1
    out(new)
    return 0


def verdict_draft(validate: dict, observation: str) -> dict:
    """The verdict draft: each validate criterion's claim and instrument verbatim, claimed pass.
    The dispositions are not drafted — the verdict gate observes them."""
    verdicts = []
    for c in validate.get("criteria") or []:
        v = {"claim": c["claim"], "instrument": c["instrument"], "outcome": "pass",
             "evidence": "claimed pass by CC; the verdict door's own re-run of this instrument is "
                         "the reading, recorded beside it as observed_runs",
             "discriminating_observation": observation}
        if c.get("timeout_s") is not None:
            v["timeout_s"] = c["timeout_s"]
        verdicts.append(v)
    return {"verdicts": verdicts}


def verdict(tid: str, observation: str, *, participant=None, tickets_dir=None, out=print,
            err=None) -> int:
    err = err or (lambda s: print(s, file=sys.stderr))
    if not (observation or "").strip():
        err("a verdict needs --observation: what showed each criterion's instrument can fail")
        return 1
    t = _ticket(tid, tickets_dir)
    ref = t.berth("validate")
    if not ref:
        err(f"{tid} carries no validate berth: chart it through the gates first (sail.py chart)")
        return 1
    validate = json.loads(Path(ref).read_text(encoding="utf-8"))
    t.draft("verdict", verdict_draft(validate, observation),
            why=f"{tid}: CC drafts the verdict, every criterion claimed pass")
    got = t.queueme("verdict", participant=participant or Asker(), timeout=VERDICT_TIMEOUT_S)
    reply = got["reply"]
    if not got["queued"] or reply.get("passed") is not True:
        err(f"the verdict gate refused {tid}: {_said(reply)}")
        return 1
    out(reply.get("berth"))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sail.py", description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    d = sub.add_parser("draft")
    d.add_argument("ticket")
    d.add_argument("spec")
    c = sub.add_parser("chart")
    c.add_argument("ticket")
    x = sub.add_parser("cross")
    x.add_argument("ticket")
    x.add_argument("target", nargs="?")
    x.add_argument("--why")
    x.add_argument("--proven-by", action="append", default=[])
    x.add_argument("--missing", action="append", default=[])
    v = sub.add_parser("verdict")
    v.add_argument("ticket")
    v.add_argument("--observation", required=True)
    a = ap.parse_args(argv)
    if a.verb == "draft":
        return draft(a.ticket, json.loads(Path(a.spec).read_text(encoding="utf-8")))
    if a.verb == "chart":
        return chart(a.ticket)
    if a.verb == "cross":
        return cross(a.ticket, a.target, why=a.why, proven_by=a.proven_by, missing=a.missing)
    return verdict(a.ticket, a.observation)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

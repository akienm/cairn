"""chart/live.py — the tree stratum against the real embed seam, through the one door.

The thin edge where the doors compose: text → vector rides inference_domain's resolve
verb, metered and cached; the vector then feeds the tree tool's pure verbs. Depositing a
berth (``learn``, and the drain both verbs run before serving) is codemother acting, so
it is ASKED of codemother over the bus (ticket e8fe361a5b2f) — this skill holds none of
her machines.
One embed per /chart crossing (the request, cached on repeat), one per fresh
deposit-back — the whole embed cost of the stratum, readable in the yield report.

    python3 -m skills.chart.live counsel "<request>" [nexus] [owner]  # the walk, live
    python3 -m skills.chart.live learn <berth-path> [nexus]           # deposit-back one packet
    python3 -m skills.chart.live moreabout "<ask>" [nexus] [owner]    # the learning door
    python3 -m skills.chart.live draft <ticket> <stage> <packet.json> # the stage's draft, on the plan
    python3 -m skills.chart.live queue <ticket> <stage>               # the ticket queues at that gate
    # exit 0 = the verb returned; a refusal prints loud and exits 1; exit 3 = learn or
    # counsel SERVED, but an owed verdict failed to deposit in the drain (ticket 4818f7f37e1e)
    # [owner] serves the grafted tenants: `counsel "<text>" corrections orient` walks
    # orient's correction corpus; default is codemother's own nexi (OWNER).
    # moreabout = walk + write-back in ONE act, one embed serving both — the invocation
    # IS the training signal (an opt-in signal would be skipped exactly when the honest
    # datum is least flattering).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

from skills.chart.dial import dial
from skills.moreabout.moreabout import expand, signal
from cairn.tools.tree.tree import counsel
from cairn.tools.bus_client import reach
from cairn.tools.system_word import fold_head
from cairn.tools.base.diagnostic import DiagnosticBase

_BUS = None
_SENDER = "chart"
DRAIN_FAILED_EXIT = 3  # served, but an owed deposit failed — 1 stays the verb's own refusal
EMBED_MODEL = "nomic-embed-text"
# codemother owns her learning (Akien 2026-11-05); ticket 67d446a1a33a
OWNER = "codemother"


def _bus():
    """One exchange, no beat: codemother answers deposit/drain, inference_domain embeds."""
    global _BUS
    if _BUS is None:
        _BUS = reach("codemother", "inference_domain")
    return _BUS


def _embed(text: str) -> list[float]:
    """text -> vector over inference_domain's resolve verb (its public interface)."""
    reply = _bus().request(sender=_SENDER, to="inference_domain", verb="resolve",
                           why="chart embed",
                           body={"kind": "embed", "prompt": text, "model": EMBED_MODEL,
                                 "domain": "research"})
    return reply["body"]["answer"]["vector"]


def _ask_codemother(verb: str, body: dict) -> dict:
    """Depositing is codemother acting (ticket e8fe361a5b2f): ask her over the bus. A
    bounce or a refusal comes back as accepted False with the reason, never raised away."""
    reply = _bus().request(sender=_SENDER, to="codemother", verb=verb,
                           why="chart %s" % verb, body=body)
    got = (reply or {}).get("body") or {}
    if got.get("is_bounce"):
        return {"accepted": False, "reason": "codemother bounced %r: %s" % (verb, got)}
    return got


def _drain_before_serving() -> list[dict]:
    """The one call both verbs make. Failures are named on stderr as well as in the
    served payload — a diagnostic surface is loud (Law 7), and a counsel read that
    quietly ate a failed deposit would be the silent lapse this stone exists to end."""
    got = _ask_codemother("drain", {})
    if not got.get("accepted"):
        print("DRAIN FAILED — codemother did not drain the pending verdicts: %s"
              % got.get("reason", got), file=sys.stderr)
        return [{"berth": None, "failed": got.get("reason", str(got)), "still_pending": True}]
    drained = got.get("drained") or []
    for entry in drained:
        if "failed" in entry:
            # The drain rendered the line once and wrote it to the ledger (ticket
            # 637d206be821); print THAT line — a second rendering here would drift.
            # The fallback is for a codemother that predates the carried line.
            print(entry.get("stderr") or "DEPOSIT FAILED — %s STANDS PENDING on the ledger: %s"
                  % (entry["berth"], entry["failed"]), file=sys.stderr)
    return drained


def _served(drained: list[dict]) -> int:
    """The exit of a verb that SERVED: 3 when any owed deposit failed in the drain, so a
    caller sees it in the status as well as on stderr (ticket 4818f7f37e1e)."""
    return DRAIN_FAILED_EXIT if any("failed" in e for e in drained) else 0


def _counsel(argv: list[str]) -> int:
    if not argv:
        print('usage: live counsel "<request>" [nexus] [owner]', file=sys.stderr)
        return 1
    request, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    owner = argv[2] if len(argv) > 2 else OWNER
    drained = _drain_before_serving()  # pending verdicts land before the walk reads
    got = counsel(_embed(request), nexus=nexus, owner=owner)
    print(json.dumps({
        "request": request,
        "owner": owner,
        "drained": drained,
        "counsel": {k: v for k, v in got.items() if k != "walk"},
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "standing": n["standing"], "provenance": n["provenance"]}
                 for n in got["walk"]],
    }, indent=2, default=str))
    return _served(drained)


def _learn(argv: list[str]) -> int:
    if not argv:
        print("usage: live learn <berth-path> [nexus]", file=sys.stderr)
        return 1
    berth = argv[0]
    drained = _drain_before_serving()  # pending verdicts land before this deposit
    body = {"berth": os.path.abspath(berth)}
    if len(argv) > 1:
        body["nexus"] = argv[1]
    reply = _ask_codemother("deposit", body)
    if not reply.get("accepted"):
        print("DEPOSIT REFUSED — %s: %s" % (berth, reply.get("reason", reply)), file=sys.stderr)
        return 1
    got, nexus = reply.get("learn"), reply.get("nexus")
    print(json.dumps({"learn": got, "berth": berth, "nexus": nexus,
                      "drained": drained,
                      "dial": dial()["nexi"].get(nexus, {}).get("aggregate")},
                     indent=2, default=str))
    return _served(drained)


def _moreabout(argv: list[str]) -> int:
    if not argv:
        print('usage: live moreabout "<ask>" [nexus] [owner] [--context build]',
              file=sys.stderr)
        return 1
    context = None
    if "--context" in argv:
        idx = argv.index("--context")
        if idx + 1 < len(argv):
            context = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2:]
        else:
            argv = argv[:idx]
    ask, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    kw = {"owner": argv[2]} if len(argv) > 2 else {}
    vector = _embed(ask)
    got = expand(vector, nexus=nexus, **kw)
    top = got["expansions"][0] if got["expansions"] else None
    about = (top.get("provenance") or {}).get("source") if top else None
    sig = signal(ask, vector, date=date.today().isoformat(), nexus=nexus,
                 about=about, context=context, **kw)
    print(json.dumps({"ask": ask, "expansion": got, "signal": sig},
                     indent=2, default=str))
    return 0


def _chain(argv: list[str]) -> int:
    """The resolver verb (ticket berths-carry-request-identity): print the standing
    chain for a ticket — per stage, the latest claiming berth. Tree-free and
    host-free by construction (a pure glob walk), so it works on a machine where
    the embed host is down: recovery must not depend on the fanciest dependency."""
    if not argv:
        print("usage: python3 -m skills.chart.live chain <ticket>", file=sys.stderr)
        return 1
    from cairn.tools.chain.chain import chain_for_ticket
    print(json.dumps({"ticket": argv[0], "chain": chain_for_ticket(argv[0])},
                     indent=2))
    return 0


class _Gates(DiagnosticBase):
    """The participant the ticket is handed: a bus asking codemother, sent as chart. The ticket
    asks the gate itself (outline 9.6: each stage is a gate answering queueme <fileref>); this
    skill only drafts and hands it a hand to ask with."""

    def request(self, **kw):
        return _bus().request(sender=_SENDER, **kw)

    def post(self, **kw):
        return _bus().post(sender=_SENDER, **kw)


def _gates():
    return _Gates()


# a stage's gate may take a while to answer: the verdict runs every instrument
_GATE_TIMEOUT_S = 120.0


def _draft(argv: list[str]) -> int:
    """Put the packet file's JSON on the plan as ``chart.<stage>`` (Ticket.draft), the draft the
    stage's gate reads. A stage outside the chart is refused before anything is written."""
    if len(argv) != 3:
        print("usage: python3 -m skills.chart.live draft <ticket> <stage> <packet.json>",
              file=sys.stderr)
        return 1
    from cairn.machines.ticket.ticket import Ticket
    tid, stage, path = argv
    try:
        packet = json.loads(open(path, encoding="utf-8").read())
        Ticket.at(tid).draft(stage, packet, why=f"{tid}: /chart drafts chart.{stage} for its gate")
    except (ValueError, OSError) as exc:
        print(f"draft refused: {exc}", file=sys.stderr)
        return 1
    print(f"{tid}: drafted chart.{stage}")
    return 0


def _queue(argv: list[str]) -> int:
    """The ticket queues itself at ``stage``'s gate (Ticket.chart over that one stage) and the
    berth the gate wrote is printed. A gate that refuses, or one nobody answers, exits 1 with
    what it said."""
    if len(argv) != 2:
        print("usage: python3 -m skills.chart.live queue <ticket> <stage>", file=sys.stderr)
        return 1
    from cairn.machines.ticket import ticket as T
    from cairn.machines.ticket.ticket import CHART, VERDICT, Ticket
    tid, stage = argv
    if stage not in CHART + (VERDICT,):
        print(f"queue refused: {stage!r} is not a chart stage ({', '.join(CHART)}, {VERDICT})",
              file=sys.stderr)
        return 1
    try:
        # the reply may come after its timeout; the berth the gate writes is the answer (0bcb816d6e9c)
        got = Ticket.at(tid, settle=T.STAGE_BUDGET_S).chart(
            participant=_gates(), timeout=_GATE_TIMEOUT_S, stages=(stage,))
    except (ValueError, OSError) as exc:
        print(f"queue refused: {exc}", file=sys.stderr)
        return 1
    one = got["stages"][-1]
    reply = one["reply"]
    if one["passed"]:
        print(f"{stage}: {reply.get('berth')}")
        return 0
    lacks = reply.get("lacks") or []
    said = ("; ".join(f"[{x.get('kind')}] {x.get('why')}" for x in lacks) if lacks
            else str(reply.get("reason") or reply.get("error") or reply))
    print(f"refused at {stage}: {said}", file=sys.stderr)
    return 1


def _main(argv: list[str]) -> int:
    argv = fold_head(argv, 1)  # system words fold (ruled 2026-09-07); the rest is verbatim
    if argv and argv[0] == "chain":
        return _chain(argv[1:])
    if argv and argv[0] == "counsel":
        return _counsel(argv[1:])
    if argv and argv[0] == "learn":
        return _learn(argv[1:])
    if argv and argv[0] == "moreabout":
        return _moreabout(argv[1:])
    if argv and argv[0] == "draft":
        return _draft(argv[1:])
    if argv and argv[0] == "queue":
        return _queue(argv[1:])
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

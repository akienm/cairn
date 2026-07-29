"""chart/live.py — the tree stratum against the real embed seam, through the one door.

The thin edge where the doors compose (the same shape as librarian/live.py, whose
``embed_via_domain`` this reuses rather than re-derives): text → vector rides
inference_domain, metered and cached; the vector then feeds chart/tree.py's pure verbs.
One embed per /chart crossing (the request, cached on repeat), one per fresh
deposit-back — the whole embed cost of the stratum, readable in the yield report.

    python3 -m cairn.chart.live counsel "<request>" [nexus] [owner]  # the walk, live
    python3 -m cairn.chart.live learn <berth-path> [nexus]           # deposit-back one packet
    python3 -m cairn.chart.live moreabout "<ask>" [nexus] [owner]    # the learning door
    # exit 0 = the verb returned; a refusal prints loud and exits 1
    # [owner] serves the grafted tenants: `counsel "<text>" corrections orient` walks
    # orient's correction corpus; default is chart's own nexi.
    # moreabout = walk + write-back in ONE act, one embed serving both — the invocation
    # IS the training signal (an opt-in signal would be skipped exactly when the honest
    # datum is least flattering).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

from cairn.chart.constrain import constrain_node_content, deposit_constrain
from cairn.chart.dial import dial
from cairn.chart.moreabout import expand, signal
from cairn.chart.orient import CAIRN_ROOT
from cairn.chart.decompose import decompose_node_content, deposit_decompose
from cairn.chart.hypothesize import deposit_hypothesize, hypothesize_node_content
from cairn.chart.survey import deposit_survey, survey_node_content
from cairn.chart.tree import counsel, deposit_learning, deposit_packet
from cairn.chart.triage import deposit_triage, triage_node_content
from cairn.chart.validate import deposit_validate, validate_node_content
from cairn.chart.verdict import (VerdictRefused, mark_deposited, pending,
                                 validate_verdict, verdict_node_content)
from cairn.librarian.live import embed_via_domain


def deposit_verdict(artifact: dict, vector, *, berth_path: str,
                    root: str = CAIRN_ROOT, nexus: str = "hypothesize",
                    conn=None) -> dict:
    """The verdict face on the deposit door (ticket proved-answers-the-chart): the
    dispositions become the HYPOTHESIZE tree's memory of what killed which — the
    'one day' deposit_hypothesize's docstring has promised since the brick landed.

    Lives HERE and not in verdict.py by construction: verdict.py is the tree-free
    validator both the exit gate and this face compose (the fire path from the
    chokepoint may never reach tree machinery — a verdict is always hardware);
    the tree side of the split is this module's side. Gate before seed, like
    every face: the artifact re-validates at the ONE door, and the berth must
    exist on disk."""
    validate_verdict(artifact, root=root)
    if not isinstance(berth_path, str) or not os.path.isfile(os.path.expanduser(berth_path)):
        raise VerdictRefused(
            "deposit_verdict: berth %r does not exist on disk — a node whose "
            "provenance points at nothing is fabricated attribution one layer up"
            % (berth_path,))
    content = verdict_node_content(artifact)
    provenance = {
        "source": berth_path,
        "validate_ref": artifact["validate_ref"],
        "ticket": artifact["ticket"],
    }
    return deposit_learning(nexus, content, vector, provenance, conn=conn)


def drain_pending(*, root: str = CAIRN_ROOT, nexus: str = "hypothesize",
                  embed=None, ledger_path: str | None = None, conn=None) -> list[dict]:
    """THE DRAIN (ticket the-deposit-rides-the-read, 2026-07-29): every verdict the
    emit chokepoint enqueued and nobody has deposited, landed through the ONE
    deposit door above — run by both door verbs BEFORE they serve.

    THE READ IS THE EVENT. Nothing polls and nothing schedules: the drain fires
    inside a door entry that was already happening, which is where the tree is
    already open and the db cost is already being paid (Law 1; 'reach for the
    event that already fires, never a clock'). The crossing side stayed tree-free
    so a netns-sealed crossing could enqueue identically — this is the other half,
    on the tree side, where the db is allowed.

    Law 7 at this exact seam: a deposit that raises leaves its ENQUEUED line
    standing (the record of truth keeps the obligation) and rides back named in
    the result (the presentation surface says so loudly) — and the verb still
    serves. A landing appends a ``deposited`` record, which is also the whole
    idempotence story: the second drain finds nothing pending, so no berth is ever
    deposited twice, and no line was ever edited to make that true.

    Returns one entry per pending berth: ``{"berth", "deposited"|"failed", ...}``.
    """
    embed = embed or embed_via_domain()
    drained = []
    for entry in pending(ledger_path=ledger_path):
        berth = entry["berth"]
        try:
            with open(os.path.expanduser(berth), encoding="utf-8") as fh:
                artifact = json.load(fh)
            got = deposit_verdict(artifact, embed(verdict_node_content(artifact)),
                                  berth_path=berth, root=root, nexus=nexus, conn=conn)
            mark_deposited(berth, got["node_id"], ledger_path=ledger_path)
            drained.append({"berth": berth, "deposited": got["node_id"],
                            "duplicate": got.get("duplicate"), "nexus": nexus})
        except Exception as e:  # noqa: BLE001 — deliberate: the door must still serve
            drained.append({"berth": berth, "failed": "%s: %s" % (type(e).__name__, e),
                            "still_pending": True})
    return drained


def _drain_before_serving() -> list[dict]:
    """The one call both verbs make. Failures are named on stderr as well as in the
    served payload — a diagnostic surface is loud (Law 7), and a counsel read that
    quietly ate a failed deposit would be the silent lapse this stone exists to end."""
    drained = drain_pending()
    for entry in drained:
        if "failed" in entry:
            print("DEPOSIT FAILED — %s STANDS PENDING on the ledger: %s"
                  % (entry["berth"], entry["failed"]), file=sys.stderr)
    return drained


def _counsel(argv: list[str]) -> int:
    if not argv:
        print('usage: live counsel "<request>" [nexus] [owner]', file=sys.stderr)
        return 1
    request, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    kw = {"owner": argv[2]} if len(argv) > 2 else {}
    drained = _drain_before_serving()  # pending verdicts land before the walk reads
    got = counsel(embed_via_domain()(request), nexus=nexus, **kw)
    print(json.dumps({
        "request": request,
        "drained": drained,
        "counsel": {k: v for k, v in got.items() if k != "walk"},
        "walk": [{"similarity": round(n["similarity"], 4), "content": n["content"],
                  "standing": n["standing"], "provenance": n["provenance"]}
                 for n in got["walk"]],
    }, indent=2, default=str))
    return 0


def _learn(argv: list[str]) -> int:
    if not argv:
        print("usage: live learn <berth-path> [nexus]", file=sys.stderr)
        return 1
    berth = argv[0]
    drained = _drain_before_serving()  # pending verdicts land before this deposit
    with open(berth, encoding="utf-8") as fh:
        packet = json.load(fh)
    if os.path.basename(berth).startswith("constrain-"):
        # Stage 2's deposit-back: the vector embeds the SAME rendering the node
        # deposits (constrain_node_content — one rendering, no drift).
        nexus = "constrain"
        got = deposit_constrain(packet, embed_via_domain()(constrain_node_content(packet)),
                                berth_path=berth)
    elif os.path.basename(berth).startswith("survey-"):
        nexus = "survey"
        got = deposit_survey(packet, embed_via_domain()(survey_node_content(packet)),
                             berth_path=berth)
    elif os.path.basename(berth).startswith("decompose-"):
        nexus = "decompose"
        got = deposit_decompose(packet, embed_via_domain()(decompose_node_content(packet)),
                                berth_path=berth)
    elif os.path.basename(berth).startswith("triage-"):
        nexus = "triage"
        got = deposit_triage(packet, embed_via_domain()(triage_node_content(packet)),
                             berth_path=berth)
    elif os.path.basename(berth).startswith("hypothesize-"):
        nexus = "hypothesize"
        got = deposit_hypothesize(packet,
                                  embed_via_domain()(hypothesize_node_content(packet)),
                                  berth_path=berth)
    elif os.path.basename(berth).startswith("validate-"):
        nexus = "validate"
        got = deposit_validate(packet,
                               embed_via_domain()(validate_node_content(packet)),
                               berth_path=berth)
    elif os.path.basename(berth).startswith("verdict-"):
        # The exit gate's write-back: what killed which lands in the HYPOTHESIZE
        # tree (the loop the brick promised), rendered once by verdict_node_content.
        nexus = "hypothesize"
        got = deposit_verdict(packet, embed_via_domain()(verdict_node_content(packet)),
                              berth_path=berth)
    else:
        nexus = argv[1] if len(argv) > 1 else "orient"
        got = deposit_packet(packet, embed_via_domain()(packet["intent"]),
                             berth_path=berth, nexus=nexus)
    print(json.dumps({"learn": got, "berth": berth, "nexus": nexus,
                      "drained": drained,
                      "dial": dial()["nexi"].get(nexus, {}).get("aggregate")},
                     indent=2, default=str))
    return 0


def _moreabout(argv: list[str]) -> int:
    if not argv:
        print('usage: live moreabout "<ask>" [nexus] [owner]', file=sys.stderr)
        return 1
    ask, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    kw = {"owner": argv[2]} if len(argv) > 2 else {}
    vector = embed_via_domain()(ask)
    got = expand(vector, nexus=nexus, **kw)
    top = got["expansions"][0] if got["expansions"] else None
    about = (top.get("provenance") or {}).get("source") if top else None
    sig = signal(ask, vector, date=date.today().isoformat(), nexus=nexus,
                 about=about, **kw)
    print(json.dumps({"ask": ask, "expansion": got, "signal": sig},
                     indent=2, default=str))
    return 0


def _main(argv: list[str]) -> int:
    if argv and argv[0] == "counsel":
        return _counsel(argv[1:])
    if argv and argv[0] == "learn":
        return _learn(argv[1:])
    if argv and argv[0] == "moreabout":
        return _moreabout(argv[1:])
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))

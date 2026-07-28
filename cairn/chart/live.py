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
import sys
from datetime import date

from cairn.chart.dial import dial
from cairn.chart.moreabout import expand, signal
from cairn.chart.tree import counsel, deposit_packet
from cairn.librarian.live import embed_via_domain


def _counsel(argv: list[str]) -> int:
    if not argv:
        print('usage: live counsel "<request>" [nexus] [owner]', file=sys.stderr)
        return 1
    request, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    kw = {"owner": argv[2]} if len(argv) > 2 else {}
    got = counsel(embed_via_domain()(request), nexus=nexus, **kw)
    print(json.dumps({
        "request": request,
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
    berth, nexus = argv[0], (argv[1] if len(argv) > 1 else "orient")
    with open(berth, encoding="utf-8") as fh:
        packet = json.load(fh)
    got = deposit_packet(packet, embed_via_domain()(packet["intent"]),
                         berth_path=berth, nexus=nexus)
    print(json.dumps({"learn": got, "berth": berth, "nexus": nexus,
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

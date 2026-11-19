"""WATCHME probe: an_outright_deletion_resolves_through_its_deleter (ticket 6e1d0a5c3b27).

THE HYPOTHESIS IT WATCHES (CC's answer under outline 0.6.1, not a question). When a build
deletes a file outright (no rename) and writes a forwarding order for it, that order is
enough: every ticket that charted the file resolves through it, and nobody has to copy the
order onto the charting tickets again. The founding case, press_office/CairnComponentOutline.txt
(e4a12d8e0cbf, 770decaf5), cost 6 hand copies before the resolver learned this; it is
excluded here because the copies were written before the hypothesis existed.

THE MEASUREMENT. Every file deleted by a commit since SINCE whose subject opens with a ticket
id, that git records no rename for, and that the deleter's own order forwards: a DISSOLUTION.
For each one, is it resolved for a ticket that carries no order (``_resolves_to`` with an id
no ticket holds), and how many OTHER tickets carry a copy of an order for it.

FIRES on a dissolution that does not resolve, or that a copy was written for (the hypothesis
is killed: copies are still being made). ENOUGH once ENOUGH_DISSOLUTIONS have been read,
every one resolved with no copy.

AUTHORITY: none. It deposits and pokes codemother's WATCHME gate (Law 6).
"""
from __future__ import annotations

import os

from cairn.tools.base.probe import Probe, Threshold, once, watch_carry

_TICKET_ID = "6e1d0a5c3b27"
SINCE = "2026-11-19"
FOUNDING = frozenset({"press_office/CairnComponentOutline.txt"})
NO_ORDER = "000000000000"  # a ticket id no ticket holds: it carries no order of its own
ENOUGH_DISSOLUTIONS = 1


def survey() -> dict:
    """Every rename-less deletion since SINCE that its deleter forwarded, judged."""
    from cairn.machines.build_inspector import inspector as insp
    from cairn.tools.base.ticket_file import plans, read_ticket
    try:
        lines = insp._git_lines(None, "log", "--diff-filter=D", "--since=" + SINCE,
                                "--name-only", "--format=@%s")
        renamed = {old for old, _new in insp.rename_records()}
    except insp.GitUnreadable as e:
        return {"reader_failed": str(e), "dissolutions": []}
    deleted, deleter = {}, None
    for line in lines:
        if line.startswith("@"):
            m = insp._TICKET_SUBJECT.match(line[1:])
            deleter = m.group(1) if m else None
        elif line.strip() and deleter and line not in deleted:
            deleted[line] = deleter
    tickets_dir = os.path.join(os.path.dirname(str(insp._TICKETS_ROOT)), "CairnCommons", "tickets")
    orders: dict = {}
    for filed in plans(tickets_dir) if os.path.isdir(tickets_dir) else []:
        try:
            t = read_ticket(filed)
        except (OSError, ValueError):
            continue
        if isinstance(t, dict):
            for old in insp._valid_orders(t.get("forwarding")):
                orders.setdefault(old, set()).add(t.get("id"))
    found = []
    for path, tid in sorted(deleted.items()):
        if path in FOUNDING or path in renamed or insp.ref_exists(path):
            continue
        if not insp._forwarding_map(tid).get(path):
            continue
        found.append({"address": path, "deleter": tid,
                      "resolved": bool(insp._resolves_to(path, NO_ORDER)),
                      "copies": sorted(x for x in orders.get(path, ()) if x != tid)})
    return {"reader_failed": None, "dissolutions": found}


def _bad(s: dict) -> list:
    return [d for d in s["dissolutions"] if not d["resolved"] or d["copies"]]


def _trigger(now, context: dict) -> bool:
    return bool(_bad(once(context, "survey", survey)))


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    return bool(_bad(s)) or (not s["reader_failed"]
                             and len(s["dissolutions"]) >= ENOUGH_DISSOLUTIONS)


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    bad = _bad(s)
    return {
        "dissolutions": s["dissolutions"][:20],
        "reader_failed": s["reader_failed"],
        "finding": (
            "%d rename-less dissolution(s) since %s needed a copy or did not resolve through "
            "the deleter's order: the hypothesis is killed" % (len(bad), SINCE)
        ) if bad else (
            "%d rename-less dissolution(s) since %s, each resolved through its deleter's order "
            "with no copy" % (len(s["dissolutions"]), SINCE)
        ),
    }


PROBE = Probe(
    why="6e1d0a5c3b27 lets a deleter's own order answer for a file deleted with no rename; "
        "the claim is that no hand copies an order again. This reads every such dissolution "
        "since the land and fires on one that still needed a copy or does not resolve.",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "6e1d0a5c3b27 hypothesis", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
    enough=_enough,
    thresholds=(
        Threshold(ENOUGH_DISSOLUTIONS, "rename-less dissolutions read, each resolved with no copy",
                  set_by="ticket 6e1d0a5c3b27 watchme: the next rename-less dissolution"),
    ),
    horizon=1000,
)

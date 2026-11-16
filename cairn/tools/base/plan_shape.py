"""THE CAST DOOR'S PLAN-SHAPE CHECK (moved out of transitions.py, ticket efcb2efe7dd3).

``_shape_lacks(doc, charter)`` names every lack of a ticket's plan against the store charter's
``plan_shapes``. It lived in transitions.py, and the rehearsal machine imports it, so reaching
the shape check pulled in all of transitions: gate_probes (socket) and inspect_wire (the bus and
its store). The inspector's verdict path imports rehearsal, so test_inspector_nexus's
fire-path tooth caught that reach (measured 2026-11-16 at 5dc2364a8adb's reseal). Here the
check imports only the standard library. transitions.py re-imports every name, so its callers
are unchanged.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


_CAST_REQUIRED: tuple[str, ...] = (
    "id", "title", "date", "owner", "owning_intention", "intention", "why", "traces_to",
    "how", "falsifier", "node_class", "workflow_and_state", "watchme", "sorted_berth",
    "intent_berth",
)

_CAST_ID = re.compile(r"^[0-9a-f]{12}$")


def _blank(v: object) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _paths_ok(v) -> bool:
    """A list of non-blank strings (an empty list is a claim: this line writes or reads nothing)."""
    return isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)


def _resolves(p: str, roots: list[Path]) -> bool:
    q = Path(p)
    if q.is_absolute():
        return q.exists()
    return any((r / q).exists() for r in roots)


def _outcome_lacks(doc: dict, spec: dict, charter: Path) -> list[str]:
    """Every lack of ``doc['outcomes']`` against the charter's ``plan_shapes.outcomes``: each
    line ``{n, claim, writes_to, reads, after?, via?}`` numbered 1..k, every ``reads`` a file, no
    more than ``max_items`` lines (``too_big`` names the split), and none of the ``excludes`` keys
    beside it. A line with no claim is refused: awaiting judgement is the migration's state
    (``plan.awaiting``), never a cast's."""
    lacks: list[str] = []
    beside = [k for k in spec.get("excludes") or [] if doc.get(k) is not None]
    if beside:
        lacks.append(f"outcomes beside {' and '.join(beside)}: a plan is outcomes, or "
                     f"decisions with a falsifier, never both")
    outs = doc.get("outcomes")
    if not isinstance(outs, list) or len(outs) < int(spec.get("min_items") or 1):
        return lacks + [f"outcomes is not a non-empty list: {repr(outs)[:80]}"]
    most = spec.get("max_items")
    if isinstance(most, int) and len(outs) > most:
        lacks.append(f"outcomes carries {len(outs)}, more than {most}: "
                     f"{spec.get('too_big') or 'too big'}")
    here = Path(__file__).resolve().parents[3]
    commons = charter.resolve().parent.parent
    roots = [here, commons, commons.parent]
    ns = [o.get("n") if isinstance(o, dict) else None for o in outs]
    for i, o in enumerate(outs):
        if not isinstance(o, dict):
            lacks.append(f"outcomes[{i}] is not an object: {repr(o)[:80]}")
            continue
        n = o.get("n")
        if not (isinstance(n, int) and not isinstance(n, bool)):
            lacks.append(f"outcomes[{i}].n is not an int: {n!r}")
        claim = o.get("claim")
        if not (isinstance(claim, str) and claim.strip()):
            lacks.append(f"outcomes[{i}] has no claim (awaiting judgement is the migration's "
                         f"state, never a cast's)")
        for k in [k for k in spec.get("each_requires") or [] if k in ("writes_to", "reads")]:
            if k not in o:
                lacks.append(f"outcomes[{i}] lacks {k}")
            elif not _paths_ok(o[k]):
                lacks.append(f"outcomes[{i}].{k} is not a list of non-blank strings: {repr(o[k])[:80]}")
        if spec.get("reads_resolve") and _paths_ok(o.get("reads")):
            lacks.extend(f"outcomes[{i}].reads {p!r} resolves to no file"
                         for p in o["reads"] if not _resolves(p, roots))
        after = o.get("after")
        if after is not None:
            ok = isinstance(after, list) and all(
                (isinstance(a, int) and not isinstance(a, bool) and a in ns and a != n)
                or (isinstance(a, str) and _CAST_ID.match(a)) for a in after)
            if not ok:
                lacks.append(f"outcomes[{i}].after is not a list of this plan's outcome numbers "
                             f"or 12-hex ticket ids: {repr(after)[:80]}")
        if "via" in o and not isinstance(o.get("via"), str):
            lacks.append(f"outcomes[{i}].via is not a string: {repr(o.get('via'))[:80]}")
    if ns != list(range(1, len(ns) + 1)):
        lacks.append(f"outcomes numbers {ns}, not 1..k")
    return lacks


def _shape_lacks(doc: dict, charter: Path) -> list[str]:
    """THE PLAN IS JSON, NOT PROSE (ticket e4f02a1ceef5): every lack of the plan shapes the store
    charter declares in ``plan_shapes``, and of the shaped fields it names in
    ``cast_requires_shaped``. Read at call time from ``charter`` — never a second copy here — so a
    charter with no ``plan_shapes`` yields []. Measured 2026-11-05: falsifier a dict on 248
    tickets and a string on 384 (39 of the newest 40), writes_to on 17 of 635, bounds on 3 — the
    structure was tried and decayed while this door checked only non-blank.

    A ``reads`` path resolves against the cairn root, then the commons root, then the commons'
    parent (paths are written as ``CairnCommons/...``)."""
    try:
        c = json.loads(Path(charter).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    shapes = c.get("plan_shapes") if isinstance(c, dict) else None
    if not isinstance(shapes, dict):
        return []
    lacks: list[str] = []
    for key in c.get("cast_requires_shaped") or []:
        # a key the required set already names (falsifier) is not named twice; measured's own
        # lack below says absent-or-empty in one line
        if key in shapes and _blank(doc.get(key)) and key != "measured" and key not in _CAST_REQUIRED:
            lacks.append(f"{key} is required")

    if "falsifier" in shapes and not _blank(doc.get("falsifier")):  # blank: (a) names it
        f = doc.get("falsifier")
        clauses = f.get("clauses") if isinstance(f, dict) else None
        if not isinstance(clauses, list) or not clauses:
            lacks.append("falsifier is not an object with clauses")
        else:
            ns = []
            for i, cl in enumerate(clauses):
                n = cl.get("n") if isinstance(cl, dict) else None
                claim = cl.get("claim") if isinstance(cl, dict) else None
                if not (isinstance(n, int) and not isinstance(n, bool)
                        and isinstance(claim, str) and claim.strip()):
                    lacks.append(f"falsifier.clauses[{i}] is not {{n, claim}}: {repr(cl)[:80]}")
                ns.append(n)
            if ns != list(range(1, len(ns) + 1)):
                lacks.append(f"falsifier.clauses numbers {ns}, not 1..k")

    spec = shapes.get("decisions")
    decisions = doc.get("decisions")
    if isinstance(spec, dict) and isinstance(decisions, list):
        here = Path(__file__).resolve().parents[3]
        commons = Path(charter).resolve().parent.parent
        roots = [here, commons, commons.parent]
        for i, d in enumerate(decisions):
            if not isinstance(d, dict):
                continue  # (d3) already names a line that is not a dict
            for k in spec.get("each_requires") or []:
                if k not in d:
                    lacks.append(f"decisions[{i}] lacks {k}")
                elif not _paths_ok(d[k]):
                    lacks.append(f"decisions[{i}].{k} is not a list of non-blank strings: {repr(d[k])[:80]}")
            if spec.get("reads_resolve") and _paths_ok(d.get("reads")):
                lacks.extend(f"decisions[{i}].reads {p!r} resolves to no file"
                             for p in d["reads"] if not _resolves(p, roots))

    # outcomes: the plan as Q#100 draws it (ticket 5c1e0a7d93b2, outline 9.3.5.1.2.1) — every
    # number below (the most outcomes, the keys it excludes) is the charter's, read here
    spec = shapes.get("outcomes")
    if isinstance(spec, dict) and "outcomes" in doc:
        lacks.extend(_outcome_lacks(doc, spec, Path(charter)))

    for key in ("constraints", "resources"):
        if isinstance(shapes.get(key), dict) and key in doc:
            cs = doc.get(key)
            if not (isinstance(cs, list) and all(isinstance(x, str) and x.strip() for x in cs)):
                lacks.append(f"{key} is not a list of non-blank strings: {repr(cs)[:80]}")

    spec = shapes.get("bounds")
    if isinstance(spec, dict) and not _blank(doc.get("bounds")):  # blank and required: named above
        b = doc.get("bounds")
        if not (isinstance(b, dict) and all(_paths_ok(b.get(k)) for k in spec.get("required") or [])):
            lacks.append(f"bounds is not {{{', '.join(spec.get('required') or [])}}} lists: {repr(b)[:80]}")
        else:
            # every writes_to lies in bounds.in (ticket 03b7e5d1a4c2). The containment runs one
            # way only: bounds.in may hold MORE than the writes_to union. Tester red tickets put
            # the red proof in bounds.in to dedup (cairn/devices/tester/red_tickets.py) while the
            # fix's writes are unknown at cast, so D1 writes [], and 6fc14bbead55 reads bounds.in
            # as a claim of its own. Measured 2026-11-16: 7 of 480 bounded tickets hold such a
            # path, all tester reds; 20 write outside bounds.in, the breach this refuses.
            inside = set(b.get("in") or [])
            for key in ("decisions", "outcomes"):
                for i, d in enumerate(doc.get(key) if isinstance(doc.get(key), list) else []):
                    w = d.get("writes_to") if isinstance(d, dict) else None
                    if _paths_ok(w):
                        lacks.extend(f"{key}[{i}].writes_to {p!r} is not in bounds.in"
                                     for p in w if p not in inside)

    spec = shapes.get("measured")
    if isinstance(spec, dict) and ("measured" in doc or "measured" in (c.get("cast_requires_shaped") or [])):
        m = doc.get("measured")
        if not isinstance(m, list) or len(m) < int(spec.get("min_items") or 1):
            lacks.append("measured is absent or empty")
        else:
            for i, e in enumerate(m):
                if not isinstance(e, dict):
                    lacks.append(f"measured[{i}] is not an object: {repr(e)[:80]}")
                    continue
                for k in spec.get("each_requires") or []:
                    if _blank(e.get(k)):
                        lacks.append(f"measured[{i}] lacks {k}")
                when = e.get("when")
                if not _blank(when) and not (isinstance(when, str) and _ISO_DATE.match(when[:10])):
                    lacks.append(f"measured[{i}].when {when!r} is not an ISO date")

    # fixes: the proofs whose red a fixit answers (ticket 5defc13bfebe, outline 17.11.7.2) — read
    # by the tester's rung 4 (path y) and codemother's BUILDME fixit rule, both resolving each
    # path against the cairn root, so that is the one root here. Not required at cast: the
    # BUILDME rule demands it of a bug at the crossing.
    spec = shapes.get("fixes")
    if isinstance(spec, dict) and "fixes" in doc:
        fx = doc.get("fixes")
        if not _paths_ok(fx) or len(fx) < int(spec.get("min_items") or 1):
            lacks.append(f"fixes is not a non-empty list of non-blank paths: {repr(fx)[:80]}")
        elif spec.get("resolves"):
            here = Path(__file__).resolve().parents[3]
            lacks.extend(f"fixes {p!r} resolves to no file" for p in fx
                         if not (Path(p) if Path(p).is_absolute() else here / p).is_file())

    # chart: each stage's draft, authored on the plan (ticket cd8a1de6139c, outline 9.6) — a
    # map of chart stage -> draft packet, so a gate reading it never meets a stage it has no door
    # for, nor a draft that is not a packet.
    spec = shapes.get("chart")
    if isinstance(spec, dict) and "chart" in doc:
        ch = doc.get("chart")
        if not isinstance(ch, dict):
            lacks.append(f"chart is not a map of stage -> draft: {repr(ch)[:80]}")
        else:
            keys = spec.get("keys") or []
            for stage, draft in ch.items():
                if stage not in keys:
                    lacks.append(f"chart.{stage} is not a chart stage ({', '.join(keys)})")
                elif not isinstance(draft, dict):
                    lacks.append(f"chart.{stage} is not a draft packet: {repr(draft)[:80]}")
    return lacks

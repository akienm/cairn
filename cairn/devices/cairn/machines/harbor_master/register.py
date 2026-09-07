"""harbor_master/register.py — the FLEET REGISTER: a compiled index over the boats' own records.

harbor_master owns the HARBOR through which workflows voyage. This is its first rung —
the TRUTH rung as an AGGREGATE: 'where you go to query open tickets', the fleet-scale
view of what is in port and what is still at sea. (The AUTHORITY rung — clearance for a
transition — is child b, and waits on the base-class emit-chokepoint; the VOYAGE view is
child c, deferred to meet the web_server. This file is child a alone.)

Two vantages, both already git-JSON on disk:
  - OPEN boats  = the tickets in ``CairnCommons/tickets/``, each wearing the ONE status
    label operator_inbox's ``read_tickets`` derives for it (ticket 3feb201c84ea,
    2026-09-06 — this file used to parse the cursor with a regex of its own, and the
    same ticket wore a different status here than in the inbox).
  - IN-PORT = the open tickets berthed at each COMPONENT, grouped by the ticket's
    ``owning_component``. A component's ``history.json`` is still walked, for two
    reasons only: the harbor sees every component that has a history even when no
    ticket is berthed there, and a history whose last standing is PROSE rather than a
    stage token surfaces as a ``finding`` — one line, never a status group.
    (Before 3feb201c84ea an in-port entry's standing was ``project(history).cursor``, and
    the map printed a component's last crossing as though it were a ticket's status —
    which is how the bus appeared twice with two statuses.)

The register is an INDEX, not a rival record (Law 7). Every entry's standing is read from
the boat's OWN record — through the one reader — and carries a ``source`` pointing back to
it; the register invents no truth a boat does not already hold. ``berth`` (open|in_port) is
not an invented field — it is a pure function of WHERE the boat lives.

Computed on read, never stored — so it cannot drift from the boats (Law 7), and child a's
filed "db-vs-git placement edge" DISSOLVES: there is nothing to place because there is no
second copy (Law 1 — the aggregate is compiled, not kept). If fleet queries ever turn hot,
an event-fired cache (the FileChanged pattern the intentions_model_compiler already uses)
is the grow-against-need step — never a poll.

The BaseDevice introspection FACE + bus-fronting (callers poke the harbor over the bus
rather than importing it) are a later runtime wrapper, deferred until a runtime pulls them —
exactly as inference_domain and db_domain deferred their faces. A filed edge, below.

Deliberately dependency-light: pure file reads + the projector's pure core. Runs bare.

    python3 -m cairn.devices.cairn.machines.harbor_master.register     # prints a human fleet summary
    python3 -m cairn.devices.cairn.machines.harbor_master.register <intention-address>   # deprecation report
"""

from __future__ import annotations

from pathlib import Path

from cairn.tools.base import address
from cairn.tools.charter import projector
from cairn.tools.operator_inbox.inbox import (
    is_stage_token,
    read_done_tickets,
    read_tickets,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]   # cairn/devices/cairn/machines/harbor_master/register.py -> repo root
_CAIRN = _REPO_ROOT / "cairn"
_SRC_ROOT = _REPO_ROOT.parent                        # ~/dev/src — the common parent of the two repos
_DEFAULT_TICKETS = _SRC_ROOT / "CairnCommons" / "tickets"


def _rel(path: Path) -> str:
    """A source pointer relative to the common src root when possible (portable, greppable)."""
    try:
        return str(path.relative_to(_SRC_ROOT))
    except ValueError:
        return str(path)


def _open_boats(tickets_dir: Path) -> list[dict]:
    """Open boats: every ticket in the commons tickets folder — the not-done ones first,
    in priority order, then the done-but-not-berthed (a PROVED ticket still in tickets/
    is migration debt the harbor keeps visible; the map's ``open`` filter drops it).

    Every field comes from operator_inbox's ``read_tickets`` — the ONE reader. ``standing``
    IS the record's ``label``, so the harbor map prints the same token the inbox does.
    """
    records = (read_tickets(tickets_dir=tickets_dir)["records"]
               + read_done_tickets(tickets_dir=tickets_dir)["records"])
    boats = []
    for r in records:
        boat = dict(r)
        boat["berth"] = "open"
        boat["standing"] = r["label"]
        boat["source"] = _rel(Path(r["source"]))
        boats.append(boat)
    return boats


def _component_key(d: Path, cairn_root: Path) -> str:
    """The component address the way a ticket's ``owning_component`` spells it:
    ``devices/cairn/machines/harbor_master``, ``bin``."""
    try:
        return str(d.relative_to(cairn_root))
    except ValueError:
        return d.name


def _berthed_boats(cairn_root: Path, open_boats: list[dict]) -> tuple[list[dict], list[dict]]:
    """In-port: the open boats berthed at each component, grouped by ``owning_component``.

    Returns ``(in_port, findings)``. Every component with a ``history.json`` beside its
    code (+ bin/) is an in-port entry even with no boats berthed (the harbor sees the
    whole port); every ``owning_component`` an open boat names is an entry even with no
    history yet (no ticket hides). A history whose last standing is prose rather than a
    stage token is a FINDING — ``{component, standing, source}`` — not a status.

    The ``boats`` list holds the SAME record dicts ``open`` holds, so a crossing patch on
    the open boat is visible from its berth too (one status, one object).
    """
    # The walk asks the component roster where the components ARE (address.component_dirs,
    # 2026-08-13) rather than spelling their depth. It used to be glob("*/history.json"),
    # and the rung reorganisation is exactly the event that shape cannot survive: after the
    # move it matched nothing and the harbor reported an EMPTY in-port lane. Caught by this
    # device's own proof ("the harbor does not see its own berthed history"), which is why
    # the tooth asserts non-empty rather than a count.
    dirs = [d for d in address.component_dirs(cairn_root)[0]
            if (d / "history.json").is_file()]
    bin_hist = cairn_root.parent / "bin" / "history.json"
    if bin_hist.exists():
        dirs.append(bin_hist.parent)

    by_component: dict[str, list[dict]] = {}
    for b in open_boats:
        by_component.setdefault(b.get("owning_component") or "unassigned", []).append(b)

    entries: dict[str, dict] = {}
    findings: list[dict] = []
    for d in sorted(dirs):
        key = _component_key(d, cairn_root)
        history = projector.read_history(str(d / "history.json"))
        cursor = projector.project(history)["cursor"] or {}
        standing = cursor.get("standing")
        source = _rel(d / "history.json")
        entries[key] = {
            "id": d.name,
            "berth": "in_port",
            "component": key,
            "standing": standing,
            "gate": cursor.get("gate"),
            "seq": cursor.get("seq"),
            "source": source,
            "boats": by_component.get(key, []),
        }
        if standing is not None and not is_stage_token(standing):
            findings.append({"component": key, "standing": standing, "source": source})
    for key, boats in by_component.items():
        if key not in entries:
            entries[key] = {
                "id": key.rsplit("/", 1)[-1],
                "berth": "in_port",
                "component": key,
                "standing": None,
                "gate": None,
                "seq": None,
                "source": boats[0]["source"],
                "boats": boats,
            }
    return [entries[k] for k in sorted(entries)], findings


def register(*, cairn_root: Path | str = _CAIRN, tickets_dir: Path | str = _DEFAULT_TICKETS) -> dict:
    """Compile the fleet register — a pure INDEX over the boats' own records.

    Returns ``{open, in_port, findings, fleet, counts}``. Not stored: recomputed from the
    boats each call, so it can never be a rival record that drifts (Law 7). ``fleet`` is
    the union of both vantages: the open tickets, and the components they are berthed at.
    """
    open_ = _open_boats(Path(tickets_dir))
    in_port, findings = _berthed_boats(Path(cairn_root), open_)
    return {
        "open": open_,
        "in_port": in_port,
        "findings": findings,
        "fleet": open_ + in_port,
        "counts": {"open": len(open_), "in_port": len(in_port), "fleet": len(open_) + len(in_port),
                   "findings": len(findings)},
    }


# ── query surface (the harbor's read face) ───────────────────────────────────


def open_boats(reg: dict) -> list[dict]:
    """The boats still at sea — 'query open tickets'."""
    return reg["open"]


def in_port(reg: dict) -> list[dict]:
    """The boats berthed — proven voyages beside their code."""
    return reg["in_port"]


def find(reg: dict, boat_id: str) -> list[dict]:
    """Every vantage of one boat by id — a LIST, because a boat mid-voyage shows in both
    (an open ticket + its berthed history). One entry: berthed or open only. Two: mid-voyage."""
    return [b for b in reg["fleet"] if b["id"] == boat_id]


def _retirement_report(intention: str) -> int:
    """THE DEPRECATION REPORT — print who rides one intention, and what the read could not see.

    Composes ``clearance.riders_of`` and prints it. There is deliberately NO arithmetic here:
    every integer below is one the library already returned, so the printed answer and the
    programmatic answer cannot drift (Law 7 — a presentation surface may arrange, it may not
    compute a second version of the truth).

    It lives here, in the register's ``__main__``, and not as a new verb under ``bin/cmd``:
    that folder carries sixteen verbs and none of them is a harbor verb, and minting the
    first one to hold a single read would be building a surface this device has never had.
    The register is already the established seat for a fleet-scale read.

        python3 -m cairn.devices.cairn.machines.harbor_master.register <intention-address>

    The consumer is the hand deciding whether to retire an intention — which is why the
    blind classes are printed at the same weight as the findings rather than as a footnote.
    A report that whispers its blindness is the one this whole build exists to forbid.
    """
    from cairn.devices.cairn.machines.harbor_master.clearance import riders_of

    r = riders_of(intention)
    blind = r.blind
    print(f"DEPRECATION REPORT — {intention}\n")
    print(f"RIDING IT ({len(r.riding)} in-flight boat(s) name this intention):")
    for b in r.riding:
        print(f"  {b}")
    if not r.riding:
        print("  (none)")
    print(f"\nWHAT THIS READ COULD NOT SEE — over {r.in_flight} in-flight boats, "
          f"{r.attributable} were attributable:")
    print(f"  unattributed  {blind['unattributed']:4}  in flight, naming no owning intention")
    print(f"  unresolvable  {blind['unresolvable']:4}  naming an intention that resolves nowhere")
    print(f"  unreadable    {blind['unreadable']:4}  whose flight status could not be judged")
    for boat, addr in r.unresolvable:
        print(f"      {boat}  ->  {addr}")
    for boat, why in r.unreadable:
        # TRUNCATED HERE AND NOWHERE ELSE. ``Riders`` carries the whole reason; a printout
        # is a presentation surface and may arrange (Law 7 permits the collapse HERE and
        # forbids it in the record) — one ticket's state field is a 900-character essay,
        # and letting it push the counts off the top of the screen would be a report that
        # hides its own findings.
        print(f"      {boat}  ::  {why[:120]}{'…' if len(why) > 120 else ''}")
    print("\nA clean 'nobody is riding this' means nothing while those three counts are "
          "non-zero.\nRetiring the intention is the owner's act; this read informs it and "
          "decides nothing (Law 6).")
    return 0


def _main(argv: list[str] | None = None) -> int:
    import sys

    args = sys.argv[1:] if argv is None else argv
    if args:
        return _retirement_report(args[0])
    reg = register()
    c = reg["counts"]
    print(f"HARBOR REGISTER — {c['fleet']} boats ({c['open']} open, {c['in_port']} in port)\n")
    print("OPEN (still at sea — CairnCommons/tickets/):")
    for b in reg["open"]:
        print(f"  {b['id']:32} @ {b['standing']}")
    print("\nIN PORT (open tickets berthed at each component):")
    for b in reg["in_port"]:
        if b["boats"]:
            print(f"  {b['component']:48} {len(b['boats'])} boat(s)")
    for f in reg["findings"]:
        print(f"  FINDING: {f['component']} history standing is prose: {f['standing'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

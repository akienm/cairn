"""The tester's tiers — the hourly, daily and weekly runs of outline 9.4.2.3.7 (Akien, 2026-11-13).

Commit, hourly, daily and weekly: each tier reseals a wider set than the one before, and every
run writes any new bugs — *"every test failure, every orphaned file, HAS TO BE FIXED ... reds
don't get lost"*. Each tier is one function here, fired by one verb of the tester's
(device.py declared_verbs), and each seals ONLY through ``reseal.reseal_all``, the one door that
writes a seal (9.4.2.3.3.1, one sealer), then hands its results to
``red_tickets.ticket_what_is_new`` so a new red becomes a ticket in the same act.

THE HOURLY TIER (ticket 810fb2fc4a15, outline 9.4.2.3.7.2): ``reseal_yellow``. A component that
passed its own proofs at commit is in service, YELLOW, until what depends on it is measured
again (ticket ee4e874a2d61). The yellow set is CodeMother's to compute — build_inspector lives
in her — so it is ASKED over the bus through her ``inspect`` verb and never imported (RULE 1;
outline 9.4.3.3.4; revised on open-ffae1cd5fc50). An absent or refusing CodeMother raises, and
nothing is resealed: a tier that cannot read its set measured nothing (Law 7).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
# A whole-repo inspect() sweeps every component; the ask waits for it rather than reading a
# slow answer as an absent CodeMother.
INSPECT_TIMEOUT_S = 900


class TierRefused(RuntimeError):
    """A tier could not read the set it reseals; nothing was resealed."""


def ask_codemother(judge: str, *args, bus=None, timeout: int = INSPECT_TIMEOUT_S, **kwargs):
    """``judge(*args, **kwargs)`` as CodeMother's ``inspect`` verb answers it, rebuilt.

    ``bus`` is any bus CodeMother is held on; the default reaches the house's. A refusal or a
    silence raises TierRefused naming the judge and the reason."""
    from cairn.devices.codemother.tools.inspect_wire.inspect_wire import wire_decode, wire_encode
    if bus is None:
        from cairn.tools.bus_client.bus_client import reach
        bus = reach("codemother")
    try:
        reply = bus.request(
            sender="tester", to="codemother", channel="personal", verb="inspect",
            why=f"the tester's tier asks {judge} (outline 9.4.2.3.7)",
            body={"judge": judge, "args": wire_encode(list(args)), "kwargs": wire_encode(kwargs)},
            timeout=timeout)
    except TimeoutError as exc:
        raise TierRefused(f"codemother did not answer inspect {judge!r}: {exc}") from exc
    body = (reply or {}).get("body") or {}
    if (reply or {}).get("sender") != "codemother" or not body.get("accepted"):
        raise TierRefused(f"codemother refused inspect {judge!r}: "
                          f"{body.get('reason') or body or reply}")
    return wire_decode(body["data"])


def yellow_proofs(yellow: list, repo_root: Path = REPO_ROOT) -> list[str]:
    """The proofs the hourly tier reseals, repo-relative, deduped and sorted.

    inspect() reports yellow in two shapes, and both are read:
      - ``component-waits-on-dependents`` (ee4e874a2d61): the changed component at ``at`` — every
        one of its own proofs — and each dependent proof named in ``waiting_on``;
      - ``a_reached_component_moved``: a dependent's seal whose reached digest moved — the proof
        ``proof`` in the component at ``at``.
    ``at`` is a component's directory under the ``cairn`` package, as inspect() names it."""
    repo_root = Path(repo_root)
    out: set[str] = set()
    for entry in yellow or []:
        if not isinstance(entry, dict):
            continue
        at = entry.get("at")
        comp = repo_root / "cairn" / at if at else None
        if entry.get("kind") == "component-waits-on-dependents":
            if comp is not None and (comp / "proofs").is_dir():
                out.update(p.relative_to(repo_root).as_posix()
                           for p in (comp / "proofs").glob("test_*.py"))
            out.update(str(p).replace("\\", "/") for p in entry.get("waiting_on") or [])
        elif entry.get("method") == "a_reached_component_moved" and comp is not None and entry.get("proof"):
            out.add((comp / "proofs" / entry["proof"]).relative_to(repo_root).as_posix())
    return sorted(out)


def reseal_yellow(*, bus=None, repo_root: Path | None = None, resealer=None, ticketer=None,
                  timeout: int = INSPECT_TIMEOUT_S) -> dict:
    """Reseal every yellow component's proofs and every proof waiting on one (ticket 810fb2fc4a15).

    Asks CodeMother's ``inspect`` for the yellow list, reseals the set through
    ``reseal.reseal_all`` (``resealer``), then tickets the new reds through
    ``red_tickets.ticket_what_is_new`` (``ticketer``) with the orphan scan off — the hourly tier
    is not a whole-tree run. The reply names each proof and its verdict; nothing yellow runs no
    proof and replies an empty set."""
    repo_root = Path(repo_root if repo_root is not None else REPO_ROOT)
    if resealer is None:
        from cairn.devices.tester.reseal import reseal_all as resealer
    if ticketer is None:
        from cairn.devices.tester.red_tickets import ticket_what_is_new as ticketer
    report = ask_codemother("inspect", bus=bus, timeout=timeout)
    yellow = report.get("yellow") if isinstance(report, dict) else None
    if not isinstance(yellow, list):
        raise TierRefused(f"codemother's inspect carried no yellow list: {str(report)[:300]}")
    proofs = yellow_proofs(yellow, repo_root)
    if not proofs:
        return {"tier": "hourly", "proofs": [], "verdicts": {}, "refusals": [], "ticketed": []}
    run = resealer([Path(repo_root) / p for p in proofs])
    results = run.get("results") or []
    ticketed = ticketer(results, scan_orphans=False)
    return {"tier": "hourly", "proofs": proofs,
            "verdicts": {str(r.get("proof")).replace("\\", "/"): r.get("outcome") for r in results},
            "refusals": run.get("refusals") or [],
            "ticketed": [str(p) for p in ticketed or []]}

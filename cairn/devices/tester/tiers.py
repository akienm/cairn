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


def tracked_proofs(repo_root: Path) -> list[str]:
    """Every proof git tracks under ``repo_root``, repo-relative and sorted: the daily set."""
    import subprocess
    done = subprocess.run(["git", "-C", str(repo_root), "ls-files", "*/proofs/test_*.py"],
                          capture_output=True, text=True, check=True)
    return sorted(line.strip() for line in done.stdout.splitlines() if line.strip())


def run_every_proof(*, repo_root: Path | None = None, resealer=None, ticketer=None) -> dict:
    """Reseal every proof git tracks, then ticket each new red and orphan (ticket cd40ac53f08a).

    THE DAILY TIER (outline 9.4.2.3.7.3): run in sleep, it is the whole-tree run, so it hands
    its results to ``red_tickets.ticket_what_is_new`` (``ticketer``) with the orphan scan ON.
    Every proof goes through ``reseal.reseal_all`` (``resealer``), the one door that writes a
    seal. A proof whose every tooth printed NOTRUN (ticket eb27604ab267) seals nothing; the
    reply names it under ``not_run`` so the Linux sealer's turn is asked for, never lost."""
    repo_root = Path(repo_root if repo_root is not None else REPO_ROOT)
    if resealer is None:
        from cairn.devices.tester.reseal import reseal_all as resealer
    if ticketer is None:
        from cairn.devices.tester.red_tickets import ticket_what_is_new as ticketer
    proofs = tracked_proofs(repo_root)
    run = resealer([repo_root / p for p in proofs]) if proofs else {"results": [], "refusals": []}
    results = run.get("results") or []
    ticketed = ticketer(results, scan_orphans=True, repo_root=repo_root)
    verdicts = {str(r.get("proof")).replace("\\", "/"): r.get("outcome") for r in results}
    return {"tier": "daily", "proofs": proofs, "verdicts": verdicts,
            "not_run": sorted(p for p, v in verdicts.items() if v == "not-run"),
            "refusals": run.get("refusals") or [],
            "ticketed": [str(p) for p in ticketed or []]}


def rehollow(proofs: list[str], *, repo_root: Path, measurer=None) -> tuple[list[dict], list[dict]]:
    """Part 1 of the weekly tier: every proof whose standing seal carries a hollow reading re-runs
    it through ``hollow.measure`` (``measurer``), scoped to that proof.

    A hollow whose verdict is now ``red`` means the build's reversion no longer reds the proof:
    the proof passes a hollow build, so the PROOF is red (Law 8) and is handed on as one. A
    ``green`` hollow still fails the hollow build: reported green, nothing cast. A hollow that
    cannot be measured is a refusal, never a green (Law 3). Returns (results, refusals)."""
    from cairn.devices.tester.reseal import hollow_tickets
    if measurer is None:
        from cairn.devices.tester.hollow import measure as measurer
    results, refusals = [], []
    for rel in proofs:
        for tid in sorted(hollow_tickets(Path(repo_root) / rel)):
            try:
                finding = measurer(tid, repo_root=Path(repo_root), proofs=[rel])
            except Exception as exc:   # HollowUnmeasurable and its kin: said, never green
                refusals.append({"proof": rel, "hollow": tid, "refusal": f"{type(exc).__name__}: {exc}"})
                continue
            passes = finding.get("verdict") == "red"
            results.append({"proof": rel, "hollow": tid, "outcome": "red" if passes else "green",
                            "why": ("the hollow build now passes this proof: "
                                    f"{'; '.join(finding.get('reasons') or [])}") if passes
                            else "the hollow build still fails this proof"})
    return results, refusals


def weekly_run(*, repo_root: Path | None = None, measurer=None, resealer=None, ticketer=None) -> dict:
    """The weekly tier (ticket 346c75c2f8b7, outline 9.4.2.3.7.4): hollow re-runs, then this box's
    own run of every proof it tracks.

    Part 1 (``rehollow``) reads each proof's sealed hollow BEFORE part 2 reseals it, since a seal
    over moved code drops the reading. Part 2 is run-every-proof's set on this box, sealed only
    through ``reseal.reseal_all`` (``resealer``; 9.4.2.3.3.1, one sealer), so each box's weekly
    run is its own. Both parts' results go to ``red_tickets.ticket_what_is_new`` (``ticketer``)
    in one call with the orphan scan on; red_tickets keys a red by its proof, so a proof red in
    both parts is ticketed once."""
    repo_root = Path(repo_root if repo_root is not None else REPO_ROOT)
    if resealer is None:
        from cairn.devices.tester.reseal import reseal_all as resealer
    if ticketer is None:
        from cairn.devices.tester.red_tickets import ticket_what_is_new as ticketer
    proofs = tracked_proofs(repo_root)
    hollows, hollow_refusals = rehollow(proofs, repo_root=repo_root, measurer=measurer)
    run = resealer([repo_root / p for p in proofs]) if proofs else {"results": [], "refusals": []}
    results = run.get("results") or []
    ticketed = ticketer(hollows + results, scan_orphans=True, repo_root=repo_root)
    verdicts = {str(r.get("proof")).replace("\\", "/"): r.get("outcome") for r in results}
    return {"tier": "weekly", "proofs": proofs,
            "hollow": {f"{h['proof']}::{h['hollow']}": h["outcome"] for h in hollows},
            "verdicts": verdicts,
            "not_run": sorted(p for p, v in verdicts.items() if v == "not-run"),
            "refusals": hollow_refusals + (run.get("refusals") or []),
            "ticketed": [str(p) for p in ticketed or []]}

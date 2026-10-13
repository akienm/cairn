#!/usr/bin/env python3
"""Proof of the claim_propagates_with_provenance sieve (d48d54dccde6, D-a..D-d).

A definitional claim (a normalized sentence of 8+ words in role/what/why) recurring across
two or more artifacts in EITHER root reds unless some carrier marks that field 'akien' or
'cc-read'. Each tooth builds its own two scratch roots, so no live corpus is read.

ITS OWN FILE, AND THE SUBJECT BOUND AT CALL TIME. Measured 2026-10-13: these teeth lived at
line ~1072 of test_inspector.py, one monolithic main() whose first failure ends the run.
The hollow reading reverts inspector.py to 9c53bf06ed5a (parent of the pre-hex build commit
cfdc7ced), and that inspector imports cairn.devices.builder, which no longer exists — so
the proof crashed at import, printed no tooth, and PROVED refused hollow_unreadable twice.
Here each tooth imports the inspector itself and the runner prints FAIL per tooth and goes
on, so a reverted world reads red tooth by tooth instead of UNREAD.

    bin/cairn test cairn/machines/build_inspector/proofs/test_claim_propagates_with_provenance.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"d48d54dccde6": {
    "1": "test_a_bare_recurring_claim_reds",
    "2": "test_a_marked_carrier_keeps_it_quiet",
    "3": "test_the_sieve_is_a_runnable_check",
    "4": "test_a_claim_across_both_roots_reds",
}}

_CLAIM = ("The ledger is the one record every delivery is counted from, "
          "and nothing else counts them.")
_ROW = {"component": "build_inspector", "dir": "build_inspector", "charter_on_disk": True}
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _insp():
    """The inspector, bound at call time: a reverted subject reds the tooth, not the reader."""
    from cairn.machines.build_inspector import inspector
    return inspector


def _world(prefix: str, *, a_mark: str | None = None, b_in_commons: bool = False):
    world = scratch_dir(prefix)
    repo, commons = world / "repo", world / "CairnCommons"
    (repo / ".git").mkdir(parents=True)
    (commons / "intentions-not-beside-code").mkdir(parents=True)
    a = {"component": "a", "what": _CLAIM, "claim_provenance": {}}
    if a_mark:
        a["claim_provenance"] = {"what": a_mark}
    (repo / "a").mkdir()
    (repo / "a" / "intention+why.json").write_text(json.dumps(a))
    b = {"component": "b", "why": "Said again. " + _CLAIM}
    if b_in_commons:
        (commons / "intentions-not-beside-code" / "I-b.json").write_text(json.dumps(b))
    else:
        (repo / "b").mkdir()
        (repo / "b" / "intention+why.json").write_text(json.dumps(b))
    # the derived lab copy must never count as a second carrier
    lab = commons / "intentions-congruency-lab"
    lab.mkdir()
    (lab / "a.json").write_text(json.dumps(a))
    return repo, commons


def _run(repo: Path, commons: Path) -> list:
    return _insp().claim_propagates_with_provenance(_ROW, repo / "a", repo=repo, commons=commons)


def test_a_bare_recurring_claim_reds() -> None:
    f = _run(*_world("inspector-proof-cp-bare-"))
    ok = [x["method"] for x in f] == ["claim_propagates_with_provenance"] \
        and len(f[0]["values"]["carriers"]) == 2
    check("test_a_bare_recurring_claim_reds", ok, "" if ok else str(f))


def test_a_marked_carrier_keeps_it_quiet() -> None:
    quiet = {mark: _run(*_world("inspector-proof-cp-marked-", a_mark=mark)) for mark in ("akien", "cc-read")}
    bad = _run(*_world("inspector-proof-cp-badmark-", a_mark="someone"))
    ok = all(v == [] for v in quiet.values()) and len(bad) == 1
    check("test_a_marked_carrier_keeps_it_quiet", ok,
          "" if ok else f"marked={quiet} badmark={bad} (a mark outside akien|cc-read is no provenance)")


def test_a_claim_across_both_roots_reds() -> None:
    repo, commons = _world("inspector-proof-cp-roots-", b_in_commons=True)
    f = _run(repo, commons)
    roots = ({Path(p).resolve().is_relative_to(commons.resolve()) for p in f[0]["values"]["carriers"]}
             if len(f) == 1 else set())
    check("test_a_claim_across_both_roots_reds", len(f) == 1 and roots == {True, False}, str(f))


def test_the_sieve_is_a_runnable_check() -> None:
    insp = _insp()
    registered = insp.SIEVES.get("claim_propagates_with_provenance") is insp.claim_propagates_with_provenance
    saved = insp._claim_carried
    insp._claim_carried = lambda marks: True
    try:
        silenced = _run(*_world("inspector-proof-cp-mutant-")) == []
    finally:
        insp._claim_carried = saved
    check("test_the_sieve_is_a_runnable_check", registered and silenced,
          f"registered={registered} accept-all mutant silenced the red={silenced}")


def main() -> int:
    for tooth in (test_a_bare_recurring_claim_reds, test_a_marked_carrier_keeps_it_quiet,
                  test_a_claim_across_both_roots_reds, test_the_sieve_is_a_runnable_check):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

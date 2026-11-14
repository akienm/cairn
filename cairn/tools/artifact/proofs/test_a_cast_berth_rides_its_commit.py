"""Proof for ticket 1fd53bb32084: a commit that stages a ticket also stages the berths it cites.

``transitions._carry_berths`` copies each berth a cast cites into ``<commons>/berths/<kind>/``
so every box's gates can read it, and the copy landed untracked: c7dc2ccdd9ad was refused at
another box because its sorted berth sat on disk at the casting box and in no commit. Two
clauses:

(1) the pre-commit check (``artifact.check_staged``) refuses a staged ticket state whose sorted
    or intent berth is neither tracked nor staged under ``berths/``, naming the berth and the
    ``git add`` that fixes it; the same commit with the berths staged passes. The boundary rides
    the same tooth: a citation UNCHANGED since HEAD is not judged (626 standing tickets cite
    berths cast before the carry existed, measured 2026-11-13), and a ``none, because`` entry is
    not a path. The citation is written Windows-shaped, so a berth cast on either kind of box
    resolves to the one commons address.
(2) the jurisdiction declares ``berths/sorted`` and ``berths/intent``, so the door journals what
    ``_carry_berths`` writes — and a berth written CRLF on Windows lands in the canonical LF form
    the door takes, instead of being refused.

Hermetic: a scratch git repo stands in for the commons (``set_diagnostic_roots``); the check
is called in process, the same predicate the hook runs.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_a_cast_berth_rides_its_commit.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"1fd53bb32084": {
    "1": "test_an_uncarried_berth_is_refused_by_name_and_passes_once_staged",
    "2": "test_the_door_journals_what_carry_berths_writes",
}}

FAILURES: list[str] = []
SORTED = "sorted-20261113T120000-1fd53bb32084.json"
INTENT = "intent-20261113T115900-1fd53bb32084.json"


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"\n        {detail[:600]}" if detail else ""))
    if not ok:
        FAILURES.append(name)
    return ok


def _git(root: Path, *args: str) -> str:
    from cairn.tools.scratch.scratch import git_env
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=git_env())
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def _world(tmp: Path) -> tuple[Path, Path]:
    """A scratch commons with a ticket charter and one STANDING ticket, committed, whose berths
    were never carried; and a scratch box whose instance-space holds this cast's two berths,
    written CRLF the way a Windows box writes them."""
    from cairn.tools.artifact import artifact as door
    commons, box = tmp / "CairnCommons", tmp / "box"
    (commons / "tickets").mkdir(parents=True)
    door.set_diagnostic_roots({"CairnCommons": commons, "parked": tmp / "parked"})
    _git(commons, "init", "-q")
    for k, v in (("user.email", "proof@cairn"), ("user.name", "proof"),
                 ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        _git(commons, "config", k, v)
    door.write_json(commons / "tickets" / "_charter+why.json",
                    {"state_fields": ["state", "sorted_berth", "intent_berth"]},
                    verb="charter", why="proof fixture")
    door.write_json(commons / "tickets" / "aaaaaaaaaaaa-standing.state.json",
                    {"state": "BUILDME", "sorted_berth": "/far/box/berths/sorted/sorted-old.json",
                     "intent_berth": "/far/box/berths/intent/intent-old.json"},
                    verb="cast", why="proof fixture: a ticket cast before the carry existed")
    _git(commons, "add", "-A")
    _git(commons, "commit", "-q", "--no-verify", "-m", "fixture")
    for kind, name in (("sorted", SORTED), ("intent", INTENT)):
        src = box / "berths" / kind / name
        src.parent.mkdir(parents=True)
        src.write_bytes(json.dumps({"kind": kind, "ticket": "1fd53bb32084"}, indent=2)
                        .replace("\n", "\r\n").encode("utf-8") + b"\r\n")
    return commons, box


def _cast(commons: Path, box: Path) -> list[Path]:
    from cairn.tools.base.transitions import _carry_berths
    return _carry_berths({"sorted_berth": str(box / "berths" / "sorted" / SORTED),
                          "intent_berth": str(box / "berths" / "intent" / INTENT)},
                         "proof fixture: the cast carries its berths")


def test_the_door_journals_what_carry_berths_writes(commons: Path, box: Path) -> None:
    from cairn.tools.artifact import artifact as door
    try:
        carried = _cast(commons, box)
    except Exception as exc:  # noqa: BLE001 — a refused carry is this clause's red
        check(PROVES["1fd53bb32084"]["2"], False, f"the carry raised {type(exc).__name__}: {exc}")
        return
    entries = door.read_journal(commons)
    bad = []
    for kind, name in (("sorted", SORTED), ("intent", INTENT)):
        rel = f"berths/{kind}/{name}"
        dst = commons / rel
        if dst not in carried or not dst.is_file():
            bad.append(f"{rel} not carried")
            continue
        body = dst.read_bytes()
        if b"\r" in body:
            bad.append(f"{rel} landed CRLF, not the canonical LF form")
        if door.locate(dst) is None:
            bad.append(f"{rel} is outside the door's jurisdiction")
        last = next((e for e in reversed(entries) if e.get("path") == rel), None)
        if last is None:
            bad.append(f"{rel} carried but never journaled")
        elif last.get("verb") != "cast" or last.get("sha_after") != hashlib.sha256(body).hexdigest():
            bad.append(f"{rel} journaled as {last.get('verb')!r} with sha_after "
                       f"{str(last.get('sha_after'))[:12]}, not the bytes on disk")
    check(PROVES["1fd53bb32084"]["2"], not bad, "; ".join(bad))


def test_an_uncarried_berth_is_refused_by_name_and_passes_once_staged(commons: Path, box: Path) -> None:
    from cairn.tools.artifact import artifact as door
    bad = []
    # The boundary first: a standing ticket's state moves, its berth citation does not.
    door.write_json(commons / "tickets" / "aaaaaaaaaaaa-standing.state.json",
                    {"state": "PROVEME", "sorted_berth": "/far/box/berths/sorted/sorted-old.json",
                     "intent_berth": "/far/box/berths/intent/intent-old.json"},
                    verb="phase", why="proof fixture: a crossing on a ticket cast before the carry")
    _git(commons, "add", "--", "tickets/aaaaaaaaaaaa-standing.state.json")
    standing = door.check_staged("CairnCommons")
    if standing:
        bad.append(f"a citation unchanged since HEAD was judged: {standing}")
    _git(commons, "commit", "-q", "--no-verify", "-m", "the standing ticket crosses")
    # The cast: berths carried on disk (or not, under a hollow), the state staged without them.
    if not (commons / "berths" / "sorted" / SORTED).is_file():
        try:
            _cast(commons, box)
        except Exception:  # noqa: BLE001 — clause 2's red; this clause still judges the refusal
            for kind, name in (("sorted", SORTED), ("intent", INTENT)):
                dst = commons / "berths" / kind / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(json.dumps({"kind": kind}, indent=2) + "\n", encoding="utf-8")
    state = commons / "tickets" / "1fd53bb32084-the-cast.state.json"
    door.write_json(state, {"state": "BUILDME",
                            "sorted_berth": f"C:\\Users\\box\\.cairn\\devices\\skill_block\\0\\berths\\sorted\\{SORTED}",
                            "intent_berth": f"C:\\Users\\box\\.cairn\\devices\\skill_block\\0\\berths\\intent\\{INTENT}"},
                    verb="cast", why="proof fixture: a cast citing Windows-shaped berths")
    _git(commons, "add", "--", state.relative_to(commons).as_posix())
    refused = door.check_staged("CairnCommons")
    for kind, name in (("sorted", SORTED), ("intent", INTENT)):
        rel = f"berths/{kind}/{name}"
        if not any(rel in f and f"git add {rel}" in f for f in refused):
            bad.append(f"no refusal names {rel} and its git add: {refused}")
    # The exemption: an intent berth of 'none, because' is not a path.
    door.write_json(state, {"state": "BUILDME",
                            "sorted_berth": f"C:\\Users\\box\\.cairn\\devices\\skill_block\\0\\berths\\sorted\\{SORTED}",
                            "intent_berth": "none, because the intention is CLAUDE.md's own charter"},
                    verb="cast", why="proof fixture: the intent berth exempt")
    _git(commons, "add", "--", state.relative_to(commons).as_posix())
    exempt = door.check_staged("CairnCommons")
    if any("intent" in f for f in exempt) or not any(f"berths/sorted/{SORTED}" in f for f in exempt):
        bad.append(f"the 'none, because' intent berth was judged, or the sorted one was not: {exempt}")
    # The same commit with the berth staged passes.
    _git(commons, "add", "--", f"berths/sorted/{SORTED}")
    passed = door.check_staged("CairnCommons")
    if passed:
        bad.append(f"with the berth staged the commit is still refused: {passed}")
    check(PROVES["1fd53bb32084"]["1"], not bad, "; ".join(bad))


def main() -> int:
    from cairn.tools.scratch.scratch import git_env, scratch_dir
    # check_staged runs in process and its git calls inherit this env: a hook's GIT_INDEX_FILE
    # would point them at the caller's index, not the scratch commons.
    for k in set(os.environ) - set(git_env()):
        os.environ.pop(k)
    from cairn.tools.artifact import artifact as door
    try:
        commons, box = _world(scratch_dir("cairn-1fd5-"))
        test_the_door_journals_what_carry_berths_writes(commons, box)
        test_an_uncarried_berth_is_refused_by_name_and_passes_once_staged(commons, box)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["1fd53bb32084"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    finally:
        door.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

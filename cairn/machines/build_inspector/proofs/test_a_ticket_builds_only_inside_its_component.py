"""Proof (ticket 8d14f4aa9e72) — a ticket whose decisions write outside its owning component is
refused at BUILDME: RULE 1 as physics for the write side.

MEASURED 2026-11-14 (akiendell_cc_0): d3248 and 2517, owned by cairn/tools/base, edited
cairn/machines/build_inspector/inspector.py and nothing caught it. ``encapsulation_holds``
(outline 17.13.1) is a path check over IMPORTS only. Over CairnCommons/tickets against origin/main
2889bdd1f, 89 of 391 tickets with an owner and writes cross a component line, and 38 of the 177
open ones do.

THE REGION RULE (D1). A path's component is the deepest ancestor directory holding an
``intention+why.json``, lifted to its enclosing device when that charter sits under
``cairn/devices/<d>/tools`` or ``/machines``; a component's ``proofs/`` and ``validations/`` are the
component's own. A path with no charter ancestor is ``unowned`` (D3). The charter list is read
from ``git ls-files`` of the class root the ticket lookup uses (``tickets_root``, else the
inspector's ``_TICKETS_ROOT``), never from a component's code (RULE 1).

Every tooth runs over a SCRATCH world: ``<w>/cairn``, a git tree whose only tracked files are
the charters the tooth names, and ``<w>/CairnCommons/tickets`` holding one ticket. The judge is
handed ``tickets_root=<w>/cairn`` and reads nothing else.

  (1) owned by cairn/tools/base, writing cairn/machines/build_inspector/inspector.py (the
      d3248/2517 shape): ONE finding, kind ``foreign``, naming that region and that path;
  (2) writes to its own code, proofs/ and validations/, and a device's own tools and machines,
      in either direction: no finding;
  (3) a write under no charter: one ``unowned`` finding naming every such path; an
      owning_intention that does not resolve to a charter is refused LOUDLY (one finding, kind
      ``unresolved_owner``), never skipped.

  (4) over the REAL corpus the judge's SET of crossing tickets equals the census's set
      (akiendell_cc_0, CairnCommons 83d84e0bd: 87 of 393 over commons 390ca863b and cairn
      86603d049), over every ticket on file at the census whose file has not changed since — a
      set, never a count, so two errors cannot cancel. A ticket cast or edited since is out of
      the comparison by construction.

ONE NAMED HOLE, red on purpose (tooth 3c, under clause 3's "refused loudly, never skipped"):
  - SPANNING OWNERSHIP. An owning_intention under CairnCommons/intentions-not-beside-code (a
    spanning intention, CLAUDE.md) waits on Q#103 (open-212b2de5c6b8, outline 17.13.1.1): one ticket
    under a spanning intention, or one per component. Its answer decides what the judge says.

    python cairn/machines/build_inspector/proofs/test_a_ticket_builds_only_inside_its_component.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "8d14f4aa9e72": {
        "1": "test_1_a_base_ticket_writing_the_inspector_is_one_foreign_finding",
        "1b": "test_1b_no_root_given_reads_the_bent_class_root_not_the_live_one",
        "2": "test_2_own_code_proofs_validations_and_a_devices_own_parts_are_green",
        "2b": "test_2b_a_device_machine_owner_writing_its_device_is_green",
        "3": "test_3_a_write_under_no_charter_is_one_unowned_finding",
        "3c": "test_3c_a_spanning_owner_is_the_named_hole_and_reds_loudly",
        "4": "test_4_over_the_real_corpus_the_crossing_set_is_the_census",
        "3b": "test_3b_an_owner_that_does_not_resolve_is_refused_loudly",
        "5": "test_5_a_charter_committed_in_a_worktree_moves_the_charter_list",
    },
}

TID = "b0c1d2e3f4a5"
CHARTERS = (
    "cairn/tools/base/intention+why.json",
    "cairn/machines/build_inspector/intention+why.json",
    "cairn/devices/tester/intention+why.json",
    "cairn/devices/tester/machines/swap/intention+why.json",
    "cairn/devices/tester/tools/seal/intention+why.json",
)
METHOD = "buildme_stays_in_its_component"


class _World:
    """A scratch commons with one ticket, and a scratch git tree whose tracked files are the
    charters. Closed in a finally, so a red tooth leaves nothing behind."""

    def __init__(self, owner: str | None, writes: list[str], bounds_in: list[str] | None = None):
        self.dir = scratch_dir("component-bound-proof-")
        self.commons = self.dir / "CairnCommons"
        self.tree = self.dir / "cairn"
        (self.commons / "tickets").mkdir(parents=True)
        self.tree.mkdir()
        env = git_env()
        subprocess.run(["git", "init", "-q", str(self.tree)], check=True, env=env)
        for c in CHARTERS:
            p = self.tree / c
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}\n")
        subprocess.run(["git", "-C", str(self.tree), "add", "--", *CHARTERS], check=True, env=env)
        ticket = {"ticket": TID, "decisions": [{"n": 1, "text": "D1", "writes_to": writes}],
                  "bounds": {"in": bounds_in if bounds_in is not None else list(writes), "out": []}}
        if owner is not None:
            ticket["owning_intention"] = owner
        (self.commons / "tickets" / f"{TID}-x.json").write_text(json.dumps(ticket, indent=2) + "\n")

    def judge(self) -> list[dict]:
        # ONE root, the class root, as the sibling judges take it (buildme_rides_the_sorted):
        # the ticket resolves through ticket_path from it and the charters are its git ls-files,
        # so a bent tickets_root can never pair a scratch ticket with the live tree's charters.
        import cairn.machines.build_inspector.inspector as I
        judge = getattr(I, METHOD, None)
        assert judge is not None, f"build_inspector publishes no {METHOD}"
        return judge(TID, tickets_root=self.tree)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def _v(f: dict) -> dict:
    return f.get("values", {})


def _run(owner, writes, bounds_in=None) -> list[dict]:
    w = _World(owner, writes, bounds_in)
    try:
        return w.judge()
    finally:
        w.close()


def test_1_a_base_ticket_writing_the_inspector_is_one_foreign_finding():
    got = _run("cairn/tools/base/intention+why.json",
               ["cairn/tools/base/transitions.py", "cairn/machines/build_inspector/inspector.py"])
    assert len(got) == 1, f"expected ONE finding for one foreign region, got {len(got)}: {got}"
    v = _v(got[0])
    assert v.get("kind") == "foreign", f"the finding's kind is not 'foreign': {got[0]}"
    assert v.get("region") == "cairn/machines/build_inspector", f"wrong region: {got[0]}"
    assert v.get("paths") == ["cairn/machines/build_inspector/inspector.py"], f"wrong paths: {got[0]}"
    # The lane prints ``about`` alone (transitions._sieve_lane), so the reading rides it too.
    about = got[0].get("about", "")
    assert "cairn/machines/build_inspector" in about and "inspector.py" in about, (
        f"the about line does not name the region and the path: {about!r}")


def test_1b_no_root_given_reads_the_bent_class_root_not_the_live_one():
    # Over the wire the lane passes the ticket alone. The judge must then read the inspector's
    # launch root (``_TICKETS_ROOT``, bent by CAIRN_BUILD_INSPECTOR_TICKETS_ROOT), for the ticket
    # AND the charters: a live read would find the scratch ticket "not on file" and return [],
    # a hollow green.
    import cairn.machines.build_inspector.inspector as I
    judge = getattr(I, METHOD, None)
    assert judge is not None, f"build_inspector publishes no {METHOD}"
    w = _World("cairn/tools/base/intention+why.json", ["cairn/machines/build_inspector/inspector.py"])
    was = I._TICKETS_ROOT
    I._TICKETS_ROOT = w.tree
    try:
        got = judge(TID)
    finally:
        I._TICKETS_ROOT = was
        w.close()
    assert [(_v(f).get("kind"), _v(f).get("region")) for f in got] ==         [("foreign", "cairn/machines/build_inspector")], f"root=None did not read the bent root: {got}"


def test_2_own_code_proofs_validations_and_a_devices_own_parts_are_green():
    got = _run("cairn/tools/base/intention+why.json",
               ["cairn/tools/base/transitions.py",
                "cairn/tools/base/proofs/test_x.py",
                "cairn/tools/base/validations/test_x.json"])
    assert got == [], f"a ticket writing only its own component was refused: {got}"
    got = _run("cairn/devices/tester/intention+why.json",
               ["cairn/devices/tester/isolation.py",
                "cairn/devices/tester/machines/swap/swap.py",
                "cairn/devices/tester/tools/seal/seal.py",
                "cairn/devices/tester/proofs/test_x.py"])
    assert got == [], f"a device ticket writing its own machines and tools was refused: {got}"


def test_2b_a_device_machine_owner_writing_its_device_is_green():
    # The lift runs on the OWNER side too: a machine inside a device has the device's one owner.
    got = _run("cairn/devices/tester/machines/swap/intention+why.json",
               ["cairn/devices/tester/isolation.py", "cairn/devices/tester/machines/swap/swap.py"])
    assert got == [], f"a device machine's ticket writing its own device was refused: {got}"


def test_3_a_write_under_no_charter_is_one_unowned_finding():
    got = _run("cairn/tools/base/intention+why.json",
               ["cairn/tools/base/transitions.py", "press_office/notes.txt", ".gitattributes"])
    assert len(got) == 1, f"expected ONE unowned finding, got {len(got)}: {got}"
    v = _v(got[0])
    assert v.get("kind") == "unowned", f"the finding's kind is not 'unowned': {got[0]}"
    assert sorted(v.get("paths") or []) == [".gitattributes", "press_office/notes.txt"], got[0]
    # bounds.in counts as a write too: a path named only there is judged.
    got = _run("cairn/tools/base/intention+why.json", ["cairn/tools/base/transitions.py"],
               bounds_in=["cairn/tools/base/transitions.py", "cairn/machines/build_inspector/inspector.py"])
    assert [(_v(f).get("kind"), _v(f).get("region")) for f in got] == \
        [("foreign", "cairn/machines/build_inspector")], f"a bounds.in path was not judged: {got}"


def test_3b_an_owner_that_does_not_resolve_is_refused_loudly():
    for owner in ("cairn/tools/nope/intention+why.json", None, ""):
        got = _run(owner, ["cairn/tools/base/transitions.py"])
        assert len(got) == 1 and _v(got[0]).get("kind") == "unresolved_owner", (
            f"owning_intention {owner!r} was not refused loudly: {got}")


def test_3c_a_spanning_owner_is_the_named_hole_and_reds_loudly():
    # Akien's open question decides what a spanning owner MAY do; until then the judge says so.
    got = _run("CairnCommons/intentions-not-beside-code/I-some-migration.md",
               ["cairn/tools/base/transitions.py"])
    assert len(got) == 1 and _v(got[0]).get("kind") == "spanning_owner_open", (
        f"a spanning owner did not red as the named hole: {got}")
    assert "question" in got[0].get("about", ""), f"the hole does not name the open question: {got}"


CENSUS_AT = "83d84e0bd"
CENSUS = "cast-inputs/a-ticket-whose-writes-leave-its-owning-component-is-refused-at-buildme.census-2026-11-14.json"
CENSUS_COMMONS = "390ca863b"
_HEX_STEM = re.compile(r"^([0-9a-f]{12})-")


def _git(commons: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(commons), *args], capture_output=True, text=True,
                          check=True, env=git_env()).stdout


def test_4_over_the_real_corpus_the_crossing_set_is_the_census():
    import cairn.machines.build_inspector.inspector as I
    judge = getattr(I, METHOD, None)
    assert judge is not None, f"build_inspector publishes no {METHOD}"
    commons = REPO.parent / "CairnCommons"
    census = json.loads(_git(commons, "show", f"{CENSUS_AT}:{CENSUS}"))
    then = {Path(n).stem for n in _git(commons, "ls-tree", "--name-only", CENSUS_COMMONS, "tickets/").split()
            if n.endswith(".json")}
    moved = {Path(n).stem for n in _git(commons, "diff", "--name-only", CENSUS_COMMONS, "HEAD", "--", "tickets").split()}
    moved |= {Path(n).stem for n in _git(commons, "diff", "--name-only", "--", "tickets").split()}
    # Keyed by TICKET ID, never by file stem: a ticket carries companions (``<stem>.state.json``)
    # that share its id, and one unchanged companion must not vouch for an edited ticket.
    def tid(stem: str) -> str:
        m = _HEX_STEM.match(stem)
        return m.group(1) if m else stem.removesuffix(".state")
    moved_ids = {tid(stem) for stem in moved}
    stable = {tid(stem): stem for stem in then if not stem.endswith(".state")}
    stable = {i: stem for i, stem in stable.items() if i not in moved_ids}
    assert len(stable) > 300, f"only {len(stable)} stable tickets: the comparison measures too little"
    # The census files an unowned path as a "<none:X>" key beside the real regions; the judge
    # carries those in its one unowned finding, so the region compare is over real regions. ONE
    # rule difference, measured 2026-11-14 on f942a413f26d: the census walks STRICT ancestors, so
    # a write naming a component's own directory (``bin``) read "<none:bin>"; the judge includes
    # the path itself, so a write of a component's directory is that component. The census key is
    # read by the judge's rule, never dropped: X with a charter is region X.
    charters = I._charter_dirs(REPO)
    def region(g: str) -> str | None:
        if not g.startswith("<none:"):
            return g
        x = g[len("<none:"):-1]
        return I._component_of(x, charters)
    want = {}
    for r in census["rows"]:
        if r["id"] in stable:
            want[r["id"]] = {g for k in r["foreign_regions"] if (g := region(k)) and g != r["owner"]}
    got: dict[str, set] = {}
    for tid in sorted(stable):
        found = judge(tid, tickets_root=REPO)
        kinds = {_v(f).get("kind") for f in found}
        if kinds & {"foreign", "unowned"}:
            got[tid] = {_v(f).get("region") for f in found if _v(f).get("kind") == "foreign"}
    only_judge = sorted(set(got) - set(want))
    only_census = sorted(set(want) - set(got))
    assert not only_judge and not only_census, (
        f"crossing sets differ over {len(stable)} stable tickets: judge-only {only_judge}, "
        f"census-only {only_census}")
    differ = {t: (sorted(got[t]), sorted(want[t])) for t in want if got[t] != want[t]}
    assert not differ, f"same tickets, different foreign regions (judge, census): {differ}"


def test_5_a_charter_committed_in_a_worktree_moves_the_charter_list():
    # THE CACHE STAMP (akiendell_cc_0's review of this judge, 2026-11-14): _charter_dirs stamped on
    # ``root/.git/index``; in a worktree ``.git`` is a gitfile whose mtime never moves on a commit, so
    # a process holding a worktree root served a stale list after a charter was added.
    import cairn.machines.build_inspector.inspector as I
    d = scratch_dir("charter-cache-proof-")
    main, wt = d / "main", d / "wt"
    env = git_env()

    def git(where: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(where), "-c", "user.name=proof", "-c", "user.email=proof@example.invalid",
                        "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, env=env)

    try:
        subprocess.run(["git", "init", "-q", str(main)], check=True, env=env)
        c1 = main / "cairn" / "tools" / "a" / "intention+why.json"
        c1.parent.mkdir(parents=True)
        c1.write_text("{}\n", encoding="utf-8", newline="\n")
        git(main, "add", "-A")
        git(main, "commit", "-q", "-m", "one charter")
        git(main, "worktree", "add", "-q", "-b", "wt", str(wt))
        assert (wt / ".git").is_file(), "the fixture is not a worktree: .git is not a gitfile"
        before = I._charter_dirs(wt)
        assert before == frozenset({"cairn/tools/a"}), before
        c2 = wt / "cairn" / "tools" / "b" / "intention+why.json"
        c2.parent.mkdir(parents=True)
        c2.write_text("{}\n", encoding="utf-8", newline="\n")
        git(wt, "add", "-A")
        git(wt, "commit", "-q", "-m", "a second charter")
        after = I._charter_dirs(wt)
        assert after == frozenset({"cairn/tools/a", "cairn/tools/b"}), (
            f"the charter list did not move after a charter was committed in a worktree: {sorted(after)}")
    finally:
        subprocess.run(["git", "-C", str(main), "worktree", "prune"], capture_output=True, env=env)
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    failed = 0
    for name in [n for p in PROVES.values() for n in p.values()]:
        try:
            globals()[name]()
            print(f"ok   {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)

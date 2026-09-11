"""Proof for cairn/tools/cairnmap — teeth a hollow help surface could not pass.

Runs against a SYNTHETIC two-root world (CAIRN_ROOTS_PARENT + CAIRN_SKILLS_INSTALL_DIR);
the live tree is never read or written. NON-VACUITY is structural: every defect tooth
builds the consistent world, asserts it GREEN, then introduces exactly one defect and
asserts the red names it — so a gate that reds unconditionally fails the first half and
one that greens unconditionally fails the second.

    python3 cairn/tools/cairnmap/proofs/test_cairnmap.py     # exit 0 = green
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.cairnmap import cairnmap, cli  # noqa: E402
from cairn.tools.gate import gate  # noqa: E402

# WHICH TOOTH ANSWERS WHICH FALSIFIER CLAUSE — the declaration `cairn test --hollow`
# reads. Ticket 7aed0fd0ba29's falsifier is written as one prose DONE-when sentence
# rather than an enumerated list, so proof_coverage.clauses() reads it as the single
# clause "all" and one tooth has to carry it.
#
# THE TOOTH CHOSEN IS THE DISCRIMINATING ONE, not the broadest. Against the reverted
# build — the pre-build reader, which swallows the absent key via
# `.get("members_so_far", [])` and returns ([], None) — this tooth goes RED, because a
# node class carrying no membership rule produces NO fault there at all. A tooth that
# merely exercises the gate would stay green on the hollow build and certify nothing.
PROVES = {
    "7aed0fd0ba29": {
        "all": "test_a_node_class_with_no_membership_rule_is_ONE_red",
    },
}


# ── the synthetic world ──────────────────────────────────────────────────────

def build_world(parent: Path) -> dict:
    """A consistent world: two charter'd+rostered+installed skills, one component
    whose charter owns the one command, nothing dangling. GREEN by construction."""
    repo = parent / "cairn"
    commons = parent / "CairnCommons"
    install = parent / "install"

    widget = repo / "cairn" / "widget"
    widget.mkdir(parents=True)
    (widget / "widget.py").write_text("# grinds\n")
    (widget / cairnmap.CHARTER).write_text(json.dumps({
        "component": "widget",
        "what": "THE WIDGET — grinds the grist. Slowly, and on purpose.",
        "invoke": "`cairn goodcmd` grinds once. Import: from cairn.widget import widget.",
    }))

    for name, what in (("alpha", "THE ALPHA SKILL — asks first. Then asks again."),
                       ("beta", "THE BETA SKILL — proves last. A tooth, not a vibe.")):
        d = repo / "skills" / name
        d.mkdir(parents=True)
        (d / cairnmap.CHARTER).write_text(json.dumps({"component": name, "what": what}))

    cmd = repo / "bin" / "cmd"
    cmd.mkdir(parents=True)
    (cmd / "goodcmd").write_text("#!/bin/sh\n")
    (cmd / "goodcmd").chmod(0o755)

    nc = commons / "node_classes"
    nc.mkdir(parents=True)
    # THE RULE, NOT A LIST. The corpus retired `members_so_far` on 2026-08-28; a fixture
    # still writing it would build a world the live one no longer has, and a proof over a
    # world that does not exist proves nothing about the one that does. The rule names
    # `skills/`, which this fixture has just populated with alpha and beta — so the
    # membership set is DERIVED here exactly as it is derived live.
    (nc / "skill.json").write_text(json.dumps(
        {"members_derived_by": "ls -d ~/dev/src/cairn/skills/*/ | grep -v __pycache__"}))

    install.mkdir()
    for name in ("alpha", "beta"):
        (install / name).symlink_to(repo / "skills" / name)

    return {"parent": parent, "repo": repo, "commons": commons, "install": install}


@contextlib.contextmanager
def world():
    old_env = {k: os.environ.get(k) for k in ("CAIRN_ROOTS_PARENT", "CAIRN_SKILLS_INSTALL_DIR")}
    with tempfile.TemporaryDirectory() as tmp:
        w = build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = str(w["parent"])
        os.environ["CAIRN_SKILLS_INSTALL_DIR"] = str(w["install"])
        try:
            yield w
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def assert_green(w):
    reds = cairnmap.check()
    assert reds == [], f"the consistent world must be GREEN before a defect is introduced: {reds}"


def one_red(w, needle: str) -> str:
    reds = cairnmap.check()
    assert len(reds) == 1, f"exactly one defect was introduced, expected exactly one red: {reds}"
    assert needle in reds[0], f"the red must NAME the defect ({needle!r}): {reds[0]}"
    return reds[0]


def run_cli(argv) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


# ── teeth ────────────────────────────────────────────────────────────────────

def test_green_world_and_direction_one():
    """Completeness direction one: every charter'd thing appears; gate exits 0."""
    with world():
        assert_green(None)
        code, out = run_cli(["--gate"])
        assert code == 0 and "green" in out, f"gate over a green world: {code}, {out!r}"
        surface = cairnmap.render_map()
        for expected in ("/alpha", "/beta", "goodcmd", "cairn/widget",
                         "grinds the grist", "asks first", "proves last", "green"):
            assert expected in surface, f"charter'd fact missing from the surface: {expected!r}"


def test_a_node_class_with_no_membership_rule_is_ONE_red():
    """THE DEFECT THIS TOOTH WAS CAST FOR (ticket 7aed0fd0ba29), and the shape its
    sibling below could never reach.

    The old reader said ``.get("members_so_far", [])``. A CORRUPT file raised and was
    caught — the tooth for that is
    ``test_a_check_that_stops_running_makes_the_record_shorter``, and it passed for a
    year. An ABSENT KEY raises NOTHING: the call returns ``[]``, the error stays None,
    the guard never fires, and the empty set sails into the comparison lanes as though
    it were an answer. That is precisely what the live corpus did on 2026-08-28 when it
    deleted the key, and what nothing noticed until 2026-09-09: 15 findings claiming
    fifteen skills were missing from a roster that did not exist.

    The world here is VALID JSON and simply says nothing about membership. One fault,
    one red, and the derived lane ABSENT rather than green.
    """
    with world() as w:
        assert_green(w)
        whole = [e["identity"] for e in cairnmap.inspect()]
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({"what": "a node class that forgot to say how"}))

        after = cairnmap.inspect()
        names = [e["identity"] for e in after]
        assert "every_skill_directory_carries_a_charter" not in names, (
            "a lane whose input could not be read must be ABSENT, never green: " + str(names))
        assert len(after) < len(whole), (
            "the record must get SHORTER when a check stops running: " + str(names))
        one_red(w, "skill membership has no rule")


def test_the_retired_roster_coming_back_is_ONE_red():
    """Two mouths answering one question is the defect the 2026-08-28 retirement removed.

    A `members_so_far` reappearing beside `members_derived_by` is not a harmless extra
    field: it is a second answer that can disagree with the first, and the corpus has
    already measured that disagreement three times (the node class's own `roster_note`).
    So the reader reds on its PRESENCE rather than quietly preferring one of them.
    """
    with world() as w:
        assert_green(w)
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({
            "members_derived_by": "ls -d ~/dev/src/cairn/skills/*/ | grep -v __pycache__",
            "members_so_far": ["/alpha", "/beta"]}))
        one_red(w, "the retired roster is back")


def test_a_rule_that_derives_from_elsewhere_is_ONE_red():
    """Agreeing with a rule you do not actually follow is luck, not derivation."""
    with world() as w:
        assert_green(w)
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({"members_derived_by": "ls -d ~/dev/src/cairn/machines/*/"}))
        one_red(w, "derived from elsewhere")


def test_skill_directory_with_no_charter_reds():
    """THE DIRECTION THAT SURVIVED THE RETIREMENT, and the proof that it still can red.

    ``every_chartered_skill_is_on_the_roster`` was retired on 2026-09-11 because under
    derivation it compares a set against a superset of itself — no world reds it. This
    one reads the same disagreement from the end that CAN still disagree: a directory
    the node class's rule calls a member, carrying no charter. The world exists, and
    here it is.
    """
    with world() as w:
        assert_green(w)
        (w["repo"] / "skills" / "gamma").mkdir()
        one_red(w, "skill directory with no charter: /gamma")


def test_uninstalled_skill_reds():
    with world() as w:
        assert_green(w)
        (w["install"] / "beta").unlink()
        one_red(w, "skill not installed: /beta")


def test_installed_without_charter_reds():
    with world() as w:
        assert_green(w)
        rogue = w["parent"] / "elsewhere"
        rogue.mkdir()
        (w["install"] / "delta").symlink_to(rogue)
        one_red(w, "installed skill with no charter: delta")


def test_misaimed_symlink_reds():
    with world() as w:
        assert_green(w)
        (w["install"] / "alpha").unlink()
        (w["install"] / "alpha").symlink_to(w["repo"] / "skills" / "beta")
        one_red(w, "points away from its charter'd source")


def test_uncharted_command_reds_and_does_not_render():
    """Completeness direction two: an undocumented command is a RED, never a help line."""
    with world() as w:
        assert_green(w)
        orphan = w["repo"] / "bin" / "cmd" / "orphancmd"
        orphan.write_text("#!/bin/sh\n")
        orphan.chmod(0o755)
        one_red(w, "command without a charter: bin/cmd/orphancmd")
        surface = cairnmap.render_map()
        assert "orphancmd" in surface, "the red itself must be IN the surface (Law 7)"
        for line in surface.splitlines():
            assert not (line.strip().startswith("orphancmd") and "—" in line), \
                f"an uncharted command must not render as a normal entry: {line!r}"


def test_corrupt_charter_is_loud_and_the_rest_still_renders():
    with world() as w:
        assert_green(w)
        (w["repo"] / "skills" / "beta" / cairnmap.CHARTER).write_text("{not json")
        reds = cairnmap.check()
        assert any("unreadable charter" in r and "beta" in r for r in reds), \
            f"a corrupt charter must be loudly named, not skipped: {reds}"
        surface = cairnmap.render_map()
        assert "/alpha" in surface and "asks first" in surface, \
            "one wreck must not take the rest of the surface down"


def test_code_without_a_charter_reds():
    with world() as w:
        assert_green(w)
        rogue = w["repo"] / "cairn" / "rogue"
        rogue.mkdir()
        (rogue / "rogue.py").write_text("# unchartered\n")
        one_red(w, "component without a charter: cairn/rogue")


def test_standing_in_a_directory_briefs_on_it():
    """The contextual ruling: cwd inside a chartered dir -> that brief, not the map."""
    with world() as w:
        old = os.getcwd()
        try:
            os.chdir(w["repo"] / "cairn" / "widget")
            code, out = run_cli([])
            assert code == 0
            assert "grinds the grist" in out and "Slowly, and on purpose" in out
            assert "CAIRNMAP — compiled" not in out, "standing in a component must brief, not map"
            os.chdir(w["repo"])
            code, out = run_cli([])
            assert "CAIRNMAP — compiled" in out, "standing at the root must map"
        finally:
            os.chdir(old)


def test_named_brief_and_unknown_name_refusal():
    with world():
        code, out = run_cli(["widget"])
        assert code == 0 and "grinds the grist" in out
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code, _ = run_cli(["no-such-thing"])
        assert code == 2 and "no charter" in buf.getvalue(), \
            "an unknown name must refuse loudly, not render an empty page"


def test_gate_exit_codes_and_render_always_presents():
    """A gate's exit code IS its verdict; a view presents even when red inside."""
    with world() as w:
        assert_green(w)
        (w["repo"] / "skills" / "gamma").mkdir()
        code, out = run_cli(["--gate"])
        assert code == 1 and "RED" in out, f"gate over a red world: {code}, {out!r}"
        code, out = run_cli([])
        assert code == 0 and "RED" in out, \
            "the plain render must still present, with the red loud in it"


def test_first_sentence_is_a_cut_never_a_break():
    fs = cairnmap.first_sentence
    assert fs("Grinds. Slowly.") == "Grinds."
    assert fs("Reads /a/b.c/d then stops. More.") == "Reads /a/b.c/d then stops.", \
        "a dot inside a token is not a sentence break"
    assert fs("no terminator at all") == "no terminator at all"
    assert fs("  spread\n over   lines. tail") == "spread over lines."


def test_render_mutates_nothing():
    """Falsifier (8): a view that writes is a device wearing a view's clothes."""
    with world() as w:
        before = sorted(str(p.relative_to(w["parent"])) + str(p.stat().st_mtime_ns)
                        for p in w["parent"].rglob("*"))
        cairnmap.render_map()
        cairnmap.check()
        run_cli(["--gate"])
        after = sorted(str(p.relative_to(w["parent"])) + str(p.stat().st_mtime_ns)
                       for p in w["parent"].rglob("*"))
        assert before == after, "rendering touched the world"


def test_the_gate_lists_what_it_proved_not_only_what_failed():
    """Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED."

    The tooth a hollow record could not pass, and it is TWO assertions because the
    defect has two faces. FACE ONE: on a wholly consistent world the record must be
    NON-EMPTY and every entry must have PASSED — a complaint list greens here too, so
    this half alone proves nothing, which is exactly why it is paired. FACE TWO: every
    entry carries EXPECTED beside ACTUAL and they are equal on a pass, so an entry that
    stopped comparing anything cannot sit in the record looking green.

    THE FLOOR NAMES THE LANES RATHER THAN COUNTING THEM (changed 2026-09-11, ticket
    7aed0fd0ba29). It used to read ``len(record) >= 8``, and a count is the wrong
    instrument for "a lane went missing": it cannot say WHICH, it is satisfied by any
    replacement, and retiring one lane on purpose leaves a maintainer with a bare number
    to lower and no place to say why. Naming them costs one line per lane and makes the
    retirement of ``every_chartered_skill_is_on_the_roster`` an EDIT TO THIS LIST — which
    is exactly what "a deleted lane makes the record shorter, never cleaner" asks for.
    Deleting a name from here to make a red go away is the defect; do not.
    """
    expected_lanes = [
        "every_charter_parses",
        "every_component_carries_a_charter",
        "the_skill_membership_rule_is_declared",
        # RETIRED 2026-09-11: every_chartered_skill_is_on_the_roster — a tautology once
        # membership is derived from the same directory `chartered` is filtered out of.
        # Its surviving half is the next line; see cairnmap.py's lane assembly.
        "every_skill_directory_carries_a_charter",
        "every_chartered_skill_is_installed",
        "every_installed_skill_points_at_its_charter",
        "every_command_is_named_by_a_charter",
    ]
    with world() as w:
        assert_green(w)
        record = cairnmap.inspect()
        assert record, "an empty proof record is an error, not a pass"
        assert [e["identity"] for e in record] == expected_lanes, (
            "the record's lanes are not the declared set — a lane went missing, was "
            f"renamed, or appeared unannounced: {[e['identity'] for e in record]}")
        for entry in record:
            assert gate.passed(entry), f"consistent world, failing entry: {entry}"
            assert "expected" in entry and "actual" in entry, entry
            assert entry["expected"] == entry["actual"], entry
            assert entry["identity"], entry
            assert entry["location"], entry


def test_a_check_that_stops_running_makes_the_record_shorter():
    """The whole reason the record replaces the complaint list: absence must be VISIBLE.

    An unreadable node class is ONE fault. The skill lane cannot run against a membership
    set it could not derive, so the derived entry is ABSENT from the record — not silently
    passed, and not multiplied into one derived finding per skill. A reader diffing the two
    records SEES the check that stopped running.

    THIS TOOTH COVERS THE CORRUPT-FILE SHAPE ONLY, and that limit is the point: it passed
    continuously while the ABSENT-KEY shape went unguarded, because a corrupt file RAISES
    and an absent key does not. Its sibling
    ``test_a_node_class_with_no_membership_rule_is_ONE_red`` is the tooth for the shape
    this one cannot reach. Do not merge them.
    """
    with world() as w:
        assert_green(w)
        whole = [e["identity"] for e in cairnmap.inspect()]
        assert "every_skill_directory_carries_a_charter" in whole

        (w["commons"] / "node_classes" / "skill.json").write_text("{not json", encoding="utf-8")
        after = cairnmap.inspect()
        names = [e["identity"] for e in after]
        assert len(after) < len(whole), (
            "a check that could not run must make the record SHORTER, never cleaner: "
            f"{names}")
        assert "every_skill_directory_carries_a_charter" not in names, names

        failed = [e for e in after if not gate.passed(e)]
        assert [e["identity"] for e in failed] == ["the_skill_membership_rule_is_declared"], (
            "one fault must produce one failing entry, not one per skill: "
            f"{[e['identity'] for e in failed]}")
        assert len(cairnmap.check()) == 1, cairnmap.check()


def test_check_is_derived_from_the_record_and_never_parallel():
    """Two mouths for one question is how a gate and its sentence come to disagree.

    Every red ``check`` returns must be a red some FAILING entry carries — no red may be
    accumulated beside the record, and no failing entry may be silent in the reds.
    """
    with world() as w:
        assert_green(w)
        assert cairnmap.check() == []
        # one defect, then the two mouths must still agree
        (w["repo"] / "bin" / "cmd" / "ghost").write_text("#!/bin/sh\n", encoding="utf-8")
        (w["repo"] / "bin" / "cmd" / "ghost").chmod(0o755)
        record = cairnmap.inspect()
        from_record = [r for e in record if not gate.passed(e)
                       for r in e["values"]["reds"]]
        assert cairnmap.check() == from_record, (
            f"check() and the record disagree: {cairnmap.check()} vs {from_record}")
        assert any("ghost" in r for r in from_record), from_record


def test_the_watchme_probe_is_armed_and_can_be_made_to_fire():
    """A probe that cannot be made to fire on demand is a probe nobody has measured.

    TWO HALVES, because either alone is hollow. FIRST: the module is armed the way the
    emission gate reads it — a module-level frozen ``Probe`` carrying both a ``carry`` and
    an ``enough``. SECOND, and the one that costs something: its reading is handed a
    substitute reporting the PRE-BUILD behaviour, and it must FIRE. Before this build a
    node class that said nothing about membership left the reader lane PASSING (an absent
    key returned an empty set with no error) and sent the empty set into the comparison
    lane, where it became one red per chartered skill. That is the world reconstructed
    below, and a probe that stayed quiet through it would be watching nothing.
    """
    from cairn.tools.base.probe import Probe
    from cairn.tools.cairnmap.probes import the_roster_fault_is_one_finding as probe

    assert isinstance(probe.PROBE, Probe), "the emission gate reads a module-level PROBE"
    assert callable(probe.PROBE.carry) and callable(probe.PROBE.enough), \
        "the ticket's watchme spec binds both a carry and an enough"

    def entry(identity, reds):
        return {"identity": identity, "location": "fixture", "code": "fixture",
                "expected": [], "actual": list(reds), "fatality": "none",
                "source": "fixture", "values": {"reds": list(reds), "lack": ""}}

    def pre_build_record(node_class_text: str):
        """The 2026-09-09 behaviour: an absent key is an empty answer, not a fault."""
        starved = "members_derived_by" not in node_class_text
        return [
            entry("every_charter_parses", []),
            # PASSING even when starved — this is the whole defect.
            entry("the_skill_roster_is_readable", []),
            entry("every_chartered_skill_is_on_the_roster",
                  [f"skill missing from the roster: /s{i}" for i in range(15)]
                  if starved else []),
            entry("every_roster_entry_carries_a_charter", []),
        ]

    fired = probe.multiplication_reading(record_of=pre_build_record)
    assert fired["fires"], (
        "the probe must FIRE against the pre-build behaviour it was armed to watch: "
        f"{fired}")
    assert fired["reds_from_one_fault"] == 15, fired
    assert "multiplied" in fired["what"], fired["what"]

    def post_build_record(node_class_text: str):
        """Today's behaviour: one fault, one red, the derived lane absent."""
        starved = "members_derived_by" not in node_class_text
        record = [entry("every_charter_parses", []),
                  entry("the_skill_membership_rule_is_declared",
                        ["skill membership has no rule: <fixture>"] if starved else [])]
        if not starved:
            record.append(entry("every_skill_directory_carries_a_charter", []))
        return record

    quiet = probe.multiplication_reading(record_of=post_build_record)
    assert not quiet["fires"], f"the probe must be quiet against the built behaviour: {quiet}"
    assert quiet["reds_from_one_fault"] == 1 and quiet["derived_lane_absent"], quiet


# ── runner ───────────────────────────────────────────────────────────────────
#
# TEETH IS COLLECTED AT CALL TIME, NOT AT IMPORT TIME (changed 2026-09-11, ticket
# 7aed0fd0ba29). It used to be a module-level list comprehension over globals(), which
# silently EXCLUDES any tooth defined below it — and a tooth appended to the end of the
# file is the single most natural way to add one. Measured the same day: a new tooth was
# appended, the file printed "19/19 teeth green", and the tooth had never run. A collector
# that reports a confident green over a test it did not execute is the hollow pass Law 8
# calls worse here than a red. Collecting inside main() makes file order irrelevant.


def teeth() -> list:
    return [v for k, v in sorted(globals().items()) if k.startswith("test_")]


if __name__ == "__main__":
    all_teeth = teeth()
    failed = 0
    for tooth in all_teeth:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(all_teeth) - failed}/{len(all_teeth)} teeth green")
    sys.exit(1 if failed else 0)

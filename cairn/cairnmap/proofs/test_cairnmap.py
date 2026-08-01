"""Proof for cairn/cairnmap — teeth a hollow help surface could not pass.

Runs against a SYNTHETIC two-root world (CAIRN_ROOTS_PARENT + CAIRN_SKILLS_INSTALL_DIR);
the live tree is never read or written. NON-VACUITY is structural: every defect tooth
builds the consistent world, asserts it GREEN, then introduces exactly one defect and
asserts the red names it — so a gate that reds unconditionally fails the first half and
one that greens unconditionally fails the second.

    python3 cairn/cairnmap/proofs/test_cairnmap.py     # exit 0 = green
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from cairn.cairnmap import cairnmap, cli  # noqa: E402


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
    (nc / "skill.json").write_text(json.dumps({"members_so_far": ["/alpha", "/beta"]}))

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


def test_roster_omission_reds():
    """The measured 2026-07-31 defect: chartered + installed, absent from the roster."""
    with world() as w:
        assert_green(w)
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({"members_so_far": ["/alpha"]}))
        one_red(w, "missing from the roster: /beta")


def test_roster_entry_with_no_charter_reds():
    with world() as w:
        assert_green(w)
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({"members_so_far": ["/alpha", "/beta", "/gamma"]}))
        one_red(w, "roster entry with no charter: /gamma")


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
        nc = w["commons"] / "node_classes" / "skill.json"
        nc.write_text(json.dumps({"members_so_far": ["/alpha"]}))
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


# ── runner ───────────────────────────────────────────────────────────────────

TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)

"""Proof for cairn/tools/edges — the frontier projector.

Synthetic world via CAIRN_ROOTS_PARENT (the cairnmap seam). Two lanes: filed
edges from charters, open questions from CairnCommons/questions/. The render
mutates nothing, the lanes never mix, and the surface is compiled.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

# ── synthetic world builder ─────────────────────────────────────────────────

def _build_world(tmp: Path) -> tuple[Path, Path]:
    """A minimal two-root world with charters and questions."""
    repo = tmp / "cairn"
    commons = tmp / "CairnCommons"

    # a chartered device with two filed edges
    device_dir = repo / "cairn" / "devices" / "alpha"
    device_dir.mkdir(parents=True)
    (device_dir / "intention+why.json").write_text(json.dumps({
        "component": "alpha",
        "what": "A test device.",
        "filed_edges": [
            "(a) FIRST EDGE — something to build",
            "(b) CLOSED 2026-01-01 — already retired",
        ],
    }))

    # a chartered tool with one edge
    tool_dir = repo / "cairn" / "tools" / "beta"
    tool_dir.mkdir(parents=True)
    (tool_dir / "intention+why.json").write_text(json.dumps({
        "component": "beta",
        "what": "A test tool.",
        "filed_edges": ["(a) ONE EDGE"],
    }))

    # a charter with no filed_edges — should contribute nothing
    bare_dir = repo / "cairn" / "tools" / "gamma"
    bare_dir.mkdir(parents=True)
    (bare_dir / "intention+why.json").write_text(json.dumps({
        "component": "gamma",
        "what": "No edges here.",
    }))

    # a charter with a non-string edge — should red
    bad_dir = repo / "cairn" / "devices" / "delta"
    bad_dir.mkdir(parents=True)
    (bad_dir / "intention+why.json").write_text(json.dumps({
        "component": "delta",
        "what": "Bad edge shape.",
        "filed_edges": [{"edge": "this is a dict, not a string"}],
    }))

    # one open question, one resolved question
    qdir = commons / "questions"
    qdir.mkdir(parents=True)
    (qdir / "open-is-the-sky-blue.json").write_text(json.dumps({
        "id": "open-is-the-sky-blue",
        "question": "Is the sky blue?",
        "date": "2026-01-01",
        "raised_by": "CC",
        "resolved": None,
    }))
    (qdir / "open-was-it-raining.json").write_text(json.dumps({
        "id": "open-was-it-raining",
        "question": "Was it raining?",
        "date": "2026-01-01",
        "raised_by": "CC",
        "resolved": {"date": "2026-01-02", "answer": "No."},
    }))

    # skill roster (cairnmap.gather needs it for the walk, but edges doesn't
    # care about it — still, the world needs to be valid for gather)
    nc = commons / "node_classes"
    nc.mkdir(parents=True)
    (nc / "skill.json").write_text(json.dumps({"members_so_far": []}))

    return repo, commons


# ── teeth ───────────────────────────────────────────────────────────────────

def test_non_vacuity():
    """The consistent world renders edges and questions — the surface is not empty."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        output = edges.render(repo, commons)

        assert "FRONTIER" in output
        assert "FIRST EDGE" in output
        assert "ONE EDGE" in output
        assert "open-is-the-sky-blue" in output
        assert "open-was-it-raining" in output
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_edges_from_charters():
    """Every filed_edge from a charter appears, tagged by component."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        found, reds = edges.gather_edges(repo)

        components = {e["component"] for e in found}
        assert "alpha" in components
        assert "beta" in components
        assert "gamma" not in components  # no edges

        alpha_edges = [e for e in found if e["component"] == "alpha"]
        assert len(alpha_edges) == 2
        assert alpha_edges[0]["label"] == "a"
        assert alpha_edges[1]["label"] == "b"
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_non_string_edge_is_red():
    """A filed_edge that is a dict instead of a string is a RED, not skipped."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        found, reds = edges.gather_edges(repo)

        delta_edges = [e for e in found if e["component"] == "delta"]
        assert len(delta_edges) == 0, "dict edge should not appear as a normal edge"
        assert any("non-string edge" in r and "delta" in r for r in reds)
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_open_vs_resolved_questions():
    """Open questions show as OPEN, resolved show as done."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        questions, reds = edges.gather_questions(commons)

        assert len(questions) == 2
        by_id = {q["id"]: q for q in questions}
        assert by_id["open-is-the-sky-blue"]["resolved"] is None
        assert by_id["open-was-it-raining"]["resolved"] is not None

        output = edges.render(repo, commons)
        assert "OPEN  open-is-the-sky-blue" in output
        assert "done  open-was-it-raining" in output
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_lanes_never_mixed():
    """Edges don't appear in the questions section; questions don't appear in the edges section."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        output = edges.render(repo, commons)

        lines = output.split("\n")
        edge_section = []
        question_section = []
        current = None
        for line in lines:
            if "filed edges" in line and "──" in line:
                current = "edges"
                continue
            if "open questions" in line and "──" in line:
                current = "questions"
                continue
            if line.startswith("──") and current:
                current = None
                continue
            if current == "edges":
                edge_section.append(line)
            elif current == "questions":
                question_section.append(line)

        edge_text = "\n".join(edge_section)
        question_text = "\n".join(question_section)

        assert "open-is-the-sky-blue" not in edge_text
        assert "FIRST EDGE" not in question_text
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_render_mutates_nothing():
    """The render is a view — it creates no files and changes no files."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        def snapshot(root: Path) -> dict[str, str]:
            out = {}
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    out[str(p.relative_to(root))] = p.read_text(encoding="utf-8")
            return out

        before_repo = snapshot(repo)
        before_commons = snapshot(commons)

        from cairn.tools.edges import edges
        edges.render(repo, commons)

        assert snapshot(repo) == before_repo, "render mutated the repo"
        assert snapshot(commons) == before_commons, "render mutated CairnCommons"
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_summary_line():
    """The summary counts edges, open questions, resolved questions, and reds."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        from cairn.tools.edges import edges
        output = edges.render(repo, commons)

        assert "3 edges" in output           # alpha(2) + beta(1); delta's dict-edge is a red
        assert "1 open questions" in output
        assert "1 resolved" in output
        assert "1 reds" in output            # delta's non-string edge
        del os.environ["CAIRN_ROOTS_PARENT"]


def test_unreadable_question_is_red():
    """A question file that fails to parse is a RED, never a skip."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, commons = _build_world(Path(tmp))
        os.environ["CAIRN_ROOTS_PARENT"] = tmp

        bad = commons / "questions" / "open-corrupt.json"
        bad.write_text("NOT JSON {{{", encoding="utf-8")

        from cairn.tools.edges import edges
        questions, reds = edges.gather_questions(commons)
        assert any("unreadable question" in r and "corrupt" in r for r in reds)
        del os.environ["CAIRN_ROOTS_PARENT"]


# ── live corpus ─────────────────────────────────────────────────────────────

def test_live_corpus_renders():
    """The live corpus renders without crashing — a smoke tooth over the real tree."""
    from cairn.tools.edges import edges
    output = edges.render()
    assert "FRONTIER" in output
    assert "edges" in output


if __name__ == "__main__":
    import sys

    tests = [
        test_non_vacuity,
        test_edges_from_charters,
        test_non_string_edge_is_red,
        test_open_vs_resolved_questions,
        test_lanes_never_mixed,
        test_render_mutates_nothing,
        test_summary_line,
        test_unreadable_question_is_red,
        test_live_corpus_renders,
    ]
    failed = 0
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"  pass  {name}")
        except Exception as exc:
            print(f"  FAIL  {name}: {exc}")
            failed += 1
    print(f"\n{'GREEN' if not failed else 'RED'} — {len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)

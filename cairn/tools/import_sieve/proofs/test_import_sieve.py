"""Proof for import_sieve — the mesh, and the floor under a clean result.

This component exists to turn five prose IOUs into physics, so the teeth that matter are
the ones a HOLLOW sieve passes: one that catches nothing catches nothing on a clean corpus
too, and reports the identical green. Every catching tooth here is therefore paired —
the same rule is shaken over a PLANTED graph (must catch) and over the real corpus (must
not) — because either half alone is satisfied by a sieve made of solid sheet metal.

The walk (`reaches`, and the `unreachable` kind that seats it) has a THIRD way to be
wrong on top of those two: it can stop short, and a closure that silently comes back
empty reads exactly like a corpus with nothing to find. So its teeth pin all three — a
breach two hops down that must be caught, a module that breaches identically OFF the
path and must not be, and the hollow floor still raising for a kind written after it.

The mesh teeth are the corpus's own two lessons, re-armed as permanent traps:

  - `urllib.parse.parse_qs` is string work; `urllib.request` is a door. A word-matching
    scan cannot tell them apart, and web_server/server.py is the live instance that would
    have gone red on day one.
  - `http.server` LISTENS. A dial rule that catches it reds the one component whose entire
    job is to be reachable.
  - a docstring naming psycopg2 is prose. learning_block learned this in miniature on
    2026-08-01 when its own honest docstring tripped its own tooth.

    python3 cairn/tools/import_sieve/proofs/test_import_sieve.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.import_sieve import sieve

DIALS = ("urllib.request", "urllib.error", "http.client", "requests", "httpx",
         "aiohttp", "socket", "ftplib", "telnetlib")


def _corpus():
    return sieve.import_graph(str(_REPO_ROOT))


def _planted(**files):
    """A graph big enough to clear the hollow floor, carrying exactly the planted defects."""
    g = {f"filler/mod_{i}.py": {"json"} for i in range(25)}
    for path, src in files.items():
        g[path] = sieve.imports_in(src)
    return g


# ── the mesh: capability, never mention ──────────────────────────────────────


def test_a_parse_is_not_a_dial():
    """urllib.parse is no more a door than str.split. This is the live case: the corpus
    really does import parse_qs in web_server, and a word-matching mesh reds it."""
    caught = sieve.imports_in("from urllib.parse import parse_qs")
    assert "urllib.parse" in caught and "urllib.parse.parse_qs" in caught
    assert not any(sieve._matches(m, "urllib.request") for m in caught), \
        "urllib.parse was caught by a urllib.request mesh — the mesh is matching the word"
    assert sieve._matches("urllib.request.urlopen", "urllib.request"), \
        "the mesh must still catch the leaf under a real dialing module"


def test_listening_is_not_dialing():
    """web_server serves; it cannot reach anything. A dial rule that catches it is wrong."""
    g = _planted(**{"cairn/devices/web_server/listener.py":
                    "from http.server import ThreadingHTTPServer"})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                               "modules": DIALS, "only": "cairn/devices/inference_domain/"})
    assert caught == [], f"a listening server was caught by an outbound mesh: {caught}"


def test_prose_is_not_an_import():
    """A docstring naming the driver is a description of a door, not a door."""
    g = _planted(**{"a/doc.py": '"""We reach 5432 only via psycopg2, through db_domain."""\nimport json'})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "5432",
                               "modules": ("psycopg2",), "only": "cairn/devices/db_domain/"})
    assert caught == [], f"prose about psycopg2 was caught as an import: {caught}"


def test_an_in_tree_leaf_import_is_visible():
    """`from cairn.machines.build_inspector import inspector` must be catchable. Recording only the
    MODULE (what the hand-rolled scan did) makes every in-tree edge invisible at the leaf."""
    caught = sieve.imports_in("from cairn.machines.build_inspector import inspector")
    assert "cairn.machines.build_inspector" in caught, "the package must be recorded"
    assert "cairn.machines.build_inspector.inspector" in caught, "the leaf must be recorded too"


def test_an_unparseable_file_is_not_a_door():
    assert sieve.imports_in("def (((") == set(), "a syntax error is unimportable, not a door"


# ── the floor: clean and did-not-run must never look alike ───────────────────


def test_a_sieve_over_nothing_raises_rather_than_passing():
    try:
        sieve.catches({"one.py": set()}, {"kind": "sole_path", "capability": "x",
                                          "modules": ("socket",), "only": "nowhere/"})
    except sieve.HollowScan as e:
        assert "did not read the tree" in str(e), f"the raise must say WHY: {e}"
    else:
        raise AssertionError("a sieve over 1 file returned clean — a hollow green (Law 8)")


def test_the_real_corpus_clears_the_floor():
    g = _corpus()
    assert len(g) > 150, f"the corpus scan only saw {len(g)} files — it is not reading the tree"


# ── sole_path: paired, so a solid-sheet sieve cannot pass ────────────────────


def test_sole_path_catches_a_second_door():
    g = _planted(**{"skills/rogue/probe.py": "import socket",
                    "cairn/devices/inference_domain/host.py": "import urllib.request"})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                               "modules": DIALS, "only": "cairn/devices/inference_domain/"})
    assert len(caught) == 1, f"exactly the rogue should be caught, got {caught}"
    assert "skills/rogue/probe.py" in caught[0] and "socket" in caught[0]
    assert "cairn/devices/inference_domain/" in caught[0], "the refusal must name the door that IS allowed"


def test_sole_path_is_clean_on_the_real_corpus_for_both_domains():
    """The other half of the pair. Measured 2026-08-06: one dialer (inference_domain/host.py),
    one driver importer (db_domain/store.py). If this reds, a second door was built."""
    g = _corpus()
    host = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                             "modules": DIALS, "only": "cairn/devices/inference_domain/"})
    assert host == [], f"a second door to the inference host: {host}"
    db = sieve.catches(g, {"kind": "sole_path", "capability": "port 5432",
                           "modules": ("psycopg2", "psycopg", "asyncpg", "pg8000", "sqlalchemy"),
                           "only": "cairn/devices/db_domain/"})
    assert db == [], f"a second door to 5432: {db}"


# ── forbidden: the fork ──────────────────────────────────────────────────────


def test_forbidden_catches_a_fork_breach_and_spares_everyone_else():
    g = _planted(**{"cairn/machines/diagnostic_inspector/inspector.py":
                    "from cairn.machines.build_inspector import inspector",
                    "cairn/devices/tester/device.py": "from cairn.machines.build_inspector import inspector"})
    caught = sieve.catches(g, {"kind": "forbidden", "capability": "the shared inspection library",
                               "modules": ("cairn.machines.build_inspector",),
                               "within": "cairn/machines/diagnostic_inspector/"})
    assert len(caught) == 1, f"only the forked component is bound by its fork: {caught}"
    assert "diagnostic_inspector" in caught[0]


def test_an_unknown_sieve_kind_is_refused_not_silently_clean():
    try:
        sieve.catches(_planted(), {"kind": "vibes", "modules": ()})
    except ValueError as e:
        assert "sole_path" in str(e), "the refusal must name the kinds that exist"
    else:
        raise AssertionError("an unknown kind returned clean — a typo'd rule would pass forever")


# ── importers_of: the ruling door's question ─────────────────────────────────


def test_importers_of_finds_the_live_carriers_of_a_primitive():
    """cairn/tools/base/probe.py is the file two ruling packets sentenced to death while eight
    live modules imported it. That is the trouble this query closes."""
    g = _corpus()
    hits = sieve.importers_of(g, "cairn/tools/base/probe.py")
    assert len(hits) >= 5, f"probe.py's importers should be many, got {hits}"
    assert any("shim.py" in h for h in hits), f"base/shim.py imports probe: {hits}"


def test_importers_of_is_empty_for_a_module_nobody_imports():
    g = _corpus()
    assert sieve.importers_of(g, "cairn/tools/import_sieve/proofs/test_import_sieve.py") == [], \
        "a proof nobody imports must come back empty — that is what makes deletion safe"


def test_a_module_is_not_its_own_importer():
    g = {"a/b.py": {"a.b"}, **{f"f/{i}.py": set() for i in range(25)}}
    assert sieve.importers_of(g, "a/b.py") == [], "self-reference is not an importer"


def test_module_name_folds_a_package_init():
    assert sieve.module_name("cairn/tools/base/probe.py") == "cairn.tools.base.probe"
    assert sieve.module_name("cairn/tools/base/__init__.py") == "cairn.tools.base"


# ── unreachable: the walk, and the three ways it can be wrong ────────────────
# Paired like the two kinds above, and for one extra reason on top of the hollow-sieve
# one: a walk that silently returns NOTHING is invisible from the passing side. The
# real-corpus tooth and the spares-the-stranger tooth both pass against a walker stubbed
# to `lambda *a, **k: {}`; only `test_unreachable_catches_a_breach_two_hops_down` fails
# there, which is what makes it the tooth carrying the weight (Law 8).

# start -> mid_hop -> leaf, and leaf reaches the denied door. The breach is TWO hops
# from the start, so a single-hop rule reads this graph as clean. The stranger breaches
# identically and is not reachable from the start at all — that file is the whole
# difference between this kind and `forbidden`, which would catch both.
_FIRE_PATH_GRAPH = {
    "cairn/fire/start.py": "import cairn.fire.mid_hop",
    "cairn/fire/mid_hop.py": "import cairn.deep.leaf",
    "cairn/deep/leaf.py": "import cairn.devices.librarian.session",
    "cairn/elsewhere/stranger.py": "import cairn.devices.librarian.session",
}

_UNREACHABLE_RULE = {"kind": "unreachable", "capability": "the graph tree",
                     "modules": ("cairn.devices.librarian",), "start": "cairn/fire/start.py"}


def test_reaches_walks_past_the_first_hop_and_keeps_the_shortest_chain():
    """`importers_of` is one hop backwards; this is any number of hops forwards. The
    chain is what makes a finding readable — a breach reported without its route sends
    the reader back to re-derive how the fire path got there."""
    g = _planted(**{"a/start.py": "import a.mid\nimport a.leaf",
                    "a/mid.py": "import a.leaf",
                    "a/leaf.py": "import json"})
    r = sieve.reaches(g, "a/start.py")
    assert set(r) == {"a/mid.py", "a/leaf.py"}, f"the closure is wrong: {r}"
    assert r["a/leaf.py"] == ["a/start.py", "a/leaf.py"], \
        f"the SHORTEST chain must win — a longer route reads as a deeper problem: {r}"
    assert "a/start.py" not in r, "a module does not reach itself, same as importers_of"


def test_reaches_refuses_a_start_it_never_read():
    """The hollow floor's little brother. A walk from a file the scan never saw returns
    an empty closure, and an empty closure is clean for the wrong reason."""
    g = _planted(**{"a/start.py": "import json"})
    try:
        sieve.reaches(g, "a/never_scanned.py")
    except ValueError as e:
        assert "not in the graph" in str(e), f"the refusal must say WHY: {e}"
    else:
        raise AssertionError("a walk from an unknown start returned clean")


def test_an_import_of_nothing_is_a_dead_end_not_an_error():
    """Every corpus imports stdlib and third-party names that are not files in the tree.
    If those raised, the walk would be unusable on the only graph it exists to walk."""
    g = _planted(**{"a/start.py": "import json\nimport numpy.linalg\nimport a.mid",
                    "a/mid.py": "import os"})
    assert set(sieve.reaches(g, "a/start.py")) == {"a/mid.py"}


def test_unreachable_catches_a_breach_two_hops_down():
    """THE TOOTH THAT CARRIES THE WEIGHT. Stub `sieve.reaches` to return {} and this is
    the one that fails; every other tooth in this block still passes."""
    caught = sieve.catches(_planted(**_FIRE_PATH_GRAPH), _UNREACHABLE_RULE)
    assert len(caught) == 1, f"exactly the reachable breacher should be caught: {caught}"
    assert "cairn/deep/leaf.py" in caught[0], f"the finding must name the breacher: {caught}"
    assert "cairn.devices.librarian.session" in caught[0], \
        f"the finding must name the door that was reached: {caught}"
    assert "cairn.fire.mid_hop" in caught[0], (
        "the route must name the module the walk passed THROUGH — without it the "
        f"finding is indistinguishable from a single-hop catch: {caught}")


def test_unreachable_spares_a_breacher_the_fire_path_cannot_reach():
    """The over-reach half, and the line between this kind and `forbidden`. The stranger
    imports the denied door exactly as the breacher does; it is simply not on the path.
    A rule that caught it would be a corpus-wide ban wearing a reachability rule's name."""
    caught = sieve.catches(_planted(**_FIRE_PATH_GRAPH), _UNREACHABLE_RULE)
    assert not any("stranger" in c for c in caught), \
        f"a module outside the closure was caught — this is a forbidden scan, not a walk: {caught}"


def test_unreachable_catches_a_breach_at_the_start_itself():
    """The loudest version of the failure is the one a walk over what the start reaches
    steps straight over: the start dialing the denied door directly."""
    caught = sieve.catches(_planted(**{"cairn/fire/start.py": "import cairn.devices.librarian.session",
                                       "cairn/fire/mid_hop.py": "import json"}),
                           _UNREACHABLE_RULE)
    assert len(caught) == 1 and "cairn/fire/start.py" in caught[0], caught


def test_unreachable_is_clean_on_the_real_corpus():
    """The other half of the pair, asserted as an INVARIANT. Measured 2026-08-12: the
    graph holds 243 files, the closure from inspector.py is 17, and no denied door is
    among them — so the rule goes green the day it lands. Those numbers ride as evidence;
    pinning them would red this tooth the moment the corpus legitimately grows."""
    g = _corpus()
    caught = sieve.catches(g, {"kind": "unreachable", "capability": "the graph tree",
                               "modules": ("cairn.tools.tree.tree", "cairn.devices.librarian",
                                           "cairn.devices.db_domain"),
                               "start": "cairn/machines/build_inspector/inspector.py"})
    assert caught == [], f"the verdict path can reach the graph tree: {caught}"
    assert len(sieve.reaches(g, "cairn/machines/build_inspector/inspector.py")) > 5, (
        "the closure from the verdict path came back nearly empty — the tooth above "
        "would be green because nothing was walked, which is the failure it exists to catch")


def test_the_hollow_floor_guards_the_new_kind_too():
    """Falsifier clause (3) of the owning ticket, verbatim: the floor must be a property
    of catches(), not of the two kinds that predate the walk. It holds because the size
    is checked BEFORE the kind is dispatched."""
    small = {f"a/f{i}.py": set() for i in range(5)}
    small["cairn/fire/start.py"] = set()
    try:
        sieve.catches(small, _UNREACHABLE_RULE)
    except sieve.HollowScan as e:
        assert "did not read the tree" in str(e), f"the raise must say WHY: {e}"
    else:
        raise AssertionError("a reachability sieve over 6 files returned clean (Law 8)")


# ── PHASE: when a sieve can run ───────────────────────────────────────────────
# SUPERSEDES the proximity-based reach tests (2026-08-06 through 2026-08-11).
# The band axis changed from HOW FAR A SIEVE LOOKS to WHEN IT CAN RUN (Akien,
# 2026-08-12, ruled; confirmed 2026-08-21). The tell: WHAT THE SIEVE READS.
# A recording sieve takes the SUBJECT (band 1). A postprocessing sieve takes
# PRIOR STAMPS (band 2). Preprocessing produces subjects (band 0).

_PHASE_FIXTURE = """
def produces_subjects():
    return [{"name": "a"}, {"name": "b"}]

def scores_a_subject(row, comp_dir):
    return row["score"] > 0.5

def also_scores(view):
    return view.get("ok", False)

def picks_from_stamps(stamps, row):
    return min(stamps, key=lambda s: s["cost"])

def delegates_to_picker(row, comp_dir):
    return picks_from_stamps(get_stamps(), row)
"""


def test_phase_classifies_by_what_the_sieve_reads():
    p = sieve.phase_of(_PHASE_FIXTURE)
    assert p["produces_subjects"] == 0, f"no params should be preprocess: {p}"
    assert p["scores_a_subject"] == 1, f"takes subject should be record: {p}"
    assert p["also_scores"] == 1, f"takes subject should be record: {p}"
    assert p["picks_from_stamps"] == 2, f"takes stamps should be postprocess: {p}"


def test_phase_is_transitive_through_an_in_module_helper():
    """A function that calls a postprocess helper becomes postprocess."""
    p = sieve.phase_of(_PHASE_FIXTURE)
    assert p["delegates_to_picker"] == 2, (
        f"calls picks_from_stamps but did not inherit postprocess phase: {p}")


def test_phase_on_unparseable_source_is_empty():
    assert sieve.phase_of("this is not python %%%") == {}


def test_the_real_inspector_sieves_are_all_record():
    """All current inspector sieves take the subject — they are record sieves (band 1).
    No preprocess or postprocess sieves exist yet. When one arrives, this test grows
    to assert the separation."""
    src = (_REPO_ROOT / "cairn" / "machines" / "build_inspector" / "inspector.py").read_text()
    from cairn.machines.build_inspector.inspector import SIEVES
    wanted = {f.__name__ for f in SIEVES.values()}
    phases = {k: v for k, v in sieve.phase_of(src).items() if k in wanted}
    assert phases, "no SIEVES resolved to module-level functions — the walk missed them"
    assert all(v == 1 for v in phases.values()), (
        f"expected all record (1), got: {phases}")


def _main() -> int:
    checks = [
        test_a_parse_is_not_a_dial,
        test_listening_is_not_dialing,
        test_prose_is_not_an_import,
        test_an_in_tree_leaf_import_is_visible,
        test_an_unparseable_file_is_not_a_door,
        test_a_sieve_over_nothing_raises_rather_than_passing,
        test_the_real_corpus_clears_the_floor,
        test_sole_path_catches_a_second_door,
        test_sole_path_is_clean_on_the_real_corpus_for_both_domains,
        test_forbidden_catches_a_fork_breach_and_spares_everyone_else,
        test_an_unknown_sieve_kind_is_refused_not_silently_clean,
        test_importers_of_finds_the_live_carriers_of_a_primitive,
        test_importers_of_is_empty_for_a_module_nobody_imports,
        test_a_module_is_not_its_own_importer,
        test_module_name_folds_a_package_init,
        test_reaches_walks_past_the_first_hop_and_keeps_the_shortest_chain,
        test_reaches_refuses_a_start_it_never_read,
        test_an_import_of_nothing_is_a_dead_end_not_an_error,
        test_unreachable_catches_a_breach_two_hops_down,
        test_unreachable_spares_a_breacher_the_fire_path_cannot_reach,
        test_unreachable_catches_a_breach_at_the_start_itself,
        test_unreachable_is_clean_on_the_real_corpus,
        test_the_hollow_floor_guards_the_new_kind_too,
        test_phase_classifies_by_what_the_sieve_reads,
        test_phase_is_transitive_through_an_in_module_helper,
        test_phase_on_unparseable_source_is_empty,
        test_the_real_inspector_sieves_are_all_record,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print(f"green — import_sieve: {len(checks)} teeth; the mesh tells a capability from a "
          "mention, and a clean sieve from one that never ran")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

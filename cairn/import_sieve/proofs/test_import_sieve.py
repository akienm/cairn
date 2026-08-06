"""Proof for import_sieve — the mesh, and the floor under a clean result.

This component exists to turn five prose IOUs into physics, so the teeth that matter are
the ones a HOLLOW sieve passes: one that catches nothing catches nothing on a clean corpus
too, and reports the identical green. Every catching tooth here is therefore paired —
the same rule is shaken over a PLANTED graph (must catch) and over the real corpus (must
not) — because either half alone is satisfied by a sieve made of solid sheet metal.

The mesh teeth are the corpus's own two lessons, re-armed as permanent traps:

  - `urllib.parse.parse_qs` is string work; `urllib.request` is a door. A word-matching
    scan cannot tell them apart, and web_server/server.py is the live instance that would
    have gone red on day one.
  - `http.server` LISTENS. A dial rule that catches it reds the one component whose entire
    job is to be reachable.
  - a docstring naming psycopg2 is prose. learning_block learned this in miniature on
    2026-08-01 when its own honest docstring tripped its own tooth.

    python3 cairn/import_sieve/proofs/test_import_sieve.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.import_sieve import sieve

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
    g = _planted(**{"cairn/web_server/listener.py":
                    "from http.server import ThreadingHTTPServer"})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                               "modules": DIALS, "only": "cairn/inference_domain/"})
    assert caught == [], f"a listening server was caught by an outbound mesh: {caught}"


def test_prose_is_not_an_import():
    """A docstring naming the driver is a description of a door, not a door."""
    g = _planted(**{"a/doc.py": '"""We reach 5432 only via psycopg2, through db_domain."""\nimport json'})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "5432",
                               "modules": ("psycopg2",), "only": "cairn/db_domain/"})
    assert caught == [], f"prose about psycopg2 was caught as an import: {caught}"


def test_an_in_tree_leaf_import_is_visible():
    """`from cairn.build_inspector import inspector` must be catchable. Recording only the
    MODULE (what the hand-rolled scan did) makes every in-tree edge invisible at the leaf."""
    caught = sieve.imports_in("from cairn.build_inspector import inspector")
    assert "cairn.build_inspector" in caught, "the package must be recorded"
    assert "cairn.build_inspector.inspector" in caught, "the leaf must be recorded too"


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
                    "cairn/inference_domain/host.py": "import urllib.request"})
    caught = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                               "modules": DIALS, "only": "cairn/inference_domain/"})
    assert len(caught) == 1, f"exactly the rogue should be caught, got {caught}"
    assert "skills/rogue/probe.py" in caught[0] and "socket" in caught[0]
    assert "cairn/inference_domain/" in caught[0], "the refusal must name the door that IS allowed"


def test_sole_path_is_clean_on_the_real_corpus_for_both_domains():
    """The other half of the pair. Measured 2026-08-06: one dialer (inference_domain/host.py),
    one driver importer (db_domain/store.py). If this reds, a second door was built."""
    g = _corpus()
    host = sieve.catches(g, {"kind": "sole_path", "capability": "the inference host",
                             "modules": DIALS, "only": "cairn/inference_domain/"})
    assert host == [], f"a second door to the inference host: {host}"
    db = sieve.catches(g, {"kind": "sole_path", "capability": "port 5432",
                           "modules": ("psycopg2", "psycopg", "asyncpg", "pg8000", "sqlalchemy"),
                           "only": "cairn/db_domain/"})
    assert db == [], f"a second door to 5432: {db}"


# ── forbidden: the fork ──────────────────────────────────────────────────────


def test_forbidden_catches_a_fork_breach_and_spares_everyone_else():
    g = _planted(**{"cairn/diagnostic_inspector/inspector.py":
                    "from cairn.build_inspector import inspector",
                    "cairn/tester/device.py": "from cairn.build_inspector import inspector"})
    caught = sieve.catches(g, {"kind": "forbidden", "capability": "the shared inspection library",
                               "modules": ("cairn.build_inspector",),
                               "within": "cairn/diagnostic_inspector/"})
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
    """cairn/base/probe.py is the file two ruling packets sentenced to death while eight
    live modules imported it. That is the trouble this query closes."""
    g = _corpus()
    hits = sieve.importers_of(g, "cairn/base/probe.py")
    assert len(hits) >= 5, f"probe.py's importers should be many, got {hits}"
    assert any("shim.py" in h for h in hits), f"base/shim.py imports probe: {hits}"


def test_importers_of_is_empty_for_a_module_nobody_imports():
    g = _corpus()
    assert sieve.importers_of(g, "cairn/import_sieve/proofs/test_import_sieve.py") == [], \
        "a proof nobody imports must come back empty — that is what makes deletion safe"


def test_a_module_is_not_its_own_importer():
    g = {"a/b.py": {"a.b"}, **{f"f/{i}.py": set() for i in range(25)}}
    assert sieve.importers_of(g, "a/b.py") == [], "self-reference is not an importer"


def test_module_name_folds_a_package_init():
    assert sieve.module_name("cairn/base/probe.py") == "cairn.base.probe"
    assert sieve.module_name("cairn/base/__init__.py") == "cairn.base"


# ── REACH: the band a sieve has to look through ──────────────────────────────
# These teeth exist because the FIRST cut of this derivation was a coin-toss red:
# it matched call-name tails and put 15 of build_inspector's 18 checks off-box,
# since Path.resolve() and inference_domain.resolve() share a tail. That failure is
# tooth `test_a_path_resolve_is_not_a_host_resolve` and it is the one that must never
# go quiet.

_REACH_FIXTURE = """
import subprocess
from pathlib import Path
from cairn.inference_domain import resolve

def arithmetic_only(row):
    return row["a"] + row["b"]

def reads_one_file(p):
    return Path(p).read_text()

def walks_a_tree(root):
    return sorted(Path(root).rglob("*.json"))

def asks_the_host(q):
    return resolve(q)

def shells_out(cmd):
    return subprocess.run(cmd, capture_output=True)

def path_resolve_is_local(p):
    return Path(p).resolve()

def calls_a_walker(root):
    return walks_a_tree(root)
"""


def test_reach_bands_a_body_by_how_far_it_looks():
    r = sieve.reach_of(_REACH_FIXTURE)
    assert r["arithmetic_only"] == 0, r
    assert r["reads_one_file"] == 1, r
    assert r["walks_a_tree"] == 2, r
    assert r["shells_out"] == 2, r
    assert r["asks_the_host"] == 3, r


def test_a_path_resolve_is_not_a_host_resolve():
    """The v1 failure, armed permanently.

    `Path(p).resolve()` and `inference_domain.resolve(q)` are spelled the same at the
    tail. A derivation that reads names instead of bindings calls the first one off-box
    and the whole nest inverts — the cheap local check sinks to the bottom and the
    expensive one floats. Both directions are pinned, because a tooth that only checks
    the local half is satisfied by a derivation that bands NOTHING off-box.
    """
    r = sieve.reach_of(_REACH_FIXTURE)
    assert r["path_resolve_is_local"] == 0, (
        "Path.resolve() was read as leaving the box — reach is matching call-name "
        f"tails again, not import bindings: {r}")
    assert r["asks_the_host"] == 3, (
        "the imported resolve() stopped counting as off-box, so the tooth above passes "
        f"for the wrong reason: {r}")


def test_reach_is_transitive_through_an_in_module_helper():
    """A check that calls a helper reaches whatever the helper reaches — its answer
    depends on it. Without this, every real sieve reads as band 0, because real sieves
    delegate."""
    r = sieve.reach_of(_REACH_FIXTURE)
    assert r["calls_a_walker"] == 2, r


def test_an_empty_ladder_cannot_band_anything():
    """NON-VACUITY. An accept-everything ladder must collapse every band to 0 — if this
    fixture still bands with no rules, the bands are coming from somewhere other than the
    ladder and the ladder is decoration."""
    r = sieve.reach_of(_REACH_FIXTURE, ladder={})
    assert set(r.values()) == {0}, r


def test_a_nest_is_coarsest_first_and_omits_empty_bands():
    n = sieve.nest({"a": 2, "b": 0, "c": 2, "d": 3})
    assert [band for band, _ in n] == [0, 2, 3], n
    assert n[1] == (2, ["a", "c"]), "within a band the order is sorted, never invented"


def test_the_real_inspector_separates_into_bands():
    """Measured over the live corpus, 2026-08-06: the eighteen checks separate into
    THREE populated bands. Asserted as an INVARIANT, not a snapshot — the counts move as
    checks are added, and pinning them would turn every new sieve into a spurious red.
    What must hold is that reach DISCRIMINATES: if every check lands in one band the
    derivation has stopped telling them apart, which is the failure this replaces."""
    src = (_REPO_ROOT / "cairn" / "build_inspector" / "inspector.py").read_text()
    from cairn.build_inspector.inspector import FILTERS
    wanted = {f.__name__ for f in FILTERS.values()}
    bands = {k: v for k, v in sieve.reach_of(src).items() if k in wanted}
    assert bands, "no FILTERS resolved to module-level functions — the walk missed them"
    assert len(set(bands.values())) >= 2, (
        f"every check banded identically ({bands}) — reach is no longer discriminating")
    assert bands["charter_on_disk"] < bands["charted_refs_resolve"], (
        "the cheapest precondition check did not sort above a chart-packet judge, so "
        f"the nest would run them in the wrong order: {bands}")


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
        test_reach_bands_a_body_by_how_far_it_looks,
        test_a_path_resolve_is_not_a_host_resolve,
        test_reach_is_transitive_through_an_in_module_helper,
        test_an_empty_ladder_cannot_band_anything,
        test_a_nest_is_coarsest_first_and_omits_empty_bands,
        test_the_real_inspector_separates_into_bands,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print(f"green — import_sieve: {len(checks)} teeth; the mesh tells a capability from a "
          "mention, and a clean sieve from one that never ran")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

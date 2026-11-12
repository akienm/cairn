"""Teeth for ticket 336a781018ba — a probe's enough threshold declares what set it.

MEASURED 2026-11-12, at the build: 105 probe modules, 103 carrying ``enough=``, and not one
of them able to say which ticket or observation set the number inside it (69 ``_ENOUGH*``
constants across 58 files; 55 across 47 at the cast). The build gives the number a declared
shape (``Threshold(value, of, set_by)`` on the frozen ``Probe``), counts the silent ones from
source (``cairn.tools.base.threshold_census``), reds them per component (build_inspector's
``probe_thresholds_declare_provenance``), declares every one, and arms a WATCHME probe that
the count HOLDS at zero while the corpus grows.

ONE COMPOSITE TOOTH, because the falsifier is unnumbered (``proof_coverage.clauses`` reads
``['all']``); its parts are the helpers below, in D19's order. Everything the build ADDED is
bound at call time, never at import, so the hollow reading reds a tooth instead of crashing
the module.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "336a781018ba": {"all": "test_the_declaration_the_census_the_sieve_and_the_watch"},
}

_HEAD = "from cairn.tools.base.probe import Probe, Threshold\n_ENOUGH = 3\n"
_TAIL = "\n"


def _probe_src(extra: str) -> str:
    return (_HEAD + "PROBE = Probe(why='w', trigger=lambda now, c: True, to='x'"
            + extra + ")" + _TAIL)


_PLANTED = {
    "silent": ", enough=lambda c: True",
    "declared": ", enough=lambda c: True, thresholds=(Threshold(_ENOUGH, 'runs', "
                "set_by='ticket f1x7a4c4038a names the number'),)",
    "blank_set_by": ", enough=lambda c: True, thresholds=(Threshold(_ENOUGH, 'runs', set_by=''),)",
    "blank_of": ", enough=lambda c: True, thresholds=(Threshold(_ENOUGH, '', set_by='x'),)",
    "no_enough": "",
    "enough_none": ", enough=None",
}


def _plant(root: Path, names: dict, folder: str = "probes") -> Path:
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    for name, extra in names.items():
        (d / f"{name}.py").write_text(_probe_src(extra))
    return d


def _planted_component() -> Path:
    comp = scratch_dir("cairn-threshold-") / "comp"
    d = _plant(comp, _PLANTED)
    (d / "broken.py").write_text("PROBE = Probe(why='w', enough=lambda c: True,\n")
    _plant(comp, {"dormant": ", enough=lambda c: True"}, folder="probes_disabled")
    # A proof's planted probe is outside the census: proofs/ is never read.
    _plant(comp / "proofs", {"fixture_silent": ", enough=lambda c: True"})
    return comp


def _the_declaration_refuses_a_blank():
    from cairn.tools.base.probe import Probe, Threshold
    for args, exc in (((5, "", "x"), ValueError), ((5, "runs", ""), ValueError),
                      ((lambda: 5, "runs", "x"), TypeError)):
        try:
            Threshold(args[0], args[1], set_by=args[2])
        except exc:
            continue
        raise AssertionError(f"Threshold{args} constructed; {exc.__name__} expected")
    t = Threshold(5, "runs", set_by="ticket x")
    assert (t.value, t.of, t.set_by) == (5, "runs", "ticket x"), t
    try:
        Probe(why="w", trigger=lambda now, c: True, to="x", thresholds=[t])
    except TypeError:
        pass
    else:
        raise AssertionError("a list of thresholds constructed; a tuple of Threshold is the shape")
    p = Probe(why="w", trigger=lambda now, c: True, to="x", enough=lambda c: True, thresholds=())
    assert p.thresholds == (), "D2: an enough with no thresholds constructs; the sieve counts it"
    p = Probe(why="w", trigger=lambda now, c: True, to="x", thresholds=(t,))
    assert p.thresholds == (t,), p.thresholds


def _the_census_finds_the_silent_and_only_them(comp: Path):
    from cairn.tools.base import threshold_census
    c = threshold_census.census(comp)
    assert c["total"] == 7, ("seven live probes planted", c["total"], [r["path"] for r in c["probes"]])
    assert c["with_enough"] == 4, c["with_enough"]
    assert sorted(Path(p).stem for p in c["provenance_less_paths"]) == \
        ["blank_of", "blank_set_by", "broken", "silent"], c["provenance_less_paths"]
    assert c["provenance_less"] == 4, c
    assert (c["disabled_total"], c["disabled_provenance_less"]) == (1, 1), c
    broken = next(r for r in c["probes"] if r["path"].endswith("broken.py"))
    assert broken["error"], ("a module that does not parse carries its error (Law 7)", broken)
    assert not any("proofs/" in r["path"] for r in c["probes"]), "proofs/ is outside the census"


def _the_sieve_reds_the_silent_and_passes_the_declared(comp: Path):
    from cairn.machines.build_inspector import inspector
    assert "probe_thresholds_declare_provenance" in inspector.SIEVES
    sieve = inspector.SIEVES["probe_thresholds_declare_provenance"]
    f = sieve({"component": "comp"}, comp)
    bands = sorted(x["values"]["band"] for x in f)
    assert len(f) == 5 and bands == ["disabled", "live", "live", "live", "live"], \
        [(x["about"], x["values"].get("band")) for x in f]
    clean = scratch_dir("cairn-threshold-clean-") / "comp"
    _plant(clean, {k: v for k, v in _PLANTED.items() if k in ("declared", "no_enough", "enough_none")})
    assert sieve({"component": "clean"}, clean) == [], "a declared component reads clean"


def _the_live_corpus_reads_zero():
    from cairn.tools.base import threshold_census
    c = threshold_census.census(_REPO_ROOT)
    assert c["total"] > 0 and c["with_enough"] > 0, ("an empty census is a red, not a green", c["total"])
    assert c["provenance_less"] == 0, ("live probes silent about their number", c["provenance_less_paths"])
    assert c["disabled_provenance_less"] == 0, c["disabled_provenance_less_paths"]


def _the_watch_clears_only_on_a_held_window():
    import importlib
    mod = importlib.import_module("cairn.tools.base.probes.a_threshold_without_provenance_is_refusable")
    from cairn.tools.base.probe import Probe, Threshold
    assert isinstance(mod.PROBE, Probe) and mod.PROBE.carry and mod.PROBE.enough
    assert all(isinstance(t, Threshold) and t.set_by for t in mod.PROBE.thresholds) \
        and mod.PROBE.thresholds, "the WATCHME probe declares its own numbers"
    tmp = scratch_dir("cairn-threshold-watch-")
    roots = {"repo": tmp / "repo", "commons": tmp / "commons", "instance": tmp / "instance"}
    tree = tmp / "tree"
    _plant(tree, {"a": _PLANTED["silent"], "b": _PLANTED["declared"]})
    declared = _PLANTED["declared"]
    seen = []
    for pulse in range(1, 8):
        if pulse == 2:
            _plant(tree, {"a": declared})
        if pulse in (4, 6):
            _plant(tree, {f"born_{pulse}": declared})
        ctx = {"roots": roots, "repo_root": tree}
        mod.PROBE.fires(None, ctx)
        seen.append(mod.PROBE.gathered_enough(ctx))
    assert seen == [False] * 6 + [True], ("enough only on the seventh pulse", seen)
    runs = mod.read_runs(roots)
    assert len(runs) == 7, ("one line per pulse, not per question", len(runs))
    assert runs[0]["provenance_less"] == 1 and runs[0]["silent"], runs[0]
    assert runs[-1]["total"] - runs[1]["total"] == 2, [r["total"] for r in runs]
    assert str(mod.runs_path(roots)).startswith(str(roots["instance"])), "never the live instance"
    for k in ("at", "provenance_less", "total", "with_enough", "added_since_last", "silent",
              "disabled_total", "disabled_provenance_less", "disabled_silent"):
        assert k in runs[-1], (k, runs[-1])


def test_the_declaration_the_census_the_sieve_and_the_watch():
    """The number is declared (a blank is refused, a list is refused, a bare enough still
    constructs); the census finds exactly the silent probes in a planted tree, banding the
    disabled one beside the live; the sieve reds each silent probe and passes a declared
    component; the live corpus reads zero in both bands; and the WATCHME probe clears only on
    the seventh pulse, when six lines read zero and the corpus grew by two."""
    _the_declaration_refuses_a_blank()
    comp = _planted_component()
    _the_census_finds_the_silent_and_only_them(comp)
    _the_sieve_reds_the_silent_and_passes_the_declared(comp)
    _the_live_corpus_reads_zero()
    _the_watch_clears_only_on_a_held_window()


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))

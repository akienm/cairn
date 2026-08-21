"""Proof for the nest primitive — bands, coarsest-first assembly, the one-shake.

Teeth a hollow lift could not pass:
  - THE TOY SECOND TENANT (the load-bearing row, ticket banding-berths-at-the-
    general-level): a tenant that is not build_inspector assembles and shakes a nest
    with its OWN firing convention, and this file's only cairn import is
    cairn.tools.base.nest. If the "general" berth needed tenant internals — the census, the
    sieve registry, the reach ladder — the lift was a relabel, and this row is where
    that fails first.
  - THE ASSEMBLY IS COARSEST-FIRST AND OMITS EMPTY BANDS (migrated here from
    import_sieve's proofs 2026-08-07, because the proof berths beside the code it
    proves).
  - SCORES ARE BINARY AND THE ROLL-UP IS min(), NEVER A MEAN — one zero sinks the
    subject; a pile of passes cannot buy past a catch; absence is not a third value.

Runnable bare (no DB, no framework):
    python3 cairn/tools/base/proofs/test_nest.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.nest import BAND_NAMES, nest, shake


def test_a_nest_is_coarsest_first_and_omits_empty_bands():
    n = nest({"a": 2, "b": 0, "c": 2, "d": 3})
    assert [band for band, _ in n] == [0, 2, 3], n
    assert n[1] == (2, ["a", "c"]), "within a band the order is sorted, never invented"


def test_band_names_are_phases_and_extensible():
    assert BAND_NAMES == {0: "preprocess", 1: "record", 2: "postprocess"}
    widened = {**BAND_NAMES, 3: "cleanup"}
    n = nest({"late": 3, "early": 0})
    assert [widened[b] for b, _ in n] == ["preprocess", "cleanup"], (
        "a band outside the shipped vocabulary must assemble fine — the names are "
        "data, not a gate")


def test_a_toy_second_tenant_shakes_importing_only_the_general_berth():
    """THE LOAD-BEARING ROW. The tenant below shares nothing with build_inspector:
    its sieves take a single string subject (not (row, comp_dir)), its registry is a
    local dict, its reaches are hand-derived. If shake() runs it to a full gradation,
    assembly-and-shake is general; everything tenant-specific stayed with the tenant."""
    fired: list[str] = []

    def no_vowels(subject: str) -> list:
        return [f"vowel in {subject}"] if any(v in subject for v in "aeiou") else []

    def short_enough(subject: str) -> list:
        return [] if len(subject) <= 5 else [f"{subject} is long"]

    tenant_sieves = {"no_vowels": no_vowels, "short_enough": short_enough}
    tenant_reaches = {"no_vowels": 0, "short_enough": 2}   # derived by the tenant's own rule

    def fire(name: str, subject: object) -> list:
        fired.append(name)
        return tenant_sieves[name](subject)                 # the tenant's own convention

    out = shake(nest(tenant_reaches), {"xyz": "xyz", "audacious": "audacious"}, fire)

    # Coarse first, once per subject — the shake's only ordering, observed not asserted.
    assert fired == ["no_vowels", "short_enough"] * 2, fired
    # The gradation covers every sieve for every subject; scores drawn from {0.0, 1.0}.
    assert set(out["gradation"]) == {"xyz", "audacious"}
    for scores in out["gradation"].values():
        assert set(scores) == set(tenant_sieves), scores
        assert set(scores.values()) <= {0.0, 1.0}, scores
    assert out["gradation"]["xyz"] == {"no_vowels": 1.0, "short_enough": 1.0}
    assert out["gradation"]["audacious"] == {"no_vowels": 0.0, "short_enough": 0.0}
    assert out["roll_up"] == {"xyz": 1.0, "audacious": 0.0}
    assert out["findings"] == ["vowel in audacious", "audacious is long"]


def test_scores_are_binary_and_the_rollup_is_min_never_mean():
    # Nineteen passes cannot buy past one catch — min(), deliberately not a mean.
    many = {f"s{i}": (lambda s: []) for i in range(19)}
    many["catches"] = lambda s: ["caught"]
    reaches = {name: 0 for name in many}
    out = shake(nest(reaches), {"comp": "comp"},
                lambda name, subject: many[name](subject))
    assert out["roll_up"]["comp"] == 0.0, (
        "a pile of passes bought past a real catch — the roll-up went mean-shaped")
    # An empty shake caught nothing: 1.0, not a red, not a third value.
    out = shake([], {"comp": "comp"}, lambda name, subject: [])
    assert out["gradation"]["comp"] == {} and out["roll_up"]["comp"] == 1.0


def _main() -> int:
    for check in (test_a_nest_is_coarsest_first_and_omits_empty_bands,
                  test_band_names_are_phases_and_extensible,
                  test_a_toy_second_tenant_shakes_importing_only_the_general_berth,
                  test_scores_are_binary_and_the_rollup_is_min_never_mean):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — nest: the assembly is coarsest-first with empty bands omitted, the "
          "band names ride as data, a toy second tenant shakes on its own convention "
          "importing ONLY cairn.tools.base.nest, and the roll-up is min() — one zero sinks "
          "the subject")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

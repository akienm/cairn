"""nest — bands, the coarsest-first assembly, and the one-shake. Block-general.

THE BANDS ARE PHASES (Akien, 2026-08-12, ruled; confirmed 2026-08-21: "BANDING IS
PREPROCESS, MEASURE AND POSTPROCESS"): preprocess, record, postprocess. His words:
"each question is a seive. and because we might have seives that come after others
(which is min, which is max) this is the kind of bands that we replace our previous
ideas with: preprocessing, recording, postprocessing. and the which is smallest is
simply a post processing seive." So the band axis is WHEN IT CAN RUN, not how far
it reaches. The proximity ladder (in-hand/local-disk/correlated-local/off-box) is
superseded — those distinctions remain true about what they described and are no
longer the spec (ticket the-questions-are-the-sieve, distinction 50).

THE GENERAL CASE, BY RULING (2026-08-07-the-nest-is-block-general): "nest/banding
is the general case." Nest, gradation and bands are a block-general primitive any
inspector or block carries — build_inspector is the first tenant, not the owner.
A tenant derives its phases however its domain demands, then assembles and shakes
them HERE. Derivation is tenant-specific; assembly and shake are general.

A BAND SEQUENCES; IT NEVER FORBIDS (Akien, 2026-08-06). An empty band is empty,
not closed. And the names are DATA a tenant may extend, not a closed taxonomy —
the integers order the shake; the words are for the reader of the report.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping

BAND_NAMES = {0: "preprocess", 1: "record", 2: "postprocess"}


def nest(reaches: dict[str, int]) -> list[tuple[int, list[str]]]:
    """The reaches, assembled coarsest-first: [(band, [names]), ...].

    A nest is coarse mesh on top and is shaken ONCE — the word forbids firing one
    sieve, reading it, and re-firing, before any proof looks at it. Within a band the
    order genuinely does not matter, which is what lets a band be shaken at once;
    ONLY the bands are ordered, and nothing here invents an order inside one.

    Empty bands are omitted rather than reported as empty groups: the assembly is what
    exists, and a band with no sieves in it is not a step in the shake.
    """
    grouped: dict[int, list[str]] = {}
    for name, band in reaches.items():
        grouped.setdefault(band, []).append(name)
    return [(b, sorted(grouped[b])) for b in sorted(grouped)]


def shake(assembled: Iterable[tuple[int, list[str]]],
          subjects: Mapping[str, object],
          fire: Callable[[str, object], list]) -> dict:
    """One shake of an assembled nest over the subjects. The general half of inspect.

    The tenant brings its OWN firing convention as ``fire(sieve_name, subject) ->
    findings`` — what a sieve is, what a subject is, and how one meets the other is
    tenant domain (build_inspector fires ``SIEVES[name](row, comp_dir)``; a second
    tenant may fire anything). The general side owns what the ruling generalized:
    the coarse-first ordering, the GRADATION — a score per sieve per subject rather
    than a pass/fail — and the min() roll-up.

    Scores are drawn from exactly {0.0, 1.0}: the sieve caught, or it did not. A
    sieve that did not run at all is ABSENT from a subject's row rather than scored
    — Akien refused a third value, and absence is what carries 'not applicable'
    without inventing one. Here that means every sieve in the assembly fires for
    every subject; absence enters only when the tenant's assembly omits a sieve.

    The roll-up is min() — one zero sinks the subject — and it is deliberately NOT
    a mean: averaging would let a subject buy its way past a real catch with a pile
    of passes, which is the whole reason the score is relative to the requirement
    rather than to the other sieves. A subject with no sieves rolls up 1.0: an
    empty shake caught nothing, and inventing a red for it would be a third value
    by another door.
    """
    findings: list = []
    gradation: dict[str, dict[str, float]] = {}
    for subject_name, subject in subjects.items():
        scores: dict[str, float] = {}
        for _band, names in assembled:      # coarse first — the shake's only ordering
            for name in names:
                caught = fire(name, subject)
                findings.extend(caught)
                scores[name] = 0.0 if caught else 1.0
        gradation[subject_name] = scores
    return {
        "findings": findings,
        "gradation": gradation,
        "roll_up": {s: (min(v.values()) if v else 1.0) for s, v in gradation.items()},
    }

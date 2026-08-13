"""nest — bands, the coarsest-first assembly, and the one-shake. Block-general.

READ THIS FIRST — BANDS ARE SCAFFOLDING, NOT THE SPEC (Akien, 2026-08-11, ruling
2026-08-11-a-sieve-is-one-true-false-rule). THE DEFINITION IS: "a seive is something
that evaluates to true based on whatever it's inspecting. it's specific to the device
being inspected and provides a true false ruling." That is the whole of it — no bands,
no ladder, no ordering are part of what a sieve IS.

BANDS WERE CC'S IDEA: "we added bands and ordering because you thought you needed it.
I DONT." They stay only because he said so in the same breath — "i do not think the
existing stuff needs to go" — which is LEAVE TO REMAIN, not endorsement, and it does
not extend to growing them (the ticket to make a band into stored data was killed).

WHY THIS PARAGRAPH EXISTS AT ALL. Everything below cites rulings of 2026-08-06 and
2026-08-07 and attributes lines to Akien by name. Those citations are REAL — he did
rule on this structure. But he ruled on an object CC put in front of him, and for four
days every later reader (CC) treated those rulings as evidence of what he WANTED. A
ruling on someone's invention does not make it theirs. If you are about to build on
what follows, the question is not "is this ruling current" but "whose idea was this
originally" — and the answer here is CC's.

THE GENERAL CASE, BY RULING (2026-08-07-the-nest-is-block-general): "nest/banding
is the general case." Nest, gradation and bands are a block-general primitive any
inspector or block carries — build_inspector is the first tenant, not the owner,
and this berth is where a consumer can read the gradation without importing a
tenant. Berthed beside probe.py by the same precedent: block-general machinery
lives in cairn.tools.base under base's charter, and grows a component of its own only
when a real need arrives that base cannot serve.

WHAT MOVED AND WHAT DID NOT. The band vocabulary and the assembly moved here from
import_sieve (2026-08-07, ticket banding-berths-at-the-general-level); the shake
moved here from inside build_inspector.inspect()'s loop. Band DERIVATION did not
move: reach_of and the ladder stay in import_sieve, because how far an import
looks is that component's own domain. A tenant derives its reaches however its
domain demands, then assembles and shakes them HERE. Derivation is tenant-
specific; assembly and shake are general — that distinction is the whole lift.

THE BOUNDARIES ARE WHERE THE FAILURE MODE CHANGES, not where the milliseconds do
(Akien, 2026-08-06 — reasoning about answer-proximity, which is why it survives
the move out of the import domain). In-hand cannot fail environmentally. Local
disk fails on absence. Correlated local work fails on inconsistency. Off-box
fails on UNAVAILABILITY, which nothing above it can do — and that last boundary
is the one that earns its keep, because an unreachable host must never mask a
local finding.

A BAND SEQUENCES; IT NEVER FORBIDS (Akien, 2026-08-06). An empty band is empty,
not closed. And the names are DATA a tenant may extend, not a closed taxonomy —
the integers order the shake; the words are for the reader of the report.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping

BAND_NAMES = {0: "in-hand", 1: "local-disk", 2: "correlated-local", 3: "off-box"}


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

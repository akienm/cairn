"""nest — the shared machine of sieves (outline 16.2): bands, the coarsest-first assembly, the shake.

THE BANDS ARE PHASES (Akien, 2026-08-12, ruled; confirmed 2026-08-21: "BANDING IS
PREPROCESS, MEASURE AND POSTPROCESS"; outline 16.2.3.1: "Bands are phases: preprocess,
measure, postprocess"): preprocess, measure, postprocess. His words: "each question is a
seive. and because we might have seives that come after others (which is min, which is
max) this is the kind of bands that we replace our previous ideas with: preprocessing,
recording, postprocessing. and the which is smallest is simply a post processing seive."
So the band axis is WHEN IT CAN RUN, not how far it reaches.

ITS OWN MACHINE (outline 16.2, Q#46; ticket 71cd4a62e8c5): its users are build_inspector
(9.4.3) and the inference proxy's route (11.4.6), so it berths at cairn/machines/nest/,
not inside the base tool where it lived from 2026-08-07 to 2026-11-10. A tenant derives
its phases (import_sieve.phase_of reads what each sieve takes), then assembles and shakes
them HERE. Derivation is tenant-specific; assembly and shake are general.

THE SHAKE RANKS, IT DOES NOT ONLY CUT (Akien 2026-09-29, open-8ecde12362d6, option c): a
postprocess sieve gets the stamps of every subject and stamps each survivor with a RANK,
and the shake hands back the survivors in rank order — so a compare over all the inputs
(the cheapest survivor first) runs inside the nest. A rank is a postprocess stamp, never
a cut score: it changes neither the gradation nor the roll-up.

A BAND SEQUENCES; IT NEVER FORBIDS (Akien, 2026-08-06). An empty band is empty, not
closed. And the names are DATA a tenant may extend, not a closed taxonomy — the integers
order the shake; the words are for the reader of the report. A band other than 0 and 2
shakes as a measure band.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping

BAND_NAMES = {0: "preprocess", 1: "measure", 2: "postprocess"}
PREPROCESS, POSTPROCESS = 0, 2


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
          fire: Callable[..., object]) -> dict:
    """One shake of an assembled nest over the subjects, band-outer. The general half of inspect.

    The tenant brings its OWN firing convention as ``fire``; what a sieve is, what a subject
    is, and how one meets the other is tenant domain. The bands run in assembled order, each
    over every subject before the next band starts:

    - PREPROCESS (band 0): ``fire(name, subjects)`` once, with the whole subject set; it
      returns the subject names to go on scoring. A subject it leaves out gets no score from
      any later sieve (absent, never a third value) and so rolls up 1.0.
    - MEASURE (band 1, and any band but 0 and 2): ``fire(name, subject) -> findings`` per
      subject, subject-outer within the band. Scores are drawn from exactly {0.0, 1.0}: the
      sieve caught, or it did not.
    - POSTPROCESS (band 2): after the bands before it have fired over every subject,
      ``fire(name, subject, stamps)`` for each subject then rolling up 1.0, ``stamps`` being
      the gradation across every subject. Its return is any comparable value, kept as
      ``ranks[subject][name]`` — a stamp, never a cut score.

    The roll-up is min() — one zero sinks the subject — and deliberately NOT a mean:
    averaging would let a subject buy its way past a real catch with a pile of passes. A
    subject with no scores rolls up 1.0: an empty shake caught nothing.

    Returns findings, gradation, roll_up, ranks ({survivor: {sieve: rank}}) and order: the
    subjects rolling up 1.0, sorted by the tuple of their ranks in the assembled order of the
    postprocess sieves, ties by subject name.
    """
    findings: list = []
    gradation: dict[str, dict[str, float]] = {s: {} for s in subjects}
    live = list(subjects)
    ranks: dict[str, dict[str, object]] = {}
    post_names: list[str] = []

    def roll_up() -> dict[str, float]:
        return {s: (min(v.values()) if v else 1.0) for s, v in gradation.items()}

    for band, names in assembled:           # coarse first — the shake's only ordering
        if band == PREPROCESS:
            for name in names:
                keep = set(fire(name, {s: subjects[s] for s in live}))
                live = [s for s in live if s in keep]
        elif band == POSTPROCESS:
            post_names.extend(names)
            up = roll_up()
            for s in subjects:
                if up[s] != 1.0:
                    continue
                for name in names:
                    ranks.setdefault(s, {})[name] = fire(name, subjects[s], gradation)
        else:
            for s in live:
                for name in names:
                    caught = fire(name, subjects[s])
                    findings.extend(caught)
                    gradation[s][name] = 0.0 if caught else 1.0
    up = roll_up()
    survivors = [s for s in subjects if up[s] == 1.0]
    order = sorted(survivors, key=lambda s: (tuple(ranks.get(s, {}).get(n) for n in post_names), s))
    return {"findings": findings, "gradation": gradation, "roll_up": up,
            "ranks": {s: ranks[s] for s in survivors if s in ranks}, "order": order}

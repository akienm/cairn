"""WATCHME probe: declared_cadence_discriminates.

The ticket (a4c2be029f49) claims that a recorder's DECLARED reading cadence separates
the read from the unread in the field — that ``last_read`` against
``expected_read_frequency_seconds`` is a number that discriminates, not a field that
everybody leaves null. Until the population shows it, the intention is a hypothesis
(Law 3). The at-rest probe beside this one raises the reds; this one watches whether
the declaration is ever anything BUT red.

TRIGGER: each beat takes the population census — how many recorders stand, how many
carry a non-null ``last_read``, how many distinct declared frequencies — and fires the
first beat any recorder has been read at all (the first evidence a declared cadence
is being met by a reader). ENOUGH once three or more recorders carry a non-null
``last_read`` under two or more distinct frequencies: the declaration then measurably
discriminates across holders, and the watch retires. CARRIER: the counts, in the form
a verdict artifact against the ticket's falsifier reads.

Reads only; raises nothing. ``roots=`` is the proof's isolation seam.
"""
from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.probe import Probe, once
from cairn.tools.data_recorder.probes.reading_is_declared_and_current import _recorders

TICKET = "a4c2be029f49"
ENOUGH_READ = 3
ENOUGH_FREQUENCIES = 2


def population(*, roots=None) -> dict:
    recs = _recorders(roots)
    read = [r for r in recs if (r["reading"] or {}).get("last_read")]
    frequencies = sorted({(r["reading"] or {}).get("expected_read_frequency_seconds")
                          for r in recs
                          if (r["reading"] or {}).get("expected_read_frequency_seconds")
                          is not None})
    return {
        "recorders": len(recs),
        "declared": sum(1 for r in recs
                        if (r["reading"] or {}).get("expected_read_frequency_seconds")
                        is not None),
        "read": len(read),
        "read_names": sorted("%s-%s-%s" % (r["device"], r["instance"], r["name"])
                             for r in read),
        "frequencies": frequencies,
    }


def discriminates(pop: dict) -> bool:
    return pop["read"] >= ENOUGH_READ and len(pop["frequencies"]) >= ENOUGH_FREQUENCIES


def _trigger(now, context: dict) -> bool:
    pop = once(context, "recorder_population", lambda: population())
    return pop["read"] >= 1


def _carry(context: dict) -> dict:
    pop = once(context, "recorder_population", lambda: population())
    return {
        "ticket": TICKET,
        "at": datetime.now(timezone.utc).isoformat(),
        "population": pop,
        "discriminates": discriminates(pop),
        "finding": (
            "%d of %d recorders read (%d declared) under %d distinct frequency(ies) %s — "
            "the declared cadence %s"
            % (pop["read"], pop["recorders"], pop["declared"], len(pop["frequencies"]),
               pop["frequencies"],
               "discriminates read from unread across holders"
               if discriminates(pop) else
               "is being met by at least one reader; not yet across holders")),
    }


def _enough(context: dict) -> bool:
    pop = once(context, "recorder_population", lambda: population())
    return discriminates(pop)


PROBE = Probe(
    why="the ticket's falsifier: a declared reading cadence that nobody ever meets is a "
        "field, not a measurement. This watches the live population for the first read "
        "recorder and retires once three are read under two distinct frequencies — the "
        "point at which the declaration measurably discriminates.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy", "ticket": TICKET},
    carry=_carry,
    enough=_enough,
    horizon=2000,
)

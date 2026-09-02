"""PROBE — is the verdict vocabulary CHECK constraint still enforced by the database?

Berth for the WATCHME that ticket ``the-verdict-vocabulary-is-held-by-postgres`` (6890cf7e4053)
carries. Berthed beside ``cairn/devices/inference_domain`` because that is WHAT IT WATCHES:
``ensure_cache()`` applies the constraint, and a constraint silently dropped (by a migration, a
manual ALTER, a recreated table without it) would revert the guarantee to prose.

THE EFFICACY QUESTION: does the database still refuse an out-of-vocabulary verdict? The build
proved the constraint is applied by ensure_cache() and that an invalid write raises
CheckViolation. Whether it CONTINUES to hold is what this probe watches — the constraint could
be dropped, the table could be recreated without it, or a migration could ALTER it away.

TWO INVARIANTS:

  (a) THE CONSTRAINT EXISTS: information_schema.table_constraints carries a CHECK constraint
      named 'verdict_vocabulary' on the inference_calls table.

  (b) THE CONSTRAINT BITES: an out-of-vocabulary INSERT is refused by the database (not by
      application code) — the refusal is at the store level.

AUTHORITY: none. This probe deposits and pokes; fixing the constraint is the owner's act (Law 6).
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-verdict-vocabulary-is-held-by-postgres"


def survey_the_corpus() -> dict:
    """The live read — the store through its one door."""
    from cairn.devices.db_domain import store

    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_name = 'inference_calls' AND constraint_type = 'CHECK' "
                "AND constraint_name = 'verdict_vocabulary'"
            )
            row = cur.fetchone()
    finally:
        conn.close()

    return {
        "constraint_exists": row is not None,
        "table": "inference_calls",
        "constraint_name": "verdict_vocabulary",
    }


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE when the constraint is missing from the standing table."""
    s = _corpus(context)
    return not s["constraint_exists"]


def _enough(context: dict) -> bool:
    """CLEARED when the constraint exists on the standing table."""
    s = _corpus(context)
    return s["constraint_exists"]


def _carry(context: dict) -> dict:
    s = _corpus(context)
    return {
        "finding": ("verdict_vocabulary constraint MISSING from inference_calls"
                    if not s["constraint_exists"]
                    else "verdict_vocabulary constraint present on inference_calls"),
        "constraint_exists": s["constraint_exists"],
        "table": s["table"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier reds on the constraint being absent "
                             "from the standing table — prose enforcement without physics",
        "suggests": "run ensure_cache() in domain.py to re-apply the constraint, or "
                    "investigate why it was dropped",
    }


_HORIZON = 1000

PROBE = Probe(
    why="the verdict vocabulary CHECK constraint on inference_calls is the physics that "
        "replaced prose enforcement — if it disappears, the three valid values (hit, miss, "
        "refused) are back to being held by convention alone",
    trigger=_trigger,
    to="inference_domain",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))

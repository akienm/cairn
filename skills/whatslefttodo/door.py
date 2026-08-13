"""THE /whatslefttodo JUDGE — a gather stops being a report and becomes a measurement.

/whatslefttodo is tenant #5 of the ``cairn.machines.skill_block`` seam (after /intent, /sorted,
/saveslate and /idea). Until this module it was the one skill in the roster that fired
no door and named no other store holding its firings — the dial said so plainly:
"declares neither an input_contract nor a counted_by … This is NOT zero uses: it is no
measurement." Akien put it at the top of the sail batch on 2026-08-12.

**WHAT THIS DOOR OWNS THAT THE FLAT CONTRACT CANNOT: IT RE-READS THE WORLD.** The
skill's charter carried a tracked debt in exactly two halves — "nothing detects a
/whatslefttodo that skipped a gather **or reported a stale count**" — and the flat
contract closes only the first. Presence of a ``rulings`` field proves somebody typed
something; it says nothing about whether the number came from the instrument or from
the session-open banner, which may be hours old. So this judge runs the SAME readers
the gather is supposed to run, at the instant of firing, and refuses a mismatch with
both numbers named.

**IT COMPOSES THE READERS, IT DOES NOT RE-DERIVE THEM** (Law 1, Law 6). Three of the
four gathers already have an owner:

  - RULINGS → ``learning_block.pending_findings`` — the primitive owns pendingness (a
    question keeps a finding at the gate; only approve/disprove clear it).
  - ALARMS (the trouble half) → ``TroubleDevice.live`` — the lane owns what LIVE means,
    and counts a missing or malformed standing as live on purpose.
  - THE SLATE and the OPEN QUESTIONS → ``bin/cmd/slate``'s own ``_newest_slate`` and
    ``_open_questions``. That ranking is not a glob: its docstring carries two measured
    corrections (14 slates bulk-touched at one mtime; three slates sharing 2026-08-03
    where the filename tiebreak named the 15:50 slate over the 16:41 one). Re-deriving
    it here would be the Law 1 defect at the smallest scale, so this module loads that
    file and calls it. **THE LEADING UNDERSCORE IS CROSSED DELIBERATELY AND NAMED HERE
    RATHER THAN HIDDEN:** ``bin/cmd/slate`` is a program, not a package, so it has no
    public face to reach for — and the alternative is a second owner of a rule that has
    already been wrong twice.

THE DISCOVERY THAT CAME OUT OF WIRING IT, and it is worth carrying: **three of the four
gathers ARE the session-open banner's own lanes** — the hook and the skill read the same
code. So the banner is not stale by construction, only by CLOCK, and re-running the
readers at fire time is precisely the thing that makes the difference measurable instead
of asserted.

**WHAT IS STILL NOT MEASURED, said out loud rather than left to be assumed:** ``probescan``
and ``test -q`` are the two instruments this judge does not re-run — the proof corpus costs
minutes and a judge that costs minutes is a judge the operator learns to route around. Their
figures ride the packet as operator-reported and are checked only for presence. That is a
residue, not a resting state.

**A READER THAT CANNOT BE REACHED IS A LACK, NEVER A PASS.** If the commons is unreadable
or ``bin/cmd/slate`` will not load, this judge says so as a refusal. A judge that goes quiet
when its instrument is unreachable is the vacuous gate the seam exists to stop (Law 8).
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:                       # script-invoked beside the skill
    sys.path.insert(0, str(_REPO))

JUDGE_NAME = "whatslefttodo-door"

# The four gathers in Akien's ruled order, each bound to the instrument SKILL.md names.
# The order is HIS (charter `owner`): CC may not re-order, add a fifth, or drop one.
INSTRUMENTS = {
    "rulings": ("recordverdict",),
    "alarms": ("slate", "probescan", "test"),
    "questions": ("questions",),
    "slate": ("slate",),
}

_SLATE_PROGRAM = _REPO / "bin" / "cmd" / "slate"


def _load_slate_program():
    """Load ``bin/cmd/slate`` as a module. Extensionless by design (it is a command), so
    ``spec_from_file_location`` returns None for it and the loader must be named outright.

    Loaded FRESH on every call, not cached: the program reads its roots from the
    environment at import time (``CAIRN_SLATES_DIR``, ``CAIRN_QUESTIONS_DIR``,
    ``CAIRN_TROUBLES_DIR``), and a cached module would pin whichever roots the first
    caller happened to have — which is how a proof against a temp commons silently reads
    the live one.
    """
    loader = importlib.machinery.SourceFileLoader("cairn_bin_slate", str(_SLATE_PROGRAM))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def measure_the_world() -> dict:
    """What the four gathers WOULD report if run right now. Every value or its refusal.

    Returns ``{key: value}`` for what was measured and ``{key + "_unreachable": why}``
    for what was not. The caller turns the second kind into lacks — this function never
    decides that an unreachable instrument is acceptable.
    """
    out: dict = {}

    try:
        from cairn.machines.learning_block.learning_block import pending_findings
        pend = pending_findings()
        out["rulings_count"] = len(pend)
        out["rulings_oldest_id"] = pend[0]["id"] if pend else None
    except Exception as exc:                          # noqa: BLE001 — loud, never silent
        out["rulings_unreachable"] = f"the gate could not be read — {exc!r}"

    try:
        slate = _load_slate_program()
    except Exception as exc:                          # noqa: BLE001
        slate = None
        out["slate_program_unreachable"] = (
            f"{_SLATE_PROGRAM} would not load — {exc!r}. The newest-slate ranking and the "
            "open-question lane are that program's own rules; this judge composes them "
            "rather than keeping a second copy, so it cannot check those two gathers.")

    if slate is not None:
        troubles, err = slate._live_troubles()
        if err:
            out["troubles_unreachable"] = err
        else:
            out["live_troubles"] = sorted(str(t.get("id")) for t in troubles)

        questions, err = slate._open_questions()
        if err:
            out["questions_unreachable"] = err
        else:
            out["open_questions"] = len(questions)

        path, _data, warn = slate._newest_slate()
        if path is None:
            out["slate_unreachable"] = warn or "no slate could be chosen"
        else:
            out["newest_slate"] = path.stem
            if warn:
                out["slate_warn"] = warn

    return out


def _instrument_lack(field: str, gather) -> dict | None:
    """The gather ran its instrument, or it did not. Absence is the flat contract's lack."""
    if not isinstance(gather, dict):
        return {"field": field,
                "why": f"carries a {type(gather).__name__} — a gather is an object that "
                       f"records WHAT WAS RUN and WHAT CAME BACK. See the charter's "
                       f"input_contract for this gather's shape."}
    ran = gather.get("ran")
    text = " ".join(ran) if isinstance(ran, list) else str(ran or "")
    missing = [name for name in INSTRUMENTS[field] if name not in text]
    if missing:
        return {"field": field,
                "why": f"its 'ran' does not name {missing} — the gather's whole discipline "
                       f"is that it RUNS ITS INSTRUMENT rather than reporting from the "
                       f"session-open banner or from memory. Put the command(s) you "
                       f"actually ran in 'ran', verbatim."}
    return None


def judge_packet(payload: dict, *, world: dict | None = None) -> list[dict]:
    """Every SEMANTIC lack, one pass — {field, why} dicts, this door's own vocabulary.

    Judges only fields that are PRESENT; absence is the flat contract's finding, and
    reporting it twice would be two doors disagreeing about one lack (the convention
    /sorted's judge set).

    ``world`` is the measurement, injectable so a proof can pin the comparison instead of
    racing the live commons. Left out, it is taken from the world at this instant — which
    is the entire point of the door.
    """
    lacks: list[dict] = []
    w = measure_the_world() if world is None else world

    for key in ("rulings_unreachable", "slate_program_unreachable",
                "troubles_unreachable", "questions_unreachable", "slate_unreachable"):
        if w.get(key):
            lacks.append({"field": key.rsplit("_unreachable", 1)[0],
                          "why": f"THIS JUDGE COULD NOT MEASURE IT: {w[key]} — an unreadable "
                                 "instrument is a refusal, not a pass. Fix the instrument, "
                                 "then fire again."})

    for field in INSTRUMENTS:
        gather = payload.get(field)
        if gather is None:
            continue                                  # the flat contract's lack, not this one
        lack = _instrument_lack(field, gather)
        if lack is not None:
            lacks.append(lack)
            continue

        if field == "rulings":
            if "rulings_count" in w:
                if gather.get("count") != w["rulings_count"]:
                    lacks.append({"field": "rulings",
                                  "why": f"reports count={gather.get('count')!r}; the gate "
                                         f"holds {w['rulings_count']} findings at this "
                                         "instant. A stale count is the half of this "
                                         "skill's tracked debt that presence alone cannot "
                                         "catch — re-run recordverdict and refire."})
                if gather.get("oldest_id") != w["rulings_oldest_id"]:
                    lacks.append({"field": "rulings",
                                  "why": f"reports oldest_id={gather.get('oldest_id')!r}; the "
                                         f"oldest finding standing at the gate is "
                                         f"{w['rulings_oldest_id']!r}. The id is asked for "
                                         "rather than the age because a count can be copied "
                                         "off a banner and an id cannot: it is only in the "
                                         "list, and the list is only in the instrument."})

        elif field == "alarms":
            if "live_troubles" in w:
                reported = gather.get("live_troubles")
                if not isinstance(reported, list) or sorted(map(str, reported)) != w["live_troubles"]:
                    lacks.append({"field": "alarms",
                                  "why": f"reports live_troubles={reported!r}; the lane holds "
                                         f"{w['live_troubles']} at this instant. The SET is "
                                         "asked for, not the count — Law 9: an old trouble is "
                                         "not stale by age, and naming them is what makes "
                                         "'still live' a thing the reader can check."})
            for name in ("probes", "proofs"):
                value = gather.get(name)
                if not (isinstance(value, str) and value.strip()):
                    lacks.append({"field": "alarms",
                                  "why": f"carries no {name!r} figure. probescan and test are "
                                         "the two instruments this judge does NOT re-run (the "
                                         "proof corpus costs minutes, and a judge that costs "
                                         "minutes gets routed around), so their outputs ride "
                                         "the packet operator-reported. That is the residue "
                                         "this door leaves; leaving the field blank widens it."})

        elif field == "questions":
            if "open_questions" in w and gather.get("open") != w["open_questions"]:
                lacks.append({"field": "questions",
                              "why": f"reports open={gather.get('open')!r}; the open lane holds "
                                     f"{w['open_questions']} unresolved at this instant. Note "
                                     "the lane is HALF the corpus by construction — the "
                                     "charters' filed_edges need a projector that does not "
                                     "exist yet (open-the-frontier-projector) — so this is the "
                                     "homeless half, and saying so is part of the gather."})

        elif field == "slate":
            if "newest_slate" in w and gather.get("slate_id") != w["newest_slate"]:
                lacks.append({"field": "slate",
                              "why": f"reports slate_id={gather.get('slate_id')!r}; the newest "
                                     f"slate is {w['newest_slate']!r}. The ranking is "
                                     "bin/cmd/slate's own (date, then written_at, then "
                                     "filename) and this judge calls it rather than keeping a "
                                     "second copy — a filename sort would name a different "
                                     "slate, which is a mistake that has already been made."})

    return lacks


__all__ = ["JUDGE_NAME", "INSTRUMENTS", "measure_the_world", "judge_packet"]

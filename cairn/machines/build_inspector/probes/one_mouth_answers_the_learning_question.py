"""WATCHME(one-mouth-answers-the-learning-question) — does every charter answer the learning
question with one mouth, and has the sieve bitten a second one? (ticket 96f71a89a0fa)

THE FAILURE THIS WATCHES FOR. On 2026-08-31 a backfill wrote ``learns`` beside the considered
``how_it_learns`` in every charter without reading it, and the ``learning_declared`` sieve read
the backfill's field. Measured 2026-11-11: 69 charters under cairn/ answered twice, 19 of them
flatly contradicting themselves ("It does not" beside "Yes — narrowly"), and the sieve read
green over every one. The ticket removed ``learns`` everywhere and made the sieve red on its
return. This probe watches that it stays removed.

WHAT IT READS: every ``intention+why.json`` under the repo root (``context["roots"]["cairn"]``
when the holder hands one, else the live repo), skipping proof fixtures, scratch and .git; and
the last record of ``cairn/machines/build_inspector/validations/test_inspector.json``, whose
``teeth_green`` must name the tooth that reintroduces ``learns`` and watches the sieve red it —
a tooth that has never bitten is a tooth nobody has measured.

ENOUGH: no charter carries ``learns``, none lacks ``how_it_learns``, none is unparseable, and
the falsification run stands green. TRIGGER: any offender. No numeric knob exists here.

The probe carries no authority (Law 6): it deposits and pokes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.tools.base.probe import Probe, Threshold, once, owning_ticket, watch_carry

_REPO_ROOT = Path(__file__).resolve().parents[4]
_OWNING_TICKET = "96f71a89a0fa"
_RETIRED = "learns"
_FIELD = "how_it_learns"
_VALIDATION = "cairn/machines/build_inspector/validations/test_one_mouth_answers_the_learning_question.json"
_TOOTH = "learning_declared refuses the retired field"
_HORIZON = 1000
# The first-clause yes/no reading the contradiction count comes from (D5). Not tuned to any
# number: the only number enough depends on is 0, and with one mouth it is 0 by construction.
_YES = re.compile(r"^\s*(yes|the point|directly|through|by |reflexively|from |partly|barely)", re.I)
_NO = re.compile(r"^\s*(it does not|it doesn.t|no\b|not yet|nothing|it holds nothing)", re.I)
_HEAD = 60


def _repo_root(context: dict | None) -> Path:
    roots = (context or {}).get("roots") if isinstance(context, dict) else None
    if isinstance(roots, dict) and roots.get("cairn"):
        return Path(roots["cairn"])
    return _REPO_ROOT


def _charters(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("intention+why.json"):
        rel = "/" + p.relative_to(root).as_posix()
        if "/proofs/" in rel or "scratch" in rel or "/.git/" in rel:
            continue
        out.append(p)
    return sorted(out)


def _shape(text) -> str:
    if not isinstance(text, str):
        return ""
    head = text[:_HEAD]
    return "yes" if _YES.match(head) else "no" if _NO.match(head) else ""


def census(root: Path | None = None) -> dict:
    """One walk: how many charters answer the learning question once, twice, or not at all."""
    root = _REPO_ROOT if root is None else Path(root)
    c = {"charters": 0, "both": 0, "only_learns": 0, "only_how_it_learns": 0, "neither": 0,
         "unparseable": 0, "contradictions": 0, "offenders": []}
    for p in _charters(root):
        c["charters"] += 1
        rel = p.relative_to(root).as_posix()
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(d, dict):
                raise ValueError("not an object")
        except (OSError, ValueError):
            c["unparseable"] += 1
            c["offenders"].append(rel)
            continue
        has_l = _RETIRED in d
        how = d.get(_FIELD)
        has_h = isinstance(how, str) and bool(how.strip())
        if has_l and has_h:
            c["both"] += 1
            a, b = _shape(d[_RETIRED]), _shape(how)
            if a and b and a != b:
                c["contradictions"] += 1
        elif has_l:
            c["only_learns"] += 1
        elif has_h:
            c["only_how_it_learns"] += 1
        else:
            c["neither"] += 1
        if has_l or not has_h:
            c["offenders"].append(rel)
    return c


def _falsification_stands(root: Path) -> bool:
    try:
        records = json.loads((root / _VALIDATION).read_text(encoding="utf-8"))
        last = records[-1]
        return (last["verdict"] == "green"
                and any(_TOOTH in str(t) for t in last["evidence"]["teeth_green"]))
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return False


def _survey(context: dict) -> dict:
    def compute():
        root = _repo_root(context)
        c = census(root)
        c["falsification_stands"] = _falsification_stands(root)
        return c
    return once(context, "one_mouth_census", compute)


def _enough(context: dict) -> bool:
    s = _survey(context)
    return not s["offenders"] and s["both"] == 0 and s["falsification_stands"]


def _trigger(now, context: dict) -> bool:
    return bool(_survey(context)["offenders"])


def _carry(context: dict) -> dict:
    s = _survey(context)
    if s["both"]:
        finding = f"{s['both']} charter(s) answer the learning question with two mouths"
    elif s["only_learns"]:
        finding = f"{s['only_learns']} charter(s) still carry the retired field learns"
    elif s["neither"] or s["unparseable"]:
        finding = "a charter answers the learning question with no mouth, or cannot be read"
    elif not s["falsification_stands"]:
        finding = "the sieve has not yet redded a deliberately reintroduced learns"
    else:
        finding = "every charter answers once and the sieve has refused a second mouth"
    return {
        "finding": finding,
        "census": {k: v for k, v in s.items() if k != "offenders"},
        "offenders": list(s["offenders"]),
        "falsification_stands": s["falsification_stands"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": ("WRONG INTENT if the fix is to make the two fields agree rather "
                              "than to remove one, or if the surviving text is the backfill's."),
        "suggests": ("read the offender's charter: a returned learns is a second mouth to remove, "
                     "not to reconcile; a missing how_it_learns is a question its owner answers."),
    }


PROBE = Probe(
    why="does every charter answer the learning question with one mouth? — the 2026-08-31 "
        "backfill wrote learns beside how_it_learns without reading it, and 19 of 69 pairs "
        "contradicted flatly while the sieve read green (census 2026-11-11)",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET), "object": "one-mouth-answers-the-learning-question"},
    verb="machines/watchme/watch",
    carry=watch_carry(_OWNING_TICKET, _carry, fails=_trigger),
    enough=_enough,
    thresholds=(
        Threshold(None, "the predicate itself, no number: not s['offenders'] and s['both'] == 0 and s['falsification_stands']",
                  set_by="ticket 96f71a89a0fa (the predicate itself; no number to move)"),
    ),
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(census(), indent=2, ensure_ascii=False))

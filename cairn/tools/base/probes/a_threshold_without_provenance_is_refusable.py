"""WATCHME(a-threshold-without-provenance-is-refusable) — does every probe still say what set
the number behind its ``enough``, and does that hold while new probes are born? (ticket
336a781018ba)

THE FAILURE THIS WATCHES FOR. The ticket's own words: "the failure this ticket names is a rule
that covers what exists today and lets the 48th probe be born undeclared." Reaching zero is
the build; HOLDING zero while the corpus grows is what this probe measures. Measured at the
build (2026-11-12): 105 probe modules, 103 carrying ``enough=``, every one of them silent
about what set its number, before the migration declared them.

WHAT IT READS: ``cairn.tools.base.threshold_census.census`` over the repo root (the pulse
context's ``repo_root`` when the holder hands one, else the live repo), once per pulse. Each
pulse appends one line to ``runs.jsonl`` under the holder's instance space,
``<instance>/devices/cairn/0/tools/base/threshold_census/runs.jsonl`` (Law 6: a tool's
ongoing state berths under the holder that assembled it; the pulse context's ``roots`` is the
proof's isolation seam). The file is append-only and read whole.

TRIGGER: the reading changed since the last line (the count, the total or a band), or there
is no last line — the probe speaks when there is something new to say, never on every beat.
ENOUGH (D12): the last six lines all read 0 in both bands, and the live total on the sixth is
at least 2 above the first: a first zero, five runs holding it, and at least two probes born
declared inside the window. Both numbers are declared below, set by the ticket's watchme.
The probe carries no authority (Law 6): it deposits and pokes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base import threshold_census
from cairn.tools.base.address import resolve
from cairn.tools.base.probe import Probe, Threshold, once, owning_ticket, watch_carry

_OWNING_TICKET = "336a781018ba"

# The ticket's watchme.enough: "the count reaches 0 AND holds at 0 across 5 subsequent runs
# in which at least 2 new probes were added." Six lines is the first zero plus five holding.
_ENOUGH_RUNS_HOLDING = 5
_ENOUGH_GROWTH = 2
_HORIZON = 2000


def runs_path(roots: dict | None = None) -> Path:
    return (resolve("instance/devices", roots) / "cairn" / "0" / "tools" / "base"
            / "threshold_census" / "runs.jsonl")


def read_runs(roots: dict | None = None) -> list[dict]:
    p = runs_path(roots)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def held(runs: list[dict]) -> bool:
    """D12: the last six lines read 0 in both bands and the total grew by at least 2."""
    window = runs[-(_ENOUGH_RUNS_HOLDING + 1):]
    if len(window) < _ENOUGH_RUNS_HOLDING + 1:
        return False
    if any(r.get("provenance_less") != 0 or r.get("disabled_provenance_less", 0) != 0
           for r in window):
        return False
    return window[-1].get("total", 0) - window[0].get("total", 0) >= _ENOUGH_GROWTH


def record_run(*, roots: dict | None = None, repo_root: Path | None = None) -> dict:
    """Run the census once and append its line (D18's shape); return the line."""
    c = threshold_census.census(repo_root)
    prior = read_runs(roots)
    line = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance_less": c["provenance_less"],
        "total": c["total"],
        "with_enough": c["with_enough"],
        "added_since_last": c["total"] - prior[-1]["total"] if prior else 0,
        "silent": c["provenance_less_paths"],
        "disabled_total": c["disabled_total"],
        "disabled_provenance_less": c["disabled_provenance_less"],
        "disabled_silent": c["disabled_provenance_less_paths"],
    }
    p = runs_path(roots)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return line


def _survey(context: dict) -> dict:
    ctx = context if isinstance(context, dict) else {}

    def compute():
        roots, repo_root = ctx.get("roots"), ctx.get("repo_root")
        before = read_runs(roots)
        line = record_run(roots=roots, repo_root=repo_root)
        runs = before + [line]
        return {"line": line, "previous": before[-1] if before else None, "runs": runs}

    return once(ctx, "threshold_census_run", compute)


_COMPARED = ("provenance_less", "total", "disabled_total", "disabled_provenance_less")


def _trigger(now, context: dict) -> bool:
    s = _survey(context)
    prev = s["previous"]
    return prev is None or any(prev.get(k) != s["line"].get(k) for k in _COMPARED)


def _enough(context: dict) -> bool:
    return held(_survey(context)["runs"])


def _holds(context: dict) -> bool:
    line = _survey(context)["line"]
    return line["provenance_less"] == 0 and line["disabled_provenance_less"] == 0


def _carry(context: dict) -> dict:
    s = _survey(context)
    line, runs = s["line"], s["runs"]
    at_zero = 0
    for r in reversed(runs):
        if r.get("provenance_less") == 0 and r.get("disabled_provenance_less", 0) == 0:
            at_zero += 1
        else:
            break
    is_held = held(runs)
    if line["provenance_less"] or line["disabled_provenance_less"]:
        finding = (f"{line['provenance_less']} live and {line['disabled_provenance_less']} "
                   f"disabled probe(s) carry an enough whose number says nothing of what set it")
    elif is_held:
        finding = (f"0 provenance-less across the last {_ENOUGH_RUNS_HOLDING + 1} runs while the "
                   f"corpus grew to {line['total']}: the rule holds for probes born after it")
    else:
        finding = (f"0 provenance-less for {at_zero} run(s) at {line['total']} probes; the window "
                   f"has not yet held across {_ENOUGH_RUNS_HOLDING + 1} runs with growth of "
                   f"{_ENOUGH_GROWTH}")
    return {"ticket": owning_ticket(_OWNING_TICKET), **line,
            "runs_at_zero": at_zero, "held": is_held, "finding": finding}


PROBE = Probe(
    why="does every probe say what set the number behind its enough, and does that hold while "
        "new probes are born? — at the build 103 of 105 probes carried an enough and every one "
        "was silent about its number (census 2026-11-12)",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET), "object": "a-threshold-without-provenance-is-refusable"},
    verb="machines/watchme/watch",
    carry=watch_carry(_OWNING_TICKET, _carry, holds=_holds),
    enough=_enough,
    thresholds=(
        Threshold(_ENOUGH_RUNS_HOLDING, "runs after the first zero that must also read zero",
                  set_by="ticket 336a781018ba names the number (watchme.enough: 5 subsequent runs)"),
        Threshold(_ENOUGH_GROWTH, "probes the corpus must grow by inside the holding window",
                  set_by="ticket 336a781018ba names the number (watchme.enough: at least 2 new probes)"),
    ),
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(threshold_census.census(), indent=2, ensure_ascii=False)[:4000])

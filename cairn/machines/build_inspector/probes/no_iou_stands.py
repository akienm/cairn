"""PROBE — once the scrub lands, does the word stay gone?

Berth for the WATCHME that ticket f5dbfddea8c6 (slug no-iou-stands) carries. It sits beside
``cairn/machines/build_inspector`` because that is what it watches: the sieve
``no_iou_stands`` and the census ``iou_census.json`` beside it.

THE CLAIM UNDER WATCH. Akien, 2026-09-29: "THERE ARE TO BE NO IOUS EVER", said after he had
answered it more than once. The sieve reds a site on the day it is written. Whether the rule
holds is a claim about the future: does a resting debt stop coming back, or do new ones keep
being written and scrubbed?

THE PAIR, from the ticket's watch spec:

  - FIRE when a site stands that no open question covers. A site at a path the census sends
    to Akien (disposition ``question``, Q#89) is waiting on his answer and is already loud
    as a red on its row. Any other site is a debt written down again, and one is enough.
  - CLEAR when 30 consecutive commits each read zero sites, and the sieve's proof is sealed
    green (its first tooth plants the word and is caught). The 30 commits are measured from
    git itself, ``git grep`` at each commit, so the clear needs no pulse history.

The word itself is read from the sieve (``inspector._IOU_WORD``), never restated here. A
copy would let this probe go green against itself while the sieve's word drifted.

AUTHORITY: none. This probe deposits and pokes. Re-opening the node is build_inspector's
act at the register (Law 6).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cairn.tools.base.probe import Probe, Threshold, once, owning_ticket, watch_carry

_TICKET_ID = "f5dbfddea8c6"
_OWNING_TICKET = "no-iou-stands"

# The clear's run length, the number the ticket's watch spec names ("the sieve green over 30
# consecutive commits after the scrub lands").
_ENOUGH = 30

_PROOF_SEAL = "cairn/machines/build_inspector/validations/test_no_iou_stands.json"


def _clean_at(repo_root: str, rev: str) -> int:
    """How many word sites an authored file carries at one commit: the sieve's own reading,
    run against a tree instead of the working copy."""
    from cairn.machines.build_inspector import inspector as I
    r = subprocess.run(["git", "-C", repo_root, "grep", "-n", "-I", "-w", "-e", I._IOU_WORD, rev],
                       capture_output=True, text=True, timeout=60)
    if r.returncode not in (0, 1):
        raise RuntimeError(f"git grep failed at {rev}: {r.stderr.strip()}")
    n = 0
    for ln in r.stdout.splitlines():
        path = ln.split(":", 2)[1]
        if path not in I._IOU_ALLOW and not I._iou_is_record(path):
            n += 1
    return n


def survey(repo_root: str | None = None) -> dict:
    """The live read: today's sites, the census's open-question paths, the last _ENOUGH
    commits' counts, and the proof's seal."""
    from cairn.machines.build_inspector import inspector as I
    root = str(repo_root or I._REPO_ROOT)
    I._IOU_CACHE.pop(root, None)
    sites = I._iou_sites(root)
    census = Path(root) / I._IOU_HOME / "iou_census.json"
    asked = set()
    if census.is_file():
        asked = {r["path"] for r in json.loads(census.read_text()).get("rows", [])
                 if r.get("disposition") == "question"}
    revs = subprocess.run(["git", "-C", root, "rev-list", f"--max-count={_ENOUGH}", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.split()
    counts = [_clean_at(root, rev) for rev in revs]
    seal = Path(root) / _PROOF_SEAL
    sealed_green = False
    if seal.is_file():
        entries = json.loads(seal.read_text())
        last = entries[-1] if isinstance(entries, list) and entries else entries
        sealed_green = isinstance(last, dict) and str(last.get("verdict", "")).lower() in ("green", "pass")
    return {"sites": sites, "asked": sorted(asked), "commit_counts": counts,
            "sealed_green": sealed_green}


def judge(s: dict) -> dict:
    """The pure judgement, separable from the read so a proof can feed it fixtures."""
    unasked = [x for x in s["sites"] if x["file"] not in set(s["asked"])]
    run = 0
    for c in s["commit_counts"]:
        if c:
            break
        run += 1
    return {"unasked": unasked, "standing": len(s["sites"]), "clean_run": run,
            "sealed_green": s["sealed_green"]}


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(once(context, "survey", survey))


def _trigger(now, context: dict) -> bool:
    """TRUE when a site stands that no open question covers: a debt written down again."""
    return bool(_seen(context)["unasked"])


def _enough(context: dict) -> bool:
    """CLEARED when the last _ENOUGH commits each read zero sites and the proof is sealed
    green. A site standing today means the newest commit is not clean, so the two halves
    cannot both hold."""
    j = _seen(context)
    return j["clean_run"] >= _ENOUGH and j["sealed_green"] and not j["unasked"]


def _carry(context: dict) -> dict:
    j = _seen(context)
    return {"finding": "a site stands that no open question covers: a rule left resting as "
                       "policy was written down again after the scrub",
            "unasked": [{"file": x["file"], "line": x["line"], "kind": x["kind"]}
                        for x in j["unasked"]],
            "counts": {"standing": j["standing"], "unasked": len(j["unasked"]),
                       "clean_run": j["clean_run"]},
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's WRONG INTENT: the word is gone but the same "
                                 "sites say it again, or a synonym, measured at the census sites",
            "suggests": "replace the site with the enforcing address or the ticket id, or open "
                        "a question at its outline line if the rule is Akien's text"}


# Same placeholder horizon as the sibling probes: the beat rate is not yet a real number.
_HORIZON = 1000

PROBE = Probe(
    why="Akien had to say more than once that no rule rests as a debt; the sieve reds a site "
        "the day it is written, and this watch asks whether sites stop being written at all",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "constrain", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
    enough=_enough,
    thresholds=(
        Threshold(_ENOUGH, "enough: CLEARED when the last _ENOUGH commits each read zero sites "
                           "and the sieve's proof is sealed green.",
                  set_by="f5dbfddea8c6 watch spec: 'the sieve green over 30 consecutive commits'"),
    ),
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey()
    j = judge(s)
    print(json.dumps({"standing": j["standing"], "unasked": len(j["unasked"]),
                      "clean_run": j["clean_run"], "sealed_green": j["sealed_green"],
                      "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j})}, indent=2))

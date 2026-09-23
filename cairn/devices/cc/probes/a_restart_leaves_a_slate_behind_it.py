"""PROBE — does a restart actually leave a slate behind it?

WATCHME probe for ticket 15b80c0c393c, object a_restart_leaves_a_slate_behind_it.
The /restart skill's second step fires /saveslate, and the whole safety of the
skill is that the slate is written BEFORE the hand-off. A restart with no slate
behind it is the failure the skill exists to prevent — and it is exactly the
failure a prose step cannot stop, which is why this watch is what says whether
physics is owed.

It reads two folders and PAIRS them. There is no poller and the skill pokes
nothing: the read happens on the beat the ground loop already runs.

  CONSUMED — every file under ``~/.cairn/launchers/superclaude/<instance>/consumed/``,
             named ``<flag>.<stamp>`` with the stamp in %Y%m%dT%H%M%S local time.
             The launcher consumes a one-shot flag by MOVING it there, so these
             files are the record of every restart that actually happened.
  SLATES   — ``CairnCommons/slates/*.json``, each carrying ``written_at`` as an
             ISO timestamp with no timezone.

A slate pairs with a consumed flag iff its ``written_at`` falls in the sixty
seconds BEFORE the consumed stamp.

Trigger: a consumed file whose stamp is newer than the watermark this probe last
carried (an absent watermark means every consumed file is new).
Carry:   the PAIRING, never a boolean. An unpaired restart is carried IMMEDIATELY
         on the beat it is seen — it does not wait for a third sample.
Enough:  three consecutive consumed flags, in stamp order, each paired.

AUTHORITY: none. This probe deposits and pokes; the back-edge that re-opens the
node is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe, owning_ticket

_TICKET = "15b80c0c393c"
_STAMP_FORMAT = "%Y%m%dT%H%M%S"
_PAIR_WINDOW_SECONDS = 60
_ENOUGH_RUN = 3

_FLAGS_HOME = Path.home() / ".cairn" / "launchers" / "superclaude"
_SLATES = Path("/home/akien/dev/src/CairnCommons/slates")
_WATERMARK = (address.instance_path("cc", 0) / "probes"
              / "a_restart_leaves_a_slate_behind_it.json")


def _stamp_of(name: str):
    """The stamp is the LAST dot-separated token — a consumed name is
    ``<flag>.<stamp>`` and a withdrawn one is ``<flag>.withdrawn.<stamp>``."""
    try:
        return datetime.strptime(name.rsplit(".", 1)[-1], _STAMP_FORMAT)
    except (ValueError, IndexError):
        return None


def _consumed() -> list:
    """Every consumed flag across every instance, newest LAST."""
    found = []
    try:
        instances = sorted(p for p in _FLAGS_HOME.iterdir() if p.is_dir())
    except OSError:
        return []
    for instance in instances:
        folder = instance / "consumed"
        try:
            names = sorted(p.name for p in folder.iterdir() if p.is_file())
        except OSError:
            continue
        for name in names:
            stamp = _stamp_of(name)
            if stamp is not None:
                found.append((stamp, name))
    found.sort()
    return [name for _, name in found]


def _slate_times() -> list:
    """Every slate's ``written_at``, parsed. An unparseable slate is skipped
    rather than guessed at — a wrong pairing is worse than a missing one."""
    times = []
    try:
        paths = sorted(_SLATES.glob("*.json"))
    except OSError:
        return times
    for path in paths:
        try:
            written = json.loads(path.read_text()).get("written_at")
            times.append((datetime.fromisoformat(str(written)), path.stem))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    times.sort()
    return times


def _pair(name: str) -> dict:
    """The pairing for one consumed flag — the carry's whole shape."""
    stamp = _stamp_of(name)
    pairing = {
        "ticket": owning_ticket(_TICKET),
        "consumed": name,
        "consumed_at": stamp.isoformat() if stamp else None,
        "slate": None,
        "slate_written_at": None,
        "paired": False,
    }
    if stamp is None:
        return pairing
    for written, slate_id in reversed(_slate_times()):
        gap = (stamp - written).total_seconds()
        if 0 <= gap <= _PAIR_WINDOW_SECONDS:
            pairing["slate"] = slate_id
            pairing["slate_written_at"] = written.isoformat()
            pairing["paired"] = True
            break
    return pairing


def _watermark() -> str:
    try:
        return str(json.loads(_WATERMARK.read_text()).get("watermark") or "")
    except (OSError, ValueError, json.JSONDecodeError):
        return ""


def _fresh() -> list:
    """The consumed flags newer than the watermark, newest LAST."""
    mark = _stamp_of(_watermark()) if _watermark() else None
    if mark is None:
        return _consumed()
    return [n for n in _consumed()
            if (_stamp_of(n) or mark) > mark]


def _trigger(now, context: dict) -> bool:
    return bool(_fresh())


def _carry(context: dict) -> dict:
    fresh = _fresh()
    if not fresh:
        return {"ticket": owning_ticket(_TICKET), "consumed": None,
                "consumed_at": None, "slate": None, "slate_written_at": None,
                "paired": False}
    newest = fresh[-1]
    pairing = _pair(newest)
    try:
        _WATERMARK.parent.mkdir(parents=True, exist_ok=True)
        _WATERMARK.write_text(json.dumps({"watermark": newest}, indent=2) + "\n")
    except OSError:
        # The watermark is a convenience, never a gate: a probe that could not
        # write it re-carries the same pairing next beat, which is noisy and
        # honest. Losing the CARRY to a failed bookkeeping write would not be.
        pass
    return pairing


def _enough(context: dict) -> bool:
    consumed = _consumed()
    if len(consumed) < _ENOUGH_RUN:
        return False
    return all(_pair(name)["paired"] for name in consumed[-_ENOUGH_RUN:])


PROBE = Probe(
    why="a restart that leaves no slate behind it is the failure this skill exists "
        "to prevent, and a probe that never fires gathers nothing while looking "
        "like learning. This watches whether the slate is really there.",
    trigger=_trigger,
    to="harbor_master",
    verb="",
    channel="personal",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    while_true=False,
    enough=_enough,
    horizon=100,
)


if __name__ == "__main__":
    print(json.dumps({
        "consumed_count": len(_consumed()),
        "fresh_count": len(_fresh()),
        "would_trigger": _trigger(None, {}),
        "enough": _enough({}),
    }, indent=2))

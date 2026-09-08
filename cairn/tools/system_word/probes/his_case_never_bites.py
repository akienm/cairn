"""PROBE — does a system word still fold at every door, or has a seam started biting on case?

Berth for the WATCHME(system-words-fold) that ticket e3cf75c6dc8f carries. Berthed beside
``system_word`` because that is WHAT IT WATCHES: not the module (a pure fold cannot drift)
but the CENSUS of seams that are supposed to call it, which is hand-taken and grows only by
someone remembering (charter, filed edge (a)). The ticket lives in the commons and this does
not follow it there (``cairn/tools/base/probe.py``: a probe berths with what it watches).

THE EFFICACY QUESTION. The ruling is "everywhere we're talking a system word, it should be
case insensitive if there's any chance of it coming from me." The build proved it at nineteen
seams on 2026-09-07. The way that goes wrong is silent and one seam at a time: a new verb
table, a new ``argv[0] == "..."`` in a fresh CLI, a bash launcher with ``case "$1"``, and the
day his shift key lands on THAT door it bites exactly as ``ruled`` bit. A bite is one entry
point refusing a word its lowercase form accepts. This replays the mixed-case drives against
the live tree and counts bites.

DRIVEN, NOT READ, for the same reason the proof is: a grep for ``fold(`` passes a seam that
calls it and compares the raw token anyway. What it drives is deliberately the CHEAP subset —
the dispatcher on a stub tree (subprocess), five python mains by import, the base device's
view lookup, the map filter and the marker — no bus, no database, nothing that writes to a
live berth; it reads the ruling list and the harbor master's fleet, which are read-only.
Cheap enough to sit on a tester seal.

READS THE TREE IT RUNS IN. A bite here is a bite in the working copy, which may be mid-edit;
the trigger therefore asks for a bite on TWO consecutive surveys before it pokes, so one
half-typed seam does not fire the owner's inbox.

AUTHORITY: none — it deposits and pokes. codemother, as owner of the care of the code, is
the receiver named in the ticket; the poke rides to the harbor master like every other watch,
which is where codemother's own watch reads.
"""

from __future__ import annotations

import io
import os
import stat
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DISPATCHER = _REPO_ROOT / "bin" / "cairn"
_OWNING_TICKET = owning_ticket("system-words-fold-case-when-akien-types-them")

# Two consecutive surveys must bite before the trigger fires — see the module docstring.
_PATIENCE = 2
# Fourteen days of clean seals is the ticket's own "enough"; the shim counts pulses, not
# days, and nothing measures how many pulses that is yet — the same debt every horizon in
# this corpus carries, stated rather than hidden.
_ENOUGH_CLEAN = 14


def _quiet(fn, *args):
    """Run a python main with its streams swallowed; SystemExit becomes a code."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            return fn(*args)
        except SystemExit as exc:
            return exc.code
        except Exception as exc:  # noqa: BLE001 — a crash on the uppercase form IS a bite
            return f"raised {type(exc).__name__}"


def _stub(dir_: Path, name: str, body: str) -> None:
    p = dir_ / name
    p.write_text("#!/usr/bin/env bash\n" + body + "\n")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)


def _drive_dispatcher() -> list[tuple[str, bool]]:
    """(entry point, bit) for the two dispatcher paths, on a stub tree it owns."""
    out = []
    with tempfile.TemporaryDirectory() as d:
        cmd = Path(d) / "cmd"
        cmd.mkdir()
        _stub(cmd, "echoer", 'echo "$*"')
        inst = Path(d) / "inst" / "fx_dev" / "0" / "bin"
        inst.mkdir(parents=True)
        _stub(inst, "show", 'echo "show:$*"')
        env = {**os.environ, "CAIRN_CMD_DIR": str(cmd), "CAIRN_INSTANCE_ROOT": str(d + "/inst")}

        def run(*a):
            return subprocess.run([str(_DISPATCHER), *a], capture_output=True, text=True,
                                  env=env, timeout=60)

        r = run("ECHOER", "x", "Y")
        out.append(("bin/cairn legacy path", not (r.returncode == 0 and r.stdout == "x Y\n")))
        r = run("FX_DEV", "Show", "Map")
        out.append(("bin/cairn device path", not (r.returncode == 0 and r.stdout == "show:Map\n")))
    return out


def _drive_python() -> list[tuple[str, bool]]:
    out = []
    from cairn.devices.cairn.machines.ground_loop.cli import main as gl_main
    out.append(("ground_loop HELP", _quiet(gl_main, ["HELP"]) != 0))

    from cairn.tools.orient import orient
    out.append(("orient GIT", _quiet(orient._main, ["GIT"]) != 0))

    from cairn.machines.skill_block.__main__ import main as sb_main
    out.append(("skill_block CONTRACT", _quiet(sb_main, ["CONTRACT", "sorted"]) != 0))

    from cairn.machines.ruling.cli import main as ru_main
    out.append(("ruling LIST", _quiet(ru_main, ["LIST"]) != _quiet(ru_main, ["list"])))

    from cairn.devices.tester.cli import main as te_main
    with tempfile.TemporaryDirectory() as empty:
        out.append(("tester --SEAL -Q", _quiet(te_main, ["--SEAL", "-Q", empty]) != 2))

    from types import SimpleNamespace

    from cairn.tools.base.device import BaseDevice

    # A NAMESPACE, NOT A SUBCLASS: build_inspector's silent_device sieve counts every
    # BaseDevice subclass outside proofs/ as a device that must emit(), and a fixture that
    # merely lends _handle_show a `declared_views` is not a device (found 2026-09-07 at the
    # WATCHME crossing, which this probe's own fixture had turned red).
    fx = SimpleNamespace(device_id="fx", declared_views=lambda: {"map": lambda: {}},
                         _render_view=lambda what, data: "")
    got = BaseDevice._handle_show(fx, {"body": {"what": "MAP"}})
    out.append(("base _handle_show MAP", got.get("accepted") is not True))

    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    fleet = {"open": [{"label": "PROVED"}, {"label": "BUILDME"}], "in_port": [], "findings": []}
    out.append(("harbor_master filter OPEN",
                len(HarborMasterDevice._filter_fleet(fleet, "OPEN")["open"]) != 1))

    from cairn.machines.ruling import ruling
    out.append(("ruling marker lowercase",
                not ruling.scan_for_ruling_markers("he ruled it", strong_only=True)))
    return out


def survey() -> dict:
    """Every entry point driven, and which bit. One survey, no memory."""
    drives = _drive_dispatcher() + _drive_python()
    bites = [name for name, bit in drives if bit]
    return {"entry_points": len(drives), "bites": len(bites), "bit": bites}


def _survey(context: dict) -> dict:
    return once(context, "survey", survey)


def _trigger(now, context: dict) -> bool:
    """TRUE on a bite that has survived ``_PATIENCE`` consecutive surveys — the shim hands
    back the previous survey's bites in ``context['previous_bites']`` when it has one; a
    first survey with no previous is a single observation and holds."""
    s = _survey(context)
    if s["bites"] == 0:
        return False
    previous = context.get("previous_bites") or []
    return any(b in previous for b in s["bit"]) or context.get("consecutive", 1) >= _PATIENCE


def _enough(context: dict) -> bool:
    """CLEARED after ``_ENOUGH_CLEAN`` consecutive clean surveys — the ticket's fourteen
    days, counted in surveys because that is what the shim can count. A single clean survey
    is NOT enough: that is the retire-before-it-can-fire shape this corpus already paid for
    (``does_optional_mean_never_carried``, 2026-07-30)."""
    s = _survey(context)
    return s["bites"] == 0 and context.get("clean_streak", 0) >= _ENOUGH_CLEAN


def _carry(context: dict) -> dict:
    s = _survey(context)
    return {"finding": "a system word bit on case at a live entry point",
            "bit": s["bit"],
            "entry_points": s["entry_points"],
            "ticket": _OWNING_TICKET,
            "against_falsifier": "clause (3): an entry point in the census refuses the "
                                 "uppercase form of a word its lowercase form accepts",
            "suggests": "the seam named in `bit` compares his token by bytes — route the "
                        "compare through cairn.tools.system_word and add the drive to the "
                        "proof; if the seam is new, the census grew without the rule"}


PROBE = Probe(
    why="the case rule was proved at nineteen seams on 2026-09-07 and holds only where a "
        "seam remembers to call the fold; a new door that compares his token by bytes bites "
        "silently, one word at a time, the day his shift key lands on it. This replays the "
        "mixed-case drives against the live tree and counts the bite before he meets it.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "codemother", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    import json
    s = survey()
    print(json.dumps(s, indent=2))
    sys.exit(1 if s["bites"] else 0)

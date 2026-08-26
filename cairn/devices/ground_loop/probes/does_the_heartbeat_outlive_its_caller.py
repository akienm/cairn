"""does_the_heartbeat_outlive_its_caller — where the heartbeat LIVES, asked of the kernel.

Ticket: ``the-heartbeat-outlives-its-caller``. The loop is the one resident process every
callback in this system hangs off, and until 2026-08-18 its lifetime was an accident of
which window launched it. MEASURED that day: the kernel oom-killed the claude binary at
14:57:31, systemd marked ``app-org.kde.konsole-….scope`` "Failed with result oom-kill" at
14:57:43, and the loop's own trail carries loop starts at 14:52:55 and 14:58:01 with
nothing between — the heartbeat died inside the terminal's cgroup because ``setsid``
detaches a tty and does not detach a cgroup. A thing declared ALWAYS UP whose survival
depends on a window staying open is policy wearing physics' clothes (Law 4).

WHY A WATCH AND NOT ONLY A PROOF. The proof answers "was it started right"; this answers
"is it parented right NOW", and NOW is the question that was false and unnoticed for
weeks. A launcher can be edited back, a hand-start can put the loop anywhere, and neither
event announces itself. So the reading is taken from the process that is actually beating,
every beat, out of its own ``/proc/self/cgroup`` — ~200 bytes, no scan, no clock of its
own, on a wake-up that was going to happen anyway.

THE PREDICATE IS INVERTED ON PURPOSE, and this is the one design decision here worth
reading twice. The obvious form is "RED when the loop is under a terminal scope", which
needs a LIST of what counts as a terminal — konsole, gnome-terminal, vte-spawn, tmux,
sshd, the session scope, the superclaude scope — and a list is a thing that goes stale
silently the first time a host runs a terminal nobody enumerated. The systemd-level
distinction needs no list at all:

    a ``.scope`` is a cgroup the manager created AROUND processes someone else forked;
    it exists only while those processes do, so its lifetime IS the caller's.
    a ``.service`` is a unit the manager forked and owns; its lifetime is the manager's.

So GREEN is "in a service of the user manager" and RED is "in a scope" — every terminal,
named or unnamed, falls out of the second clause for free. The enumeration problem raised
at hypothesize is answered by not having an enumeration.

WHAT ``enough`` NEEDS, AND WHY THIS INSTALL DOES NOT SATISFY IT. Sitting in the right
cgroup is what the launcher SAID; outliving a caller is what the parenting is FOR. The
witness is already on disk in two files the system writes anyway: the loop's own process
start time (``/proc/<pid>/stat``) and the boot log's per-line ``<stamp>.<pid>`` prefix,
which names every entry point that ever launched. The spawner is the launcher whose
"ground_loop: spawn attempted" line sits just before this loop's start; when THAT pid is
gone and this loop is still beating, a caller has died while the heartbeat kept going and
the watch may retire. In an ordinary launch that pid is not a bystander — the launcher
``exec``s the claude binary, so the spawner pid IS the session, and its death is the event
this whole seam exists for.

AND THE FIRST CLEARANCE DOES NOT COUNT, which is worth knowing before someone reads a
retirement off it. The live fire on 2026-08-18 drove the real launcher with a STAND-IN
binary that exits at once, so the spawner (pid 574929) was already gone seconds later and
``outlived_its_spawner`` came back True against a loop 70 seconds old. That is the fixture
satisfying ``enough``, not a caller dying: nothing was outlived except a shell that had
nothing left to do. The condition is right for production and was met artificially here,
so the watch STANDS until a real session's pid is the one that went away.

AUTHORITY: none (Law 6). This probe reads, deposits and pokes; re-opening the node is the
owner's act at the register.

    python3 -m cairn.devices.ground_loop.probes.does_the_heartbeat_outlive_its_caller
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import resolve
from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-heartbeat-outlives-its-caller"

# Same placeholder horizon, same tracked debt, as every other probe in this device: the
# beat rate is not yet a real number, so a horizon in PULSES is a bound, not a duration.
_HORIZON = 1000

# How far before the loop's own start a launcher's spawn line may sit and still be read as
# THE spawner. The spawn is the launcher's last act before exec, and the loop is up within
# a second of it; ten seconds is loose enough for a cold import and tight enough that an
# unrelated launch a minute earlier is not mistaken for the parent.
_SPAWNER_WINDOW_S = 10.0

_STAMP = re.compile(r"^(\d{8})\.(\d{6})\.(\d{1,6})\.(\d+):\s(.*)$")


# ── the cgroup reading, written once ─────────────────────────────────────────
# THE ONE READER OF /proc/*/cgroup IN THIS CORPUS. The proof loads this module by path and
# uses these three functions rather than re-spelling the parse, which is the whole reason
# they are module-level and take a pid instead of closing over ``self``.

def cgroup_of(pid: int | str = "self") -> str | None:
    """The cgroup v2 path of ``pid``, or ``None`` when there is no unified line to read.

    ``None`` is a real answer and not an error: a v1-only host, a pid that exited between
    the listing and the read, and a container with no unified hierarchy all land here, and
    each is a fact about the world rather than a broken probe (Law 7 — the lack is named
    by the caller that reports it, not swallowed here into a plausible default)."""
    try:
        raw = Path(f"/proc/{pid}/cgroup").read_text()
    except OSError:
        return None
    for line in raw.splitlines():
        if line.startswith("0::"):
            # The kernel appends " (deleted)" when the cgroup has been removed out from
            # under a still-living process — which is exactly what a killed caller's scope
            # looks like for the moment between the kill and the last exit. The path is
            # still the identity; the marker is not part of it, and swallowing it here
            # keeps every downstream comparison from silently missing.
            return line[3:].removesuffix(" (deleted)")
    return None


def is_descendant(inner: str | None, outer: str | None) -> bool:
    """Is ``inner`` the same cgroup as ``outer``, or beneath it? Path containment on the
    unified hierarchy, with the separator forced so ``/a/bc`` is not read as inside
    ``/a/b``. Either side missing is False — an unknown is never a containment."""
    if not inner or not outer:
        return False
    a, b = inner.rstrip("/"), outer.rstrip("/")
    return a == b or a.startswith(b + "/")


def residency(cgroup: str | None) -> dict:
    """What KIND of home this is, and therefore whose lifetime it borrows.

    ``lifetime`` is the field the verdict turns on: ``manager`` for a unit systemd forked
    and owns, ``caller`` for a scope built around processes it did not, ``unknown`` when
    there is nothing to read. No terminal is named here, and none needs to be."""
    if not cgroup:
        return {"leaf": None, "kind": "unreadable", "lifetime": "unknown",
                "under_user_manager": False}
    leaf = cgroup.rstrip("/").rsplit("/", 1)[-1]
    if leaf.endswith(".service"):
        kind, lifetime = "service", "manager"
    elif leaf.endswith(".scope"):
        kind, lifetime = "scope", "caller"
    elif leaf.endswith(".slice") or leaf in ("", "/"):
        # A bare slice (or the root) means nothing forked this process into a unit at all —
        # it inherited whatever its parent had. Not a caller's scope, but not owned either.
        kind, lifetime = "slice", "unknown"
    else:
        kind, lifetime = "other", "unknown"
    return {"leaf": leaf, "kind": kind, "lifetime": lifetime,
            "under_user_manager": f"/user@{os.getuid()}.service/" in cgroup + "/"}


def process_started_at(pid: int | str) -> float | None:
    """Wall-clock epoch seconds at which ``pid`` began — field 22 of ``/proc/<pid>/stat``
    (clock ticks since boot) against ``btime`` from ``/proc/stat``. Taken this way rather
    than from a stat() mtime because the loop's *start* is what dates it against the boot
    log, and a directory timestamp is a proxy for it rather than the thing."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        fields = raw[raw.rindex(")") + 2:].split()
        ticks = int(fields[19])
    except (OSError, ValueError, IndexError):
        return None
    btime = None
    try:
        for line in Path("/proc/stat").read_text().splitlines():
            if line.startswith("btime "):
                btime = int(line.split()[1])
                break
    except (OSError, ValueError):
        return None
    if btime is None:
        return None
    return btime + ticks / os.sysconf("SC_CLK_TCK")


def alive(pid: int | None) -> bool:
    return bool(pid) and Path(f"/proc/{pid}").exists()


# ── the survey ───────────────────────────────────────────────────────────────

def survey_pid(pid: int | str = "self", *, against: int | str | None = None) -> dict:
    """The residency reading for one pid — what the probe takes of itself every beat, and
    what the proof and the smoke surface take of anything they want to point it at.

    ``against`` names a second pid to compare with (the caller, in the proof's case), so
    the reading can say not merely "this is a scope" but "this is INSIDE that process's
    cgroup", which is the falsifier's own wording."""
    cg = cgroup_of(pid)
    out = {"pid": int(pid) if str(pid).isdigit() else os.getpid(),
           "cgroup": cg, **residency(cg)}
    if against is not None:
        other = cgroup_of(against)
        out["compared_to"] = {"pid": int(against) if str(against).isdigit() else None,
                              "cgroup": other,
                              "descendant_of_it": is_descendant(cg, other),
                              "same_as_it": bool(cg and other and cg.rstrip("/") == other.rstrip("/"))}
    return out


def _boot_log_path() -> Path:
    return Path(os.environ.get("CAIRN_LOGTARGET")
                or os.environ.get("CAIRN_BOOT_LOG")
                or resolve("instance/logs") / "boot")


def spawner_of(loop_started_at: float | None, *, boot_log: Path | None = None) -> dict:
    """WHICH LAUNCHER SPAWNED THIS LOOP, and is it still here?

    The boot log's every line carries ``<yyyymmdd.hhmmss>.<usec>.<pid>:`` — the launcher's
    own pid, which survives ``exec claude`` unchanged, so a dead pid there is a dead
    session. The spawner is the launcher whose ``ground_loop: spawn attempted`` line sits
    within ``_SPAWNER_WINDOW_S`` before this loop's start.

    ABSENT IS THE ORDINARY ANSWER, not a failure: a loop started by hand has no spawner
    line, and saying so is what keeps the watch standing instead of retiring on a witness
    it never saw."""
    path = Path(boot_log) if boot_log is not None else _boot_log_path()
    reading = {"boot_log": str(path), "loop_started_at": loop_started_at,
               "spawner_pid": None, "spawner_at": None, "spawner_alive": None,
               "lack": None}
    if loop_started_at is None:
        reading["lack"] = "the loop's own start time could not be read from /proc"
        return reading
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError as exc:
        reading["lack"] = f"no boot log to read at {path} ({type(exc).__name__})"
        return reading
    best = None
    for line in lines:
        m = _STAMP.match(line)
        if not m or "ground_loop: spawn attempted" not in m.group(5):
            continue
        try:
            when = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").timestamp()
        except ValueError:
            continue
        if loop_started_at - _SPAWNER_WINDOW_S <= when <= loop_started_at:
            if best is None or when >= best[0]:
                best = (when, int(m.group(4)))
    if best is None:
        reading["lack"] = ("no launcher spawn line within "
                           f"{_SPAWNER_WINDOW_S:.0f}s before this loop's start — it was "
                           "started by hand, or by something that does not log a boot line")
        return reading
    reading["spawner_at"], reading["spawner_pid"] = best[0], best[1]
    reading["spawner_alive"] = alive(best[1])
    return reading


def survey_the_record(pid: int | str = "self") -> dict:
    """Everything the judge needs, in one shape: where this process lives, when it
    started, and what became of whoever launched it."""
    real_pid = os.getpid() if pid == "self" else int(pid)
    started = process_started_at(real_pid)
    return {"residency": survey_pid(real_pid),
            "started_at": started,
            "uptime_s": (time.time() - started) if started else None,
            "spawner": spawner_of(started)}


# ── the judgement (pure — the proof feeds it fixtures) ───────────────────────

def judge(survey: dict) -> dict:
    """Verdict over a survey, with nothing read from the world. GREEN is manager-owned
    residency; RED is a caller's scope, which is the measured 2026-08-18 failure exactly;
    UNKNOWN is an unreadable or unowned home, and it is NOT green (Law 9 — red is the
    default and green is earned, so a home nobody could classify does not pass)."""
    res = survey.get("residency") or {}
    lifetime = res.get("lifetime")
    if lifetime == "manager":
        verdict = "GREEN"
        finding = (f"the heartbeat is in {res.get('leaf')}, a unit the user manager owns — "
                   "its lifetime is the manager's, not a window's")
    elif lifetime == "caller":
        verdict = "RED"
        finding = (f"the heartbeat is inside {res.get('leaf')}, a SCOPE — a cgroup built "
                   "around someone else's processes, which dies when they do. This is the "
                   "2026-08-18 failure standing again: the loop will go down with its caller")
    else:
        verdict = "UNKNOWN"
        finding = (f"the heartbeat's cgroup reads as {res.get('kind')} "
                   f"({res.get('cgroup')!r}) — nothing owns it, so nothing is promising to "
                   "keep it alive; unclassified is not green")
    sp = survey.get("spawner") or {}
    outlived = bool(sp.get("spawner_pid")) and sp.get("spawner_alive") is False
    return {"verdict": verdict, "finding": finding,
            "leaf": res.get("leaf"), "kind": res.get("kind"), "lifetime": lifetime,
            "cgroup": res.get("cgroup"),
            "under_user_manager": res.get("under_user_manager"),
            "uptime_s": survey.get("uptime_s"),
            "outlived_its_spawner": outlived,
            "spawner": sp}


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_record())


def _trigger(now, context: dict) -> bool:
    """TRUE when there is a finding worth a poke: the residency is not manager-owned (the
    defect is live), or the loop has just been measured outliving the launcher that
    spawned it (the intention working, which is the other half of the falsifier and the
    half nobody would otherwise ever record). Edge-triggered — ``while_true`` is left off,
    so a standing red pokes once per crossing rather than every beat forever."""
    j = _seen(context)
    return j["verdict"] != "GREEN" or j["outlived_its_spawner"]


def _enough(context: dict) -> bool:
    """CLEARED only by the second clause of the ticket's falsifier: a caller died and the
    heartbeat kept beating. Sitting in the right cgroup is what the launcher SAID; this is
    the watch confirming the parenting does what it is for. A red never clears — a watch
    that retires on the failure it watches for is the failure."""
    j = _seen(context)
    return j["verdict"] == "GREEN" and j["outlived_its_spawner"]


def _carry(context: dict) -> dict:
    j = _seen(context)
    return {
        "finding": j["finding"],
        "verdict": j["verdict"],
        "cgroup": j["cgroup"],
        "leaf": j["leaf"],
        "kind": j["kind"],
        "lifetime": j["lifetime"],
        "under_user_manager": j["under_user_manager"],
        "uptime_s": j["uptime_s"],
        "outlived_its_spawner": j["outlived_its_spawner"],
        "spawner": j["spawner"],
        "at": datetime.now(timezone.utc).astimezone().isoformat(),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the ticket's clause, verbatim: 'DONE when the loop, started through the "
            "launcher, sits in a cgroup that is neither the caller's nor a descendant of "
            "it — asked of the kernel, never read off the launcher's flags — AND survives "
            "its caller's entire process tree being killed.' Read `lifetime` for the first "
            "half and `outlived_its_spawner` for the second; a GREEN with "
            "outlived_its_spawner false has confirmed only what the launcher said."),
    }


PROBE = Probe(
    why="the heartbeat is the one resident process every callback in this system hangs "
        "off, and on 2026-08-18 it died inside a terminal's cgroup because setsid detaches "
        "a tty and not a cgroup — a launcher edited back, or a loop started by hand into "
        "the wrong home, would put that failure back in place with nothing loud about it, "
        "so the residency is read from the beating process itself every beat",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke surface: a named pid (or this process), and the live loop if there is one.
    # Pointing it at this session (which lives in a superclaude-*.scope) is how the red arm
    # is seen without waiting for the failure to happen again.
    #
    # THE ARGUMENT IS HONOURED OR THE KEY SAYS SO. Until 2026-08-18 this block took argv and
    # IGNORED it: `probe.py 574986` reported the interpreter's own cgroup under a heading that
    # read like an answer about 574986, and two runs against different pids came back
    # byte-identical. A surface that accepts a question and answers a different one is a
    # diagnostic surface lying quietly (Law 7), and it is worse than one that takes no
    # argument at all, because the reader has no way to notice.
    from cairn.devices.ground_loop.liveness import read_liveness

    _asked = sys.argv[1] if len(sys.argv) > 1 else None
    if _asked is not None:
        try:
            _subject: int | str = int(_asked)
        except ValueError:
            print(json.dumps({"lack": f"not a pid: {_asked!r}"}, indent=2))
            raise SystemExit(2)
    else:
        _subject = "self"
    out = {"pid_asked_about": _subject, "this_process": judge(survey_the_record(_subject))}
    live = read_liveness(datetime.now(timezone.utc).astimezone())
    loop_pid = (live.get("record") or {}).get("pid")
    if loop_pid:
        out["the_live_loop"] = judge(survey_the_record(loop_pid))
        out["the_live_loop"]["liveness_verdict"] = live.get("verdict")
        out["loop_inside_this_process_cgroup"] = is_descendant(
            cgroup_of(loop_pid), cgroup_of("self"))
    else:
        out["the_live_loop"] = {"lack": live.get("lack") or "no liveness record to read"}
    print(json.dumps(out, indent=2, default=str))

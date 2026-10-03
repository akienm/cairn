"""THE GROUND LOOP IS ONLY A HEARTBEAT — ticket bae622881f03 (Akien, 2026-09-30).

The whole of what the loop does, each clause a tooth:

  1. on start it records the mtimes of its own files;
  2. each beat it compares them; a change re-execs the loop in place, unless
     COMMAND_DO_NOT_RESTART is set; COMMAND_EXIT stops it;
  3. it calls every groundloop/pulse.py (class level and instance level) and lists
     the calls made this beat, a raising trigger listed with its error and the rest
     still called;
  4. it writes one JSON carrying the beat, the pid, the recorded and the current
     mtimes, and the triggers called;
  5. a second loop exits (3) while one runs and is LIVE.

And ticket a808e21d646f's clause 6, at this address because the beat record is this
component's: the record's state carries ``devices``, the rack's ids under its class root
(``cairn.tools.rack``) — a fixture rack of two folders, so neither a missing key nor a
constant reads green.

WHY TOOTH 1 READS THE REAL FOLDER. The old predicate (bytecode comparison, staleness.py)
called an untouched tree stale on Python 3.14 and restarted the loop 61 times. The new
predicate is an mtime compare, and the proof runs it over the loop's own real folder on
whatever interpreter runs the proof, which is the interpreter the loop runs on.

EVERYTHING ELSE RUNS AGAINST TEMP TREES. The runner is a subprocess with its instance root,
its class root, its watched folder and its cadence injected, so the live singleton's claim,
the live liveness record and the live pulse files are never touched. Touching the watched
folder of a fixture runner is what drives the restart teeth; the real loop's files are
never touched by this proof.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Clause keys follow the falsifier's (N) markers; (8) and (9) name what the builder_check's
# delete list and D4 required and the first falsifier text left unstated.
PROVES = {"bae622881f03": {
    "1": "an untouched folder reads unchanged",
    "2": "a changed own file re-execs the loop in place (same pid, new start)",
    "3": "with COMMAND_DO_NOT_RESTART a change is recorded and the loop stays",
    "4": "COMMAND_EXIT stops the loop cleanly",
    "5": "the triggers called this beat are listed, class and instance level",
    "6": "the record carries pid, last_run, and the heartbeat state",
    "7": "a second loop exits 3 while one runs and is LIVE",
    "8": "the loop carries no probes of its own",
    "9": "the charter describes only the heartbeat",
}, "a808e21d646f": {
    "6": "the beat record's device list is the rack",
}}
FAILURES: list[str] = []
CADENCE = 0.3   # the fixture runner's cadence; the live one is 60s


def ok(name: str, passed: bool, detail: str = "") -> None:
    # The detail rides its own unmarked line, so the marked line is the tooth's name alone and
    # a PROVES declaration can match it byte for byte (tmp paths and pids would not).
    print(f"  {'ok  ' if passed else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not passed:
        FAILURES.append(f"{name}: {detail}")


PULSE_OK = '''
from pathlib import Path
def on_pulse(now, context=None):
    p = Path(__file__).with_name("calls.txt")
    p.write_text(p.read_text() + "x" if p.exists() else "x")
    return {"called": True}
'''
PULSE_RAISES = '''
def on_pulse(now, context=None):
    raise RuntimeError("this trigger always raises")
'''


def _pulse_tree(td: Path) -> tuple[Path, Path]:
    """A class root with two devices (one good, one raising) and an instance home with one."""
    class_root = td / "class"
    inst_home = td / "inst" / "devices"
    for dev, body in (("alpha", PULSE_OK), ("broken", PULSE_RAISES)):
        d = class_root / "devices" / dev / "groundloop"
        d.mkdir(parents=True)
        (d / "pulse.py").write_text(body)
    d = inst_home / "beta" / "0" / "groundloop"
    d.mkdir(parents=True)
    (d / "pulse.py").write_text(PULSE_OK)
    return class_root, inst_home


def _now():
    return datetime.now(timezone.utc).astimezone()


def teeth_pure() -> None:
    try:
        from cairn.devices.cairn.machines.ground_loop import heartbeat as hb
    except ImportError as exc:
        ok("heartbeat module exists", False, f"{type(exc).__name__}: {exc}")
        return
    from cairn.devices.cairn.machines.ground_loop.discovery import pulse_sites

    # 1 — an untouched real folder never reads as changed, on this interpreter
    own = hb.own_files()
    first = hb.mtimes(own)
    second = hb.mtimes(hb.own_files())
    ok("the loop's own files are its folder's .py files",
       bool(own) and all(p.suffix == ".py" and p.parent == Path(hb.__file__).parent for p in own),
       f"{len(own)} files")
    ok("an untouched folder reads unchanged",
       hb.changed(first, second) == [],
       f"Python {sys.version.split()[0]}: {hb.changed(first, second)}")

    with tempfile.TemporaryDirectory(prefix="cairn-proof-heartbeat-pure-") as t:
        td = Path(t)
        w = td / "watch"
        w.mkdir()
        (w / "a.py").write_text("")
        (w / "b.py").write_text("")
        (w / "notes.txt").write_text("")
        rec = hb.mtimes(hb.own_files(w))
        ok("only .py files are watched", sorted(Path(k).name for k in rec) == ["a.py", "b.py"],
           str(sorted(rec)))
        t0 = os.stat(w / "a.py").st_mtime
        os.utime(w / "a.py", (t0 + 5, t0 + 5))
        ch = hb.changed(rec, hb.mtimes(hb.own_files(w)))
        ok("a touched file is named as changed", [Path(c).name for c in ch] == ["a.py"], str(ch))
        (w / "c.py").write_text("")
        (w / "b.py").unlink()
        ch = hb.changed(rec, hb.mtimes(hb.own_files(w)))
        ok("an added and a removed file are named too",
           sorted(Path(c).name for c in ch) == ["a.py", "b.py", "c.py"], str(ch))

        # 3 — every trigger called once, a raising one listed, the rest still called
        class_root, inst_home = _pulse_tree(td)
        sites = pulse_sites(class_root, inst_home)
        trig = hb.Triggers()
        calls = trig.fire(_now(), sites)
        by = {(c["device_id"], c["level"]): c for c in calls}
        ok("every pulse.py found is called and listed",
           set(by) == {("alpha", "class"), ("broken", "class"), ("beta", "instance")}, str(sorted(by)))
        ok("a raising trigger is listed with its error",
           by.get(("broken", "class"), {}).get("ok") is False
           and "always raises" in str(by.get(("broken", "class"), {}).get("error")),
           str(by.get(("broken", "class"))))
        ok("the others still ran and returned",
           by.get(("alpha", "class"), {}).get("ok") is True
           and by.get(("beta", "instance"), {}).get("result") == {"called": True},
           str(by.get(("alpha", "class"))))
        trig.fire(_now(), sites)
        n = (class_root / "devices" / "alpha" / "groundloop" / "calls.txt").read_text()
        ok("one call per trigger per beat", n == "xx", repr(n))


def _runner_src(td: Path, class_root: Path, watch: Path) -> str:
    return (
        "import sys; sys.path.insert(0, %r)\n"
        "from pathlib import Path\n"
        "from cairn.tools.base.address import ROOTS\n"
        "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
        "roots = dict(ROOTS); roots['instance'] = Path(%r)\n"
        "raise SystemExit(main(roots=roots, cadence=%r, watch=Path(%r), class_root=Path(%r)))\n"
        % (str(_REPO), str(td / "inst"), CADENCE, str(watch), str(class_root)))


def _home(td: Path) -> Path:
    return td / "inst" / "devices" / "cairn" / "0" / "machines" / "ground_loop"


def _record(td: Path) -> dict:
    try:
        return json.loads((_home(td) / "liveness.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _wait(pred, secs=30.0) -> bool:
    end = time.monotonic() + secs
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


def _spawn(src: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", src], cwd=str(_REPO),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                            env={**os.environ, "PYTHONPATH": str(_REPO)})


def teeth_runner() -> None:
    with tempfile.TemporaryDirectory(prefix="cairn-proof-heartbeat-runner-") as t:
        td = Path(t)
        class_root, _ = _pulse_tree(td)
        watch = td / "watch"
        watch.mkdir()
        (watch / "loop_file.py").write_text("")
        for dev in ("rack_one", "rack_two"):
            (class_root / "cairn" / "devices" / dev).mkdir(parents=True)
        src = _runner_src(td, class_root, watch)
        proc = _spawn(src)
        try:
            beating = _wait(lambda: _record(td).get("state", {}).get("beats", 0) >= 2)
            rec = _record(td)
            st = rec.get("state", {})
            ok("the runner beats and writes its record", beating and proc.poll() is None,
               f"beats={st.get('beats')} rc={proc.poll()}")
            if not beating:
                err = proc.stderr.read() if proc.poll() is not None else ""
                ok("runner alive for the remaining teeth", False, err[-400:])
                return
            want = {"beats", "started", "recorded_mtimes", "current_mtimes", "changed", "triggers"}
            ok("the record carries pid, last_run, and the heartbeat state",
               rec.get("pid") == proc.pid and "last_run" in rec and want <= set(st),
               f"missing={sorted(want - set(st))}")
            from cairn.tools.rack.rack import rack_ids
            want_rack = rack_ids(class_root)
            ok("the beat record's device list is the rack",
               st.get("devices") == want_rack == ["rack_one", "rack_two"],
               f"record devices={st.get('devices')} rack={want_rack}")
            ok("recorded and current mtimes name the watched file, unchanged",
               list(st.get("recorded_mtimes", {})) == [str(watch / "loop_file.py")]
               and st.get("changed") == [], f"changed={st.get('changed')}")
            listed = sorted((c.get("device_id"), c.get("ok")) for c in st.get("triggers", []))
            ok("the triggers called this beat are listed, class and instance level",
               listed == [("alpha", True), ("beta", True), ("broken", False)], str(listed))

            # 5 — a second loop exits 3 while this one is LIVE
            second = _spawn(src)
            try:
                rc = second.wait(timeout=30)
            except subprocess.TimeoutExpired:
                second.kill()
                rc = "still running"
            ok("a second loop exits 3 while one runs and is LIVE", rc == 3, f"rc={rc}")
            ok("the first loop is untouched by the second", proc.poll() is None)

            # 2b — COMMAND_DO_NOT_RESTART suppresses the restart but the change is recorded
            started = _record(td)["state"]["started"]
            (_home(td) / "COMMAND_DO_NOT_RESTART.flag").touch()
            t0 = os.stat(watch / "loop_file.py").st_mtime
            os.utime(watch / "loop_file.py", (t0 + 5, t0 + 5))
            seen = _wait(lambda: _record(td).get("state", {}).get("changed") == [str(watch / "loop_file.py")])
            time.sleep(CADENCE * 4)
            ok("with COMMAND_DO_NOT_RESTART a change is recorded and the loop stays",
               seen and _record(td)["state"]["started"] == started and proc.poll() is None,
               f"seen={seen} started_same={_record(td)['state']['started'] == started}")

            # 2a — without the flag, the change re-execs in place: same pid, new image
            (_home(td) / "COMMAND_DO_NOT_RESTART.flag").unlink()
            restarted = _wait(lambda: _record(td).get("state", {}).get("started") not in (None, started))
            rec = _record(td)
            ok("a changed own file re-execs the loop in place (same pid, new start)",
               restarted and rec.get("pid") == proc.pid and proc.poll() is None,
               f"restarted={restarted} pid={rec.get('pid')} vs {proc.pid}")
            ok("the new image records the new mtime as its baseline",
               _wait(lambda: _record(td).get("state", {}).get("changed") == [] and
                     _record(td).get("state", {}).get("beats", 0) >= 1),
               str(_record(td).get("state", {}).get("changed")))

            # 2c — COMMAND_EXIT stops it
            (_home(td) / "COMMAND_EXIT.flag").touch()
            try:
                rc = proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                rc = "still running"
            ok("COMMAND_EXIT stops the loop cleanly", rc == 0, f"rc={rc}")
            ok("the flag menu is laid out in flags/",
               sorted(p.name for p in (_home(td) / "flags").glob("*.flag"))
               == ["COMMAND_DO_NOT_RESTART.flag", "COMMAND_EXIT.flag"])
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=30)


def teeth_nothing_else() -> None:
    """The runner imports none of what the heartbeat no longer does."""
    src = (Path(__file__).resolve().parents[1] / "__main__.py").read_text()
    banned = ["bus.bus", "BusDevice", "staleness", "discover,", "arbitrate_newcomer"]
    hits = [b for b in banned if b in src]
    ok("the runner reaches no bus, no probe discovery, no bytecode staleness", not hits, str(hits))
    probes = Path(__file__).resolve().parents[1] / "probes"
    left = sorted(p.name for p in probes.glob("*.py")) if probes.is_dir() else []
    ok("the loop carries no probes of its own", not left, str(left))


def teeth_charter() -> None:
    """The charter says what the loop is now: it parses, cites this ticket, and no longer
    describes the roster/subscription/probe loop it replaced. (The build commit first landed
    it without its opening brace; nothing read it, so nothing noticed.)"""
    path = Path(__file__).resolve().parents[1] / "intention+why.json"
    try:
        what = json.loads(path.read_text(encoding="utf-8")).get("what", "")
    except (OSError, ValueError) as e:
        ok("the charter describes only the heartbeat", False, f"{type(e).__name__}: {e}")
        return
    stale = [w for w in ("roster()", "subscribed device", "PROBES") if w in what]
    ok("the charter describes only the heartbeat",
       "bae622881f03" in what and not stale, f"stale={stale}")


def main() -> int:
    print("the ground loop is only a heartbeat")
    teeth_pure()
    teeth_runner()
    teeth_nothing_else()
    teeth_charter()
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — mtimes, flags, triggers, one record, one loop. Nothing else.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

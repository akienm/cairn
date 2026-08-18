"""Proof: the heartbeat outlives its caller — asked of the kernel, not read off the flags.

THE FAILURE THIS GRIPS IS MEASURED, TO THE SECOND, ON 2026-08-18:

    14:57:31  the kernel oom-kills the claude binary (2.1.232, 12.4GB, CONSTRAINT_NONE)
    14:57:43  systemd: app-org.kde.konsole-b1d62b21….scope "Failed with result 'oom-kill'"
    14:52:55  ← the ground loop's previous start, from its own diagnostics trail
    14:58:01  ← the next one, and NOTHING between: the heartbeat went down in that scope

``setsid`` detaches a tty. It does not detach a cgroup. The spawn at
``launchers/superclaude`` said "so it outlives this shell and the terminal" in its own
comment and that sentence was true of the tty and false of the terminal, which is the
exact shape of a rule enforced by policy rather than by physics (Law 4).

THE FALSIFIER, verbatim from ticket ``the-heartbeat-outlives-its-caller``: "DONE when the
loop, started through the launcher, sits in a cgroup that is neither the caller's nor a
descendant of it — asked of the kernel, never read off the launcher's flags — AND survives
its caller's entire process tree being killed, with the loop's own trail showing an
unbroken run of beats across that kill, AND the losing-claimant refusal still lands in
~/.cairn/logs/ground_loop_nohup.log rather than only in the journal."

HOW THE KILL IS DONE, AND WHY IT IS NOT ``killpg``. The 2026-08-18 kill was a CGROUP kill:
systemd took the scope, and everything in the scope went with it. ``setsid`` already
leaves the caller's process GROUP, so a ``killpg`` would spare the loop today and this
proof would go green against the very defect it exists to catch — the hollow green that
is worse than a red (Law 8). So the caller is killed the way it actually died: every pid
listed in the caller's own ``cgroup.procs``.

AND THE CALLER IS A DISPOSABLE SCOPE THIS PROOF BUILDS. Driving the launcher straight
from a test process would put the spawned loop in the TESTER's cgroup, and killing that
cgroup would kill the session running the proof. Every drive therefore happens inside
``cairn-proof-caller-<n>.scope``, which is what gets killed.

EVERY ARM IS ISOLATED FROM THE LIVE SYSTEM: an isolated ``HOME`` (so the spawned loop
claims its own ``run.lock`` instead of losing to the resident one, and writes its own
liveness, nohup log and boot log), and a per-run unit name via
``SUPERCLAUDE_GROUND_LOOP_UNIT`` so the live ``cairn-ground-loop`` unit is never touched.

    python3 launchers/proofs/test_ground_loop_survives_its_caller.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))     # launchers/proofs -> repo root

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

# Resolved ONCE, before any arm hands a child a pruned PATH. The prime-directive arm makes
# systemd-run unreachable to the LAUNCHER, and an early version of that arm made it
# unreachable to this proof's own scope wrapper too — the isolation leaking one level up.
SYSTEMD_RUN = shutil.which("systemd-run") or "systemd-run"

REPO = Path(__file__).resolve().parents[2]
SUPERCLAUDE = REPO / "launchers" / "superclaude"

# THE PROBE IS THE READER, AND THE PROOF BORROWS IT — loaded by path exactly as
# test_reported_but_unfixed_probe.py loads its own floor. The cgroup parse exists once, in
# the instrument that ships with the thing it watches; a second spelling here would be the
# corpus growing two readers of /proc/*/cgroup, which criterion 7 of the chart forbids.
BERTH = REPO / "cairn" / "devices" / "ground_loop" / "probes" / "does_the_heartbeat_outlive_its_caller.py"
_spec = importlib.util.spec_from_file_location("_probe_heartbeat_residency", BERTH)
probe_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe_mod)

cgroup_of = probe_mod.cgroup_of
is_descendant = probe_mod.is_descendant
residency = probe_mod.residency
alive = probe_mod.alive

_SCRATCH = scratch_dir("cairn-proof-heartbeat-")
_UNITS: list[str] = []          # every transient unit this run created, cleaned at the end
_TAG = f"{os.getpid()}"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def _run(*argv: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout)


def _unit(kind: str, n: int) -> str:
    name = f"cairn-proof-{kind}-{_TAG}-{n}"
    _UNITS.append(name)
    return name


def _cleanup_units() -> None:
    for name in _UNITS:
        _run("systemctl", "--user", "stop", f"{name}.service", timeout=20)
        _run("systemctl", "--user", "reset-failed", f"{name}.service", timeout=20)
        _run("systemctl", "--user", "stop", f"{name}.scope", timeout=20)
        _run("systemctl", "--user", "reset-failed", f"{name}.scope", timeout=20)


def _cleanup_strays() -> int:
    """Kill any loop this run started that is not in a unit — the last sweep, by HOME.

    STOPPING THE UNITS IS NOT CLEANING UP, and that gap is measured rather than imagined.
    On 2026-08-18 the sibling A/B harness cleaned up with ``systemctl stop <unit>`` and leaked
    **14 ground loops** into the caller's own cgroup at ~64% of a core each (load average 18.7;
    the session scope fell 2.1G -> 454M when they were killed). The reason is the very defect
    under test here: the launcher's setsid fall-through creates NO unit, so there is no name to
    stop, and setsid leaves the loop in the caller's cgroup rather than anywhere findable.

    ``Drive.stop`` already covers the ordinary path twice (it kills the caller's whole cgroup,
    and it kills the pid in the liveness record). This is the sweep for what neither catches:
    a loop spawned but not yet far enough along to have written a liveness record when its
    drive was torn down. HOME is the identity, because every drive is handed an isolated one
    under ``_SCRATCH`` — so this can only ever match a process this run started.
    """
    killed = 0
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            cmd = (pid_dir / "cmdline").read_bytes()
            env_blob = (pid_dir / "environ").read_bytes()
        except OSError:
            continue
        if b"cairn.devices.ground_loop" not in cmd:
            continue
        if f"HOME={_SCRATCH}".encode() not in env_blob:
            continue
        try:
            os.kill(int(pid_dir.name), signal.SIGKILL)
            killed += 1
        except OSError:
            pass
    if killed:
        print(f"    swept {killed} stray loop(s) that no unit name could have reached")
    return killed


# ── the isolated world one drive of the launcher runs in ─────────────────────

_STAND_IN = """#!/usr/bin/env bash
echo "STAND_IN_REACHED argv=$*"
sleep %d
"""


def _path_without_systemd_run() -> str:
    """A PATH that has everything EXCEPT systemd-run, built once as a directory of symlinks.

    THE OBVIOUS SPELLING IS WRONG AND IT WAS MEASURED WRONG (take 2 of this proof, 16:20):
    dropping every PATH entry that contains ``systemd-run`` drops ``/usr/bin`` — and on this
    host ``/bin`` is a symlink to it — which leaves the launcher without ``script``, ``sed``,
    ``python3`` or anything else. The arm then fails for "no such file or directory" and
    reads exactly like the defect it was meant to measure. Isolation that removes the world
    is not isolation; it is a broken fixture wearing a red.

    So: one directory, one symlink per executable name on the real PATH, ``systemd-run``
    (and its siblings that would smuggle it back in) simply never linked.
    """
    shim = _SCRATCH / "path-without-systemd-run"
    shim.mkdir(exist_ok=True)
    withheld = {"systemd-run", "systemd-notify"}
    if not any(shim.iterdir()):
        for d in os.environ.get("PATH", "").split(":"):
            src = Path(d)
            if not src.is_dir():
                continue
            for entry in src.iterdir():
                if entry.name in withheld or (shim / entry.name).exists():
                    continue
                try:
                    (shim / entry.name).symlink_to(entry)
                except OSError:
                    pass
    # The withholding is a claim, so it is measured rather than asserted.
    assert shutil.which("systemd-run", path=str(shim)) is None, "the shim still reaches systemd-run"
    assert shutil.which("script", path=str(shim)), "the shim lost the rest of the world"
    return str(shim)


class Drive:
    """One end-to-end drive of the REAL launcher inside its own disposable caller scope."""

    def __init__(self, n: int, *, hold_s: int = 90, env_extra: dict[str, str] | None = None,
                 strip_systemd_run: bool = False, home: Path | None = None):
        self.n = n
        self.home = Path(home) if home is not None else (_SCRATCH / f"home-{n}")
        (self.home / ".cairn" / "logs").mkdir(parents=True, exist_ok=True)
        self.scope = _unit("caller", n) + ".scope"
        self.loop_unit = f"cairn-proof-loop-{_TAG}-{n}"
        _UNITS.append(self.loop_unit)
        self.stand_in = _SCRATCH / f"claude-stand-in-{n}"
        self.stand_in.write_text(_STAND_IN % hold_s)
        self.stand_in.chmod(0o755)
        self.out = _SCRATCH / f"drive-{n}.out"

        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["CLAUDE_BIN"] = str(self.stand_in)
        env["CAIRN_BOOT_LOG"] = str(self.home / ".cairn" / "logs" / "boot")
        env["CAIRN_LOGTARGET"] = env["CAIRN_BOOT_LOG"]
        # The launcher must not build a SECOND scope around the stand-in: the caller's
        # cgroup has to be one thing this proof can kill whole.
        env["SUPERCLAUDE_NO_SCOPE"] = "1"
        env["SUPERCLAUDE_GROUND_LOOP_UNIT"] = self.loop_unit
        if strip_systemd_run:
            # The prime-directive arm: make systemd-run genuinely unreachable rather than
            # asking the launcher to pretend it is.
            env["PATH"] = _path_without_systemd_run()
        env.update(env_extra or {})
        self.env = env
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        cmd = f"{SUPERCLAUDE} --no-preflight"
        fh = self.out.open("w")
        self.proc = subprocess.Popen(
            [SYSTEMD_RUN, "--user", "--scope", "--quiet", "--unit", self.scope,
             "--", "script", "-qec", cmd, "/dev/null"],
            stdout=fh, stderr=subprocess.STDOUT, env=self.env, cwd=str(REPO),
            start_new_session=True,
        )

    # — what the drive lets us read —

    @property
    def liveness(self) -> Path:
        return self.home / ".cairn" / "devices" / "ground_loop" / "0" / "liveness.json"

    @property
    def nohup(self) -> Path:
        return self.home / ".cairn" / "logs" / "ground_loop_nohup.log"

    @property
    def boot(self) -> Path:
        return self.home / ".cairn" / "logs" / "boot"

    def text(self) -> str:
        return self.out.read_text(errors="replace") if self.out.exists() else ""

    def caller_cgroup(self) -> str | None:
        return cgroup_of(self.proc.pid) if self.proc else None

    def wait_for_stand_in(self, timeout: float = 45) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if "STAND_IN_REACHED" in self.text():
                return True
            time.sleep(0.3)
        return False

    def wait_for_loop(self, timeout: float = 90) -> dict | None:
        end = time.time() + timeout
        while time.time() < end:
            try:
                return json.loads(self.liveness.read_text())
            except (OSError, ValueError):
                time.sleep(0.5)
        return None

    def kill_the_caller(self) -> list[int]:
        """Kill the caller the way it actually died: everything the caller's cgroup holds."""
        cg = self.caller_cgroup()
        killed: list[int] = []
        # THE SAFETY INTERLOCK, and it is not paranoia — it is the difference between this
        # proof and a proof that kills the session running it. If the disposable scope was
        # never created, the caller's cgroup IS the tester's cgroup, and the cgroup-wide
        # kill below would take this process, its terminal and everything beside it. So the
        # kill happens only into a cgroup whose leaf is the scope THIS drive asked for.
        if cg and cg.rstrip("/").rsplit("/", 1)[-1] != self.scope:
            print(f"    REFUSING the cgroup kill: caller sits in {cg!r}, not {self.scope!r}")
            cg = None
        if cg:
            procs = Path("/sys/fs/cgroup") / cg.lstrip("/") / "cgroup.procs"
            try:
                for line in procs.read_text().split():
                    pid = int(line)
                    if pid == os.getpid():
                        continue
                    os.kill(pid, signal.SIGKILL)
                    killed.append(pid)
            except (OSError, ValueError):
                pass
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except OSError:
                pass
        return killed

    def stop(self) -> None:
        self.kill_the_caller()
        _run("systemctl", "--user", "stop", self.loop_unit + ".service", timeout=20)
        try:
            rec = json.loads(self.liveness.read_text())
            if alive(rec.get("pid")):
                os.kill(rec["pid"], signal.SIGKILL)
        except (OSError, ValueError, KeyError):
            pass


# ── ARM 1+2 — the cgroup, and the survival ──────────────────────────────────

def arms_one_and_two() -> None:
    print("\nRESIDENCY AND SURVIVAL — the real launcher, a disposable caller, and the kernel")
    d = Drive(1)
    try:
        d.start()
        check("the launch reaches the binary at all (the prime directive)",
              d.wait_for_stand_in(), f"pty output: {d.text()[-300:]!r}")

        rec = d.wait_for_loop()
        check("a ground loop actually started and wrote its liveness record",
              bool(rec and rec.get("pid")), f"at {d.liveness}: {rec}")
        if not (rec and rec.get("pid")):
            return
        loop_pid = rec["pid"]
        loop_cg, caller_cg = cgroup_of(loop_pid), d.caller_cgroup()
        print(f"    loop pid {loop_pid}  cgroup {loop_cg}")
        print(f"    caller   {d.proc.pid}  cgroup {caller_cg}")

        check("the loop's cgroup is NOT the caller's, and not a descendant of it",
              bool(loop_cg) and not is_descendant(loop_cg, caller_cg),
              f"loop={loop_cg} caller={caller_cg}")
        res = residency(loop_cg)
        check("the loop sits in a unit the user manager OWNS, not a caller's scope",
              res["lifetime"] == "manager", f"{res}")

        beats_before = (rec.get("state") or {}).get("beats")
        killed = d.kill_the_caller()
        print(f"    killed the caller's whole cgroup: {killed}")
        time.sleep(2)
        check("the loop is still alive after its caller's entire cgroup was killed",
              alive(loop_pid), f"pid {loop_pid}")

        # The trail, not the process table: a live pid could be a wedged one.
        advanced, seen = False, None
        end = time.time() + 60
        while time.time() < end and not advanced:
            try:
                now = json.loads(d.liveness.read_text())
                seen = (now.get("state") or {}).get("beats")
                advanced = seen is not None and beats_before is not None and seen > beats_before
            except (OSError, ValueError):
                pass
            if not advanced:
                time.sleep(1)
        check("and its own trail shows beats CONTINUING across the kill",
              advanced, f"beats before={beats_before} after={seen}")
    finally:
        d.stop()


# ── ARM 3 — the unit name cannot wedge ──────────────────────────────────────

def arm_three_the_wedge() -> None:
    print("\nTHE WEDGE — a losing launch must not lock the unit name against every later one")
    print("    (the singleton loser exits 3 BY DESIGN; a nonzero exit leaves a transient")
    print("     unit loaded in `failed` state, holding its own name)")

    a = _unit("wedge-a", 1)
    _run("systemd-run", "--user", "--unit", a, "--quiet",
         "-p", "SuccessExitStatus=3", "--", "/bin/bash", "-c", "exit 3")
    time.sleep(1.5)
    failed = _run("systemctl", "--user", "is-failed", f"{a}.service")
    check("exit 3 under SuccessExitStatus=3 is not a failure",
          failed.returncode != 0, f"is-failed rc={failed.returncode} out={failed.stdout.strip()!r}")
    again = _run("systemd-run", "--user", "--unit", a, "--quiet",
                 "-p", "SuccessExitStatus=3", "--", "/bin/bash", "-c", "exit 3")
    check("and the name is free for the next launch", again.returncode == 0,
          f"rc={again.returncode} err={again.stderr.strip()!r}")
    time.sleep(1.5)

    b = _unit("wedge-b", 2)
    _run("systemd-run", "--user", "--unit", b, "--quiet", "--", "/bin/bash", "-c", "exit 9")
    time.sleep(1.5)
    blocked = _run("systemd-run", "--user", "--unit", b, "--quiet", "--", "/bin/true")
    check("a genuinely crashed unit DOES block its own name (why the clear is needed)",
          blocked.returncode != 0, f"rc={blocked.returncode} err={blocked.stderr.strip()!r}")
    cleared = _run("systemctl", "--user", "reset-failed", f"{b}.service")
    after = _run("systemd-run", "--user", "--unit", b, "--quiet", "--", "/bin/true")
    check("and a blind reset-failed frees it", after.returncode == 0,
          f"reset rc={cleared.returncode} restart rc={after.returncode} err={after.stderr.strip()!r}")

    c = _unit("wedge-c", 3)
    _run("systemd-run", "--user", "--unit", c, "--quiet", "--", "/bin/sleep", "120")
    time.sleep(1.5)
    before = _run("systemctl", "--user", "show", "-p", "MainPID", "--value", f"{c}.service")
    _run("systemctl", "--user", "reset-failed", f"{c}.service")
    time.sleep(0.5)
    now = _run("systemctl", "--user", "show", "-p", "MainPID", "--value", f"{c}.service")
    active = _run("systemctl", "--user", "is-active", f"{c}.service")
    check("reset-failed fired blind at a LIVE unit disturbs nothing",
          before.stdout.strip() == now.stdout.strip() and before.stdout.strip() not in ("", "0")
          and active.stdout.strip() == "active",
          f"MainPID {before.stdout.strip()!r} -> {now.stdout.strip()!r}, is-active={active.stdout.strip()!r}")
    _run("systemctl", "--user", "stop", f"{c}.service")


# ── ARM 4 — the refusal stays legible where a human reads it ────────────────

def arm_four_legibility() -> None:
    print("\nLEGIBILITY — both refusals land in the nohup log, not only in the journal")
    d = Drive(2, hold_s=45)
    try:
        d.start()
        d.wait_for_stand_in()
        rec = d.wait_for_loop()
        if not (rec and rec.get("pid")):
            check("a first loop is up so a second can lose to it", False, f"{rec}")
            return
        check("a first loop is up so a second can lose to it", True, f"pid {rec['pid']}")

        before = d.nohup.stat().st_size if d.nohup.exists() else -1
        second = Drive(3, hold_s=8, home=d.home)
        second.loop_unit = f"cairn-proof-loop-{_TAG}-3"
        second.env["SUPERCLAUDE_GROUND_LOOP_UNIT"] = second.loop_unit
        _UNITS.append(second.loop_unit)
        second.start()
        second.wait_for_stand_in()
        time.sleep(8)
        after = d.nohup.stat().st_size if d.nohup.exists() else -1
        text = d.nohup.read_text(errors="replace") if d.nohup.exists() else ""
        second.stop()
        # SIZE FIRST, ALWAYS. A grep over a file that never grew would pass on the text the
        # FIRST loop wrote — the whole-record substring read that goes green for the wrong
        # reason. The byte witness is what makes the grep mean something.
        check("the losing claimant's refusal GREW the nohup log",
              after > before >= 0, f"{before} -> {after} bytes at {d.nohup}")
        check("and the refusal names the claim, not a crash",
              bool(re.search(r"(?i)claim|singleton|already|refus", text[max(0, before - 200):])),
              f"tail: {text[-300:]!r}")

        # The name's refusal: pre-take the unit, then launch. systemd-run's own complaint
        # must reach the same file, or a launch that started nothing looks identical to one
        # that started something.
        taken = f"cairn-proof-loop-{_TAG}-4"
        _UNITS.append(taken)
        _run("systemd-run", "--user", "--unit", taken, "--quiet", "--", "/bin/sleep", "60")
        time.sleep(1)
        before2 = d.nohup.stat().st_size
        third = Drive(4, hold_s=8, home=d.home)
        third.loop_unit = taken
        third.env["SUPERCLAUDE_GROUND_LOOP_UNIT"] = taken
        third.start()
        third.wait_for_stand_in()
        time.sleep(4)
        after2 = d.nohup.stat().st_size
        tail = d.nohup.read_text(errors="replace")[before2:]
        third.stop()
        _run("systemctl", "--user", "stop", f"{taken}.service")
        check("a taken unit name also writes its refusal to the nohup log",
              after2 > before2 and bool(re.search(r"(?i)already|loaded|fragment|unit", tail)),
              f"{before2} -> {after2} bytes; tail={tail[-300:]!r}")
    finally:
        d.stop()


# ── ARM 5 — the prime directive outranks every bit of this ──────────────────

def arm_five_the_directive() -> None:
    print("\nTHE PRIME DIRECTIVE — from parse to exec, nothing may abort the launch")

    d = Drive(5, hold_s=6, strip_systemd_run=True)
    try:
        d.start()
        check("systemd-run unreachable: the launch still reaches the binary",
              d.wait_for_stand_in(), f"pty output: {d.text()[-300:]!r}")
        boot = d.boot.read_text(errors="replace") if d.boot.exists() else ""
        check("and the boot log carries the exec line",
              "exec:" in boot, f"boot log: {boot.strip()[-200:]!r}")
        check("and it SAYS which ground-loop path it took (Law 7 at a diagnostic surface)",
              "ground_loop:" in boot,
              next((l for l in boot.splitlines() if "ground_loop" in l), "<no ground_loop line>"))
    finally:
        d.stop()

    taken = f"cairn-proof-loop-{_TAG}-6"
    _UNITS.append(taken)
    _run("systemd-run", "--user", "--unit", taken, "--quiet", "--", "/bin/sleep", "60")
    e = Drive(6, hold_s=6)
    e.loop_unit = taken
    e.env["SUPERCLAUDE_GROUND_LOOP_UNIT"] = taken
    try:
        e.start()
        check("unit name already taken: the launch still reaches the binary",
              e.wait_for_stand_in(), f"pty output: {e.text()[-300:]!r}")
    finally:
        e.stop()
        _run("systemctl", "--user", "stop", f"{taken}.service")

    dry = subprocess.run([str(SUPERCLAUDE), "--dry-run", "--no-preflight"],
                         capture_output=True, text=True, timeout=60, cwd=str(REPO),
                         env={**os.environ, "CAIRN_BOOT_LOG": str(_SCRATCH / "dry-boot")})
    check("--dry-run still exits 0, prints its exec line and starts nothing",
          dry.returncode == 0 and "exec " in dry.stdout, f"rc={dry.returncode}")


# ── ARM 6 — one reader of /proc/*/cgroup in the whole corpus ────────────────

# EVERY MENTION OF THE PATH THAT IS NOT A PYTHON READ OF IT, DECLARED BY NAME WITH ITS
# REASON. A census that silently narrowed to "python reads" would go green while a second
# reader sat in a bash string three files away, which is the whole-record-substring shape of
# a check that passes for the wrong reason. So the census counts BOTH, and the second count
# is compared against this dict — a new entry anywhere reds until it is named here.
_DECLARED_MENTIONS = {
    "launchers/proofs/test_superclaude_memory_scope.py":
        "a bash one-liner (`cut -d: -f3 /proc/self/cgroup`) inside the stand-in that REPLACES "
        "the claude binary — it runs as the launched process, reporting its own cgroup from "
        "inside a scope this proof cannot enter, and it cannot import a python probe",
    "launchers/proofs/test_ground_loop_survives_its_caller.py":
        "this file: prose in the docstring and the census pattern itself; the read it uses "
        "is the probe's, imported at the top and asserted by the next check",
}


def arm_six_one_reader() -> None:
    print("\nONE READER — the cgroup parse exists once, and both consumers import it")
    hits = _run("grep", "-rn", "--include=*.py", r"/proc/[^\"']*cgroup", str(REPO)).stdout
    reads: set[str] = set()          # a python read: the path AND a call that opens it
    mentions: set[str] = set()       # everything else that spells the path at all
    for line in hits.splitlines():
        if not line.strip():
            continue
        path, _, text = line.split(":", 2)
        rel = str(Path(path).resolve().relative_to(REPO))
        (reads if re.search(r"read_text\(|open\(|readlines\(", text) else mentions).add(rel)
    mentions -= reads

    berth_rel = str(BERTH.resolve().relative_to(REPO))
    check("exactly one file READS /proc/<pid>/cgroup from python",
          reads == {berth_rel}, f"readers: {sorted(reads)}")

    undeclared = sorted(m for m in mentions if m not in _DECLARED_MENTIONS)
    check("and every other mention of the path is declared with its reason",
          not undeclared, f"undeclared: {undeclared}")
    stale = sorted(d for d in _DECLARED_MENTIONS if d not in mentions and d not in reads)
    check("no declared exemption has gone stale (it would be a licence nothing uses)",
          not stale, f"stale: {stale}")
    for m in sorted(mentions):
        print(f"    declared, not a python read: {m}")
        print(f"      because {_DECLARED_MENTIONS.get(m, '<UNDECLARED>')}")

    proof_src = Path(__file__).read_text()
    check("and this proof reaches it by importing the probe, not by re-spelling it",
          "spec_from_file_location" in proof_src and "cgroup_of = probe_mod" in proof_src)


def main() -> int:
    if not SUPERCLAUDE.exists():
        print(f"RED: no launcher at {SUPERCLAUDE}")
        return 1
    if _run("systemd-run", "--user", "--scope", "--quiet", "--", "true").returncode != 0:
        # Not a skip dressed as green (Law 9): this host is the one the incident happened on.
        print("RED: `systemd-run --user --scope` does not work here — the residency this")
        print("     proof grips cannot exist on this host, and that is a finding, not a skip.")
        return 1
    if not Path("/sys/fs/cgroup/cgroup.controllers").exists():
        print("RED: no cgroup v2 unified hierarchy — the reading this proof takes does not exist")
        return 1

    print(f"the heartbeat outlives its caller — scratch at {_SCRATCH}")
    try:
        arms_one_and_two()
        arm_three_the_wedge()
        arm_four_legibility()
        arm_five_the_directive()
        arm_six_one_reader()
    finally:
        _cleanup_units()
        _cleanup_strays()

    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — the heartbeat is the manager's, and it kept beating over its caller's grave.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

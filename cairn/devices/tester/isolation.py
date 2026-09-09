"""Isolation — the network the tester owns, so a build's reach is physics, not trust.

THE STONE, IN ONE SENTENCE: a run the tester supervises has **no ambient route** to a
constrained shared resource, and that seal is **measured from inside, never assumed**.

TWO SEALS LIVE HERE, and the stone was always big enough for both — it took a measured
failure to notice the second one was missing. The **network seal** (opt-in, ``isolation=
"netns"``) answers *what can this run REACH*. The **instance seal** (always on, no dial)
answers *what can this run LEAVE BEHIND*: instance-space is a constrained shared resource
like the inference slot, and a proof writing into the trail tree corrupts the instrument
every later measurement is taken from. Both are bwrap flags on one sandbox; both are probed
from inside with a control; both report the same four verdicts. Their section headers below
say which is which.

WHY THIS IS THE LOAD-BEARING HALF (measured in UU, 2026-07-13). Nine test runs shelled
on the host each drove live inference at a single shared slot; a policy ("don't hammer
the model", "run in series") binds only the consumers who *read* it, and the ones nobody
remembered to tell saturated the slot and wrote two false artifacts before the load was
traced back. Law 4: a rule that matters is enforced by physics, not policy. `--unshare-net`
binds every consumer, including the ones no one told — because the route is simply gone.

WHY THE SEAL IS MEASURED, NEVER ASSUMED. An isolation that merely *claims* to seal is one
more green light that means nothing — the exact defect the tester exists to kill (Law 8:
a proof a hollow build couldn't pass). A misconfigured, silently-downgraded, or
kernel-refused namespace looks EXACTLY like a working one until a socket opens. So every
sealed run PROBES ITS OWN SEAL FROM INSIDE, with a positive control run bare; a seal that
cannot be confirmed is INDETERMINATE (CP1: "I don't know" made structural — Law 3), and a
seal asked-for-but-breached is a measured RED, never a shrug.

FRESH design, mechanism grafted. The design — four seal verdicts mapped to CP1/Law 3, the
gate *owned by the tester* (MAP.md:333), the seal recorded inside the ratified VALIDATION
rather than a parallel record — is Cairn's, authored to Form v0. The OS plumbing (the
`bwrap --unshare-net --cap-add CAP_NET_ADMIN` flag string, the inside-probe, the
`available()` apparmor check) crosses nearly literally from UU's isolation.py, because it
is kernel truth, not a design Cairn replaced.

DEFERRED, filed not faked (the programmable-network pillar, pulled by real need — Law 1):
UU's netpolicy Router (claim an address and BE the dependency; serve a FIXTURE; REFUSE
with an nftables reject+counter so a 3-millisecond connection cannot be missed; FORWARD
over a Unix socket to keep Postgres's auth path intact). The seal here is "no route." The
Router is "a *chosen* route" — grown when db_domain pulls FORWARD and inference_domain
pulls FIXTURE/REFUSE. This module claims only the seal it can measure today.

    T-tester-owns-the-network (Cairn: MAP.md:333, build step MAP.md:888).
"""

from __future__ import annotations

import atexit
import errno
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from cairn.tools.base.address import ROOTS

# The seal's four honest verdicts.
SEALED = "sealed"                # asked for, confirmed from inside: no route.
OPEN = "open"                    # not asked for; the route is open by construction, said so.
INDETERMINATE = "indeterminate"  # asked for, could not be confirmed — CP1, and never GREEN.
BREACHED = "breached"            # asked for, the route is STILL there — a measured failure (RED).

# The probe's baseline: a near-universally reachable off-host route. The seal question is
# "can a sealed run reach *anything* off this host?", not "is one named host up?" — so a
# generic public route is a stronger, host-agnostic control than a specific dependency's
# address (which UU hard-coded to its inference slot). No packet's payload matters; only
# whether the kernel has a route at all.
DEFAULT_PROBE_TARGET = ("1.1.1.1", 53)

# The inside-probe. Printed tokens, classified by errno so we distinguish "no route at all"
# (the seal worked) from "reached the host, port said no" (a route exists — NOT sealed).
# A refusal proves a route as surely as a success does; only ENETUNREACH-family errors mean
# the route itself is gone, which is exactly what --unshare-net produces.
_PROBE = (
    "import socket,sys,errno\n"
    "try:\n"
    "    socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=3).close()\n"
    "    print('ROUTE')\n"
    "except OSError as e:\n"
    "    no_route = (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN)\n"
    "    print('NOROUTE' if e.errno in no_route else\n"
    "          'ROUTE' if e.errno == errno.ECONNREFUSED else\n"
    "          f'ERR:{e.errno}')\n"
)


@dataclass(frozen=True)
class Seal:
    """Did this run actually lose its route to the forbidden resource? Measured, from inside."""

    verdict: str
    detail: str

    @property
    def sealed(self) -> bool:
        return self.verdict == SEALED

    @property
    def trustworthy(self) -> bool:
        """A verdict may be trusted only if the seal is a definite state — SEALED or a
        deliberately-named OPEN. INDETERMINATE and BREACHED both mean 'do not call this
        green on the strength of its isolation' (Law 8 / CP1)."""
        return self.verdict in (SEALED, OPEN)


def _classify(out: str) -> str:
    """Reduce a probe's stdout to 'route' | 'noroute' | 'error'."""
    token = (out or "").strip().splitlines()[-1] if (out or "").strip() else ""
    if token == "ROUTE":
        return "route"
    if token == "NOROUTE":
        return "noroute"
    return "error"  # ERR:<errno>, a timeout, an empty line — ambiguous, so we do not guess


# ── the SECOND seal: instance-space ──────────────────────────────────────────
#
# THE NETWORK SEAL ABOVE ASKS "what can this run REACH". This one asks "what can this run
# LEAVE BEHIND", and it exists because the second question went unasked for six weeks while
# the first was carefully answered.
#
# MEASURED, TWICE, AND THE SECOND TIME AT CORPUS SCALE:
#   - 2026-08-14  test_askscan fired the live prebuild hook with the caller's HOME. 15 of the
#                 production ledger's first 19 rows were written by the proof — a question no
#                 transcript contains, inflating the instrument's own denominator 4.75x while
#                 looking exactly like evidence.
#   - 2026-08-18  every device now emits its trail unwired (ticket a-device-logs-without-being-
#                 wired), so ~/.cairn/logs/ filled with 2,080 records across eight devices. All
#                 of it spanned SEVENTEEN MINUTES: the window of two corpus runs. The tree built
#                 to show what the system did showed only what the tester did.
#
# Both are one defect: A PROOF CANNOT SEED THE TREE IT READS. The trail is a record of truth
# (Law 7), and the tester is the one process that runs every component in the corpus — so if
# proofs write there, the instrument is dominated by its own exhaust and no measurement of the
# system's behaviour can be taken from it.
#
# THE SEAL IS A SNAPSHOT, NOT AN EMPTY ROOM, and that distinction is the whole design. The
# first build bound an EMPTY directory over the instance root and turned SEVEN proofs red —
# not from pollution, but because they read the live corpus and *honestly refuse to go green
# over an empty one*:
#
#     read ZERO standing decompose berths at ~/.cairn/devices/chart — an invariant over an
#     empty corpus is a hollow green, and this assertion is the thing that says so out loud
#                                                    (build_inspector/proofs/test_inspector.py)
#
# Those proofs are RIGHT, and an isolation that breaks them is measuring the wrong thing.
# READS ARE NOT THE DEFECT — writes are. So the swap is a full copy of the live instance root
# taken at run time: every read answers exactly as it would on the host, and every write lands
# in the copy and is discarded. Measured 2026-08-18: 872 files, 49 MB, 0.12s per proof (~15s
# across the 126-proof corpus, ~3%), and it took the seven reds back to zero.
#
# VENVS ARE BOUND BACK, NOT COPIED, and this is not an optimisation — it is correctness twice
# over. The interpreter running the subject LIVES in instance-space on this box
# (~/.cairn/venv), so binding a copy over the root would swap python out from under a running
# exec; and ~/.cairn/devices/aider_shim/0/venv is a second one, which the first build silently
# dropped and thereby reded 28 of aider_shim's teeth. A venv is an INSTALLED INTERPRETER, not
# state — reproducible from its build() — so it is bound read-only at its own address. They
# are found by PEP 405's own definition (a directory holding ``pyvenv.cfg``), never by a
# hard-coded roster: the second one was found by a red, and a third would be found the same
# way if the roster were a list someone had to remember to extend.
_INSTANCE_ROOT = str(ROOTS["instance"])
_seal_counter = itertools.count()

# The inside-probe, same discipline as the network one: PRINTED TOKENS, classified out here.
# It reports what it can SEE and whether it could WRITE, because the seal has to be confirmed
# in both directions — a swap that lost the reads is as broken as one that leaked the writes.
#
# THE ROOT IS PASSED IN, not re-derived from ``Path.home()`` inside the probe. It looks like the
# same value and it usually is; what it is NOT is the same STATEMENT. The classifier out here
# judges "did the write land in the live root or the swap?" against ``_INSTANCE_ROOT``, and a
# probe deriving its own answer can disagree with the judge silently — which it did, the first
# time this seal's own positive control ran against a fake root: the probe wrote its marker into
# the REAL ~/.cairn while the classifier looked for it in the fake one and reported
# INDETERMINATE. An isolation whose self-test leaks is the joke version of an isolation. One
# statement of the root, made where the verdict is made.
_INSTANCE_PROBE = (
    "import sys, pathlib\n"
    "root = pathlib.Path(sys.argv[1])\n"
    "seen = sorted(p.name for p in root.iterdir()) if root.is_dir() else []\n"
    "print('SEES:' + ','.join(seen))\n"
    "marker = root / sys.argv[2]\n"
    "try:\n"
    "    marker.write_text('instance-seal probe')\n"
    "    print('WROTE')\n"
    "except OSError as e:\n"
    "    print(f'WRITEFAIL:{e.errno}')\n"
)


def bwrap_available() -> tuple[bool, str]:
    """Can this host build ANY bubblewrap sandbox? Shared by both seals, because both are
    bwrap and a host that cannot build one cannot build the other — two copies of this check
    would be two things to keep in agreement for no gain (Law 1)."""
    if not shutil.which("bwrap"):
        return False, "bubblewrap (bwrap) is not installed"
    try:
        with open("/proc/sys/kernel/apparmor_restrict_unprivileged_userns") as fh:
            if fh.read().strip() == "1":
                return False, (
                    "kernel.apparmor_restrict_unprivileged_userns=1 — unprivileged user "
                    "namespaces are blocked, so bwrap cannot build a sandbox "
                    "(fix: sysctl -w kernel.apparmor_restrict_unprivileged_userns=0)"
                )
    except FileNotFoundError:
        pass  # not an Ubuntu-24.04-style kernel; the live probe is the real check either way
    return True, "bwrap present, unprivileged user namespaces permitted"


# The one directory a snapshot deliberately arrives EMPTY, and it is 73% of the copy.
# Measured 2026-09-08: the live instance root is 424M on disk across 81,599 entries, and
# ~/.cairn/logs is 311M of it — the trail tree, which is append-only exhaust that every
# device writes and no proof reads the CONTENTS of. Two proofs walk it and both want it
# empty: test_device_logs_unwired takes a before/after witness (66,739 files, and the
# quadratic diff over them is what pushed that proof past the tester's 120s window on
# 2026-09-08), and test_instance_seal excludes the logs tree from its "no file was added"
# tooth by hand. An empty writable directory answers both honestly and costs nothing to
# copy. The DIRECTORY still exists in the swap, because check_instance_seal requires the
# subject to see every live top-level name — blinding a read is the failure mode this
# whole seal already learned once (see the seven reds above).
_LOGS = "logs"


def _skip_venv_contents(directory: str, names: list[str]) -> set:
    """copytree's ignore hook: skip a venv's CONTENTS, keep the empty directory.

    The directory has to survive so the read-only bind has a mount point to land on. PEP 405
    says a venv is a directory containing ``pyvenv.cfg``, so that is the test — the definition
    itself, not a name match, because "venv" is a convention and ``pyvenv.cfg`` is the spec.
    """
    return set(names) if "pyvenv.cfg" in names else set()


def _snapshot_ignore(directory: str, names: list[str]) -> set:
    """The snapshot's ignore hook: venv contents (above) AND the logs tree's contents.

    Two skips, one hook, because copytree takes exactly one. The logs test is an ADDRESS
    match, not a name match: only the instance root's own ``logs/`` is emptied, so a device
    that happens to keep a directory called ``logs`` deeper in the tree still gets copied.
    """
    if "pyvenv.cfg" in names:
        return set(names)
    if Path(directory) == Path(_INSTANCE_ROOT) / _LOGS:
        return set(names)
    return set()


def venvs_under_instance_space() -> list[str]:
    """Every venv in instance-space, discovered by PEP 405, newest scan each call.

    Not cached and not a constant: a venv appears the first time a device builds one (this is
    exactly how aider_shim's arrived), and a roster fixed at import would be stale precisely
    when a new device is being brought up — the moment its proofs matter most.
    """
    root = Path(_INSTANCE_ROOT)
    if not root.is_dir():
        return []
    return [str(cfg.parent) for cfg in sorted(root.rglob("pyvenv.cfg"))]


_SEAL_PREFIX = "cairn-instance-seal-"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # someone else's live process
    return True


def _sweep_orphaned_snapshots(tmp: str | None = None) -> list[str]:
    """Remove every ``cairn-instance-{seal,pristine}-<pid>-*`` under the temp root whose pid
    is dead, and every legacy one that carries no pid at all (nothing alive can own those —
    the naming that would have said so did not exist when they were made). Returns what it
    removed. Never raises: a sweep that fails is a leak that lives one snapshot longer,
    which is the state before this function existed, not a reason to refuse a proof.

    BOTH PREFIXES, because there are now two lifetimes here and only one sweeper. A seal
    copy dies with its proof; a pristine copy dies with the batch. A sweeper that knew only
    the first would leave the larger, longer-lived one to accumulate — which is the exact
    shape of the leak this function was written for (57 copies, 7.7G, 2026-09-05).
    """
    root = Path(tmp or tempfile.gettempdir())
    removed: list[str] = []
    for prefix in (_SEAL_PREFIX, _PRISTINE_PREFIX):
        try:
            candidates = list(root.glob(f"{prefix}*"))
        except OSError:
            continue
        for d in candidates:
            tail = d.name[len(prefix):]
            head = tail.split("-", 1)[0]
            if head.isdigit() and _pid_alive(int(head)):
                continue
            shutil.rmtree(d, ignore_errors=True)
            removed.append(str(d))
    return removed


# ── the batch snapshot: the live root is read ONCE, not once per proof ───────
#
# MEASURED 2026-09-06 and again 2026-09-08: every sealed run copied the live instance root
# TWICE (one swap for the seal's own probe, one for the subject) — 424M and 4.6s apiece, so
# ~850M and ~9s of pure copying per proof, before the proof ran a single tooth. A 93-proof
# re-seal sweep moved ~79G to prove code that had not changed, and /tmp is a tmpfs on this
# box, so those bytes are RAM.
#
# THE SHAPE OF THE FIX IS A CACHE WITH AN HONEST INVALIDATION. One PRISTINE copy is taken
# per process — a ``--seal`` batch is one process, which is why "per batch" needs no flag,
# no context manager and no caller who remembers (Law 4: the guarantee is physics, not a
# convention). Each proof's private world is then copied from the pristine rather than from
# the live tree: same bytes, but the 81,599-entry walk of the real ~/.cairn happens once.
#
# WHAT THE CACHE MAY NOT DO IS GO STALE WITHOUT SAYING SO. The live root moves while a batch
# runs (the ground loop and sudo_relay are daemons; the tester itself logs). Almost all of
# that movement is INSIDE the tree and harmless to a snapshot — but a NEW TOP-LEVEL ENTRY is
# not: ``check_instance_seal`` refuses a swap that cannot show every live top-level name, so
# a stale pristine would turn every later proof in the batch INDETERMINATE. So the top-level
# set is the invalidation key, re-read on every call (one ``iterdir`` of six entries), and a
# change rebuilds the pristine. It fails toward a fresh copy, never toward a wrong one.
#
# REFLINK IS ASKED FOR AND IS NOT AVAILABLE HERE, and saying so is the point (Law 3).
# ``cp -a --reflink=auto`` shares blocks where the filesystem can and falls back to a real
# copy where it cannot. Measured on this host 2026-09-08: ``/`` is ext4 and ``/tmp`` is
# tmpfs, and neither supports reflinks — so today the flag buys nothing and the per-proof
# copy is a true copy. It is written this way because the flag costs nothing, the fallback
# is exactly what we would have done by hand, and the day this box gets btrfs or XFS the
# per-proof cost goes to near zero with no code change. A copy-on-write MOUNT (bubblewrap
# overlay) is the other answer and is out of this ticket's bounds: bwrap 0.9.0 here has no
# ``--overlay``.
_PRISTINE_PREFIX = "cairn-instance-pristine-"
_pristine: dict = {"dir": None, "top": None, "builds": 0, "reuses": 0}
_pristine_atexit_armed = False


def _live_top_level() -> list[str]:
    """The live instance root's top-level names — the pristine cache's invalidation key."""
    root = Path(_INSTANCE_ROOT)
    try:
        return sorted(p.name for p in root.iterdir())
    except OSError:
        return []


def _drop_pristine() -> None:
    """Remove this process's pristine copy. Registered with atexit ONCE, and never raises."""
    d = _pristine.get("dir")
    if d:
        shutil.rmtree(Path(d).parent, ignore_errors=True)
        _pristine["dir"] = _pristine["top"] = None


def pristine_snapshot() -> str:
    """The batch's ONE copy of the live instance root, built on first use and reused after.

    Rebuilt only if the live root's top-level set has moved under it (see above) or if the
    copy has vanished. The caller does NOT own it and must not remove it — it is swept at
    process exit, and by the next process's ``_sweep_orphaned_snapshots``.
    """
    global _pristine_atexit_armed
    top = _live_top_level()
    d = _pristine.get("dir")
    if d and Path(d).is_dir() and _pristine.get("top") == top:
        _pristine["reuses"] += 1
        return str(d)
    if d:
        shutil.rmtree(Path(d).parent, ignore_errors=True)
    dst = Path(tempfile.mkdtemp(prefix=f"{_PRISTINE_PREFIX}{os.getpid()}-")) / "cairn"
    shutil.copytree(_INSTANCE_ROOT, dst, ignore=_snapshot_ignore,
                    symlinks=True, ignore_dangling_symlinks=True)
    _pristine["dir"], _pristine["top"] = str(dst), top
    _pristine["builds"] += 1
    if not _pristine_atexit_armed:
        atexit.register(_drop_pristine)
        _pristine_atexit_armed = True
    return str(dst)


def pristine_stats() -> dict:
    """How many times this process has READ the live root, and how many times it reused it.

    This is the falsifier's own instrument for "a batch of N proofs copies ~/.cairn once":
    it rides into every seal's evidence, so the claim is read off the record rather than
    off this docstring.
    """
    return {"builds": _pristine["builds"], "reuses": _pristine["reuses"]}


def snapshot_instance_space() -> str:
    """A proof's private copy of the instance root, made from the batch's pristine snapshot.

    The caller owns the directory and must remove it. Returns the SWAP ROOT — what gets bound
    over ``~/.cairn`` — so the address inside the sandbox is byte-identical to the real one
    and nothing a subject computes can tell the difference except by writing.

    THE OWNER'S PID IS IN THE NAME, AND THE DEAD ARE SWEPT ON THE NEXT SNAPSHOT. Measured
    2026-09-05: 57 of these at ~270M each had filled /tmp to 7.7G. Every caller removes its
    own in a ``finally`` — and a ``finally`` never runs for a process that is SIGKILLed or
    SIGTERMed mid-copy, which is what a caller's ``timeout`` does to a slow proof. So the
    copy names its owner, and the next snapshot (the one event that is guaranteed to happen
    before the disk matters again — no clock, no daemon) removes every sibling whose owner
    is no longer a live process. A live owner's copy is never touched: two testers may run
    at once.
    """
    _sweep_orphaned_snapshots()
    src = pristine_snapshot()
    swap = Path(tempfile.mkdtemp(prefix=f"{_SEAL_PREFIX}{os.getpid()}-")) / "cairn"
    r = subprocess.run(["cp", "-a", "--reflink=auto", src, str(swap)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        # LOUD, and it takes the run down. A half-copied swap is worse than no swap: the
        # subject would read a world with holes in it and the seal would call the missing
        # reads a blinding. Law 7 — the notary's own failure is not a thing to paper over.
        shutil.rmtree(swap.parent, ignore_errors=True)
        raise OSError(f"could not copy the pristine snapshot {src} -> {swap}: "
                      f"cp exited {r.returncode}: {r.stderr.strip()}")
    return str(swap)


def instance_bind_flags(swap_root: str) -> list[str]:
    """The bwrap flags that put ``swap_root`` where ``~/.cairn`` was, venvs bound back.

    Order matters and is load-bearing: the swap goes down FIRST, then each venv is bound back
    on top of the empty directory the snapshot left for it. bwrap resolves each SRC against the
    host root and applies mounts in sequence, so a later bind can land inside an earlier one.
    """
    flags = ["--bind", swap_root, _INSTANCE_ROOT]
    for venv in venvs_under_instance_space():
        flags += ["--ro-bind", venv, venv]
    return flags


def check_instance_seal(iso: Isolation, swap_root: str, cwd: str) -> Seal:
    """Measure the instance seal from inside, with a control — never assumed.

    THE CONTROL COSTS NO WRITE, and that is a deliberate improvement on the network probe's
    shape. That one has to open a socket bare to prove the seal removed something; here the
    control is a READ the tester takes in its own process, because the tester itself runs
    unsealed — so "what does the live root hold" is answered without touching it. An
    instrument that had to dirty the store to prove it was not dirtying the store would be
    the joke version of this seal.

    Three conditions, and all three must hold:
      1. the subject SEES the live world (the snapshot carried the reads across);
      2. the subject CAN write (a write that merely failed proves nothing about where it
         would have gone);
      3. what it wrote is in the SWAP and is NOT in the live root.
    Anything else is INDETERMINATE — and a marker that reaches the live root is BREACHED,
    which is the one outcome this whole module exists to make impossible to miss.
    """
    live = Path(_INSTANCE_ROOT)
    control = sorted(p.name for p in live.iterdir()) if live.is_dir() else []
    if not control:
        return Seal(INDETERMINATE, f"the live instance root {live} is empty or absent — there "
                                   f"is nothing a seal could be shown to have swapped; CP1")

    marker = f"instance-seal-probe-{os.getpid()}-{next(_seal_counter)}"
    argv = iso.wrap([sys.executable, "-c", _INSTANCE_PROBE, _INSTANCE_ROOT, marker], cwd,
                    instance_swap=swap_root)
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=30, cwd=cwd).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Seal(INDETERMINATE, f"instance-seal probe did not run: {type(exc).__name__}")

    seen = next((ln[5:].split(",") for ln in out.splitlines() if ln.startswith("SEES:")), None)
    wrote = "WROTE" in out.splitlines()

    # WHERE THE MARKER LANDED IS READ ONCE, HERE, AND THEN THE PROBE REMOVES ITS OWN EXHAUST
    # FROM THE SWAP. Until 2026-09-08 the exhaust was avoided by taking a SECOND full copy of
    # the instance root purely for the probe to dirty — 424M and 4.6s so that one 20-byte
    # marker would not show up in the subject's `wrote_to_instance` reading. That is the right
    # instinct (an instrument must not contaminate its own reading) paying an absurd price for
    # it. The marker's name is ours, known exactly, and unlinking it is the same guarantee for
    # nothing: the caller takes its before-manifest after this call returns, so a removed
    # marker is in neither side of the comparison, and a removal that FAILED leaves the marker
    # in the before-manifest too — where it also cannot read as a write. Both ways are safe,
    # which is why the failure is swallowed rather than raised.
    in_swap = (Path(swap_root) / marker).exists()
    in_live = (live / marker).exists()
    try:
        (Path(swap_root) / marker).unlink()
    except OSError:
        pass

    if in_live:
        return Seal(BREACHED, f"the probe's marker {marker!r} landed in the LIVE instance root "
                              f"{live} — the seal did NOT hold, and a proof can seed the tree "
                              f"it reads (RED)")
    if seen is None:
        return Seal(INDETERMINATE, f"probe gave no readable SEES line (got {out.strip()!r})")
    if not wrote:
        fail = next((ln for ln in out.splitlines() if ln.startswith("WRITEFAIL")), "no WROTE line")
        return Seal(INDETERMINATE, f"the probe could not write inside the seal ({fail}) — a "
                                   f"write that never happened says nothing about where it "
                                   f"would have landed; CP1")
    if not in_swap:
        return Seal(INDETERMINATE, f"the probe reported WROTE but {marker!r} is in neither the "
                                   f"live root nor the swap {swap_root} — the write went "
                                   f"somewhere unaccounted for, so nothing is confirmed")
    missing = sorted(set(control) - set(seen))
    if missing:
        return Seal(INDETERMINATE, f"the swap did not carry the reads across — the live root "
                                   f"holds {missing} that the subject cannot see. Reads are not "
                                   f"the defect this seal is for; blinding them turns honest "
                                   f"invariants into hollow greens")
    return Seal(SEALED, f"writes land in {swap_root} and not in {live}; all {len(control)} "
                        f"live top-level entries remain readable — seeded nothing, read "
                        f"everything")


class Isolation(ABC):
    """A way to run a command such that it cannot reach what it must not reach."""

    name: str = "abstract"
    seals_network: bool = False

    @abstractmethod
    def wrap(self, argv: list[str], cwd: str, *, instance_swap: str | None = None) -> list[str]:
        """Return ``argv`` wrapped in this isolation.

        ``instance_swap`` is ORTHOGONAL to the network seal and is carried by every subclass
        including ``NoIsolation``: "no network isolation" was never meant to say "free to
        write into the live instance root", and the day those two were the same dial is the
        day 2,080 records of proof exhaust filled the trail tree.
        """

    def available(self) -> tuple[bool, str]:
        return True, "always available"

    def _run_probe(self, argv: list[str], cwd: str) -> str:
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=30, cwd=cwd)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return f"probe-failed:{type(exc).__name__}"
        return r.stdout

    def check_seal(self, cwd: str, target: tuple[str, int] = DEFAULT_PROBE_TARGET) -> Seal:
        """Probe from inside, with a bare positive control, and return a measured verdict.

        This is not ceremony. An isolation that is misconfigured, silently downgraded, or
        running on a kernel that refuses the namespace looks EXACTLY like one that works —
        until a socket opens. The only way to know is to try, from inside, every time.
        """
        host, port = target
        probe = ["python3", "-c", _PROBE, host, str(port)]

        if not self.seals_network:
            return Seal(OPEN, f"{self.name}: no seal requested — the route is open by construction, and the record says so")

        control = _classify(self._run_probe(probe, cwd))
        if control != "route":
            return Seal(
                INDETERMINATE,
                f"no baseline route to {host}:{port} bare (got {control!r}); "
                f"cannot prove the seal removed anything — CP1, so not green",
            )

        inside = _classify(self._run_probe(self.wrap(probe, cwd), cwd))
        if inside == "noroute":
            return Seal(SEALED, f"{host}:{port} reachable bare, unreachable inside {self.name} — the seal removes the route")
        if inside == "route":
            return Seal(BREACHED, f"{host}:{port} is STILL reachable inside {self.name} — the seal did NOT hold (RED)")
        return Seal(INDETERMINATE, f"seal probe gave no clear verdict inside {self.name} (got {inside!r}) — CP1")


class NoIsolation(Isolation):
    """A bare host subprocess — no seal at all, and you must ASK for it by name.

    Kept only so that "unisolated" is a thing one requests deliberately and the tester can
    hand back a verdict that says, in the record, that nothing was sealed. An unnamed
    default is how host-shelling keeps happening without anyone deciding to do it.
    """

    name = "none"
    seals_network = False

    def wrap(self, argv: list[str], cwd: str, *, instance_swap: str | None = None) -> list[str]:
        if instance_swap is None:
            return list(argv)
        # Bare of the NETWORK seal, still sealed against instance-space: this is the ordinary
        # case, since the tester's default is unsealed-network and every proof gets the
        # instance seal. --chdir is required here for the same reason it is under netns — the
        # subject's cwd must be its own directory inside the namespace, not the namespace root.
        return (["bwrap", "--dev-bind", "/", "/"] + instance_bind_flags(instance_swap)
                + ["--chdir", cwd] + list(argv))


class NetnsIsolation(Isolation):
    """bubblewrap ``--unshare-net``: a fresh network namespace with no route anywhere.

    Rootless (unprivileged user namespaces), daemonless, sub-second. ``--dev-bind / /``
    keeps the whole filesystem intact — including any Unix socket, which is a file and not
    the network, so it survives the seal (the asymmetry a later FORWARD path will lean on).
    ``--cap-add CAP_NET_ADMIN`` lets a run configure the netns it already owns (what a later
    Router needs to claim an address); without it the namespace is merely dark, which is all
    the seal itself requires.

    ``available()`` reports the real reason the seal cannot be built rather than degrading
    quietly to running on the host — a sandbox that cannot be built must say so loudly.
    """

    name = "netns"
    seals_network = True

    def available(self) -> tuple[bool, str]:
        return bwrap_available()

    def wrap(self, argv: list[str], cwd: str, *, instance_swap: str | None = None) -> list[str]:
        # We deliberately do NOT pass --uid 0: the capability works at our real uid, and
        # becoming root-in-namespace breaks uid-matched services (e.g. Postgres peer auth).
        # Least privilege here is not hygiene, it is correctness — a grader that breaks the
        # thing it observes is worse than no grader.
        flags = ["bwrap", "--dev-bind", "/", "/", "--unshare-net", "--cap-add", "CAP_NET_ADMIN"]
        if instance_swap is not None:
            # ONE sandbox carrying both seals, never a sandbox inside a sandbox: they are
            # flags on the same bwrap, so composing them costs nothing and nesting would cost
            # a second namespace whose failure modes nobody has measured.
            flags += instance_bind_flags(instance_swap)
        return flags + ["--chdir", cwd] + list(argv)


def get_isolation(name: str) -> Isolation:
    if name in ("netns", "seal"):
        return NetnsIsolation()
    if name in ("none", ""):
        return NoIsolation()
    raise ValueError(f"unknown isolation {name!r} — expected 'netns' or 'none'")

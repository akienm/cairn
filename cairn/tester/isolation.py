"""Isolation — the network the tester owns, so a build's reach is physics, not trust.

THE STONE, IN ONE SENTENCE: a run the tester supervises has **no ambient route** to a
constrained shared resource, and that seal is **measured from inside, never assumed**.

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

import errno
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass

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


class Isolation(ABC):
    """A way to run a command such that it cannot reach what it must not reach."""

    name: str = "abstract"
    seals_network: bool = False

    @abstractmethod
    def wrap(self, argv: list[str], cwd: str) -> list[str]:
        """Return ``argv`` wrapped in this isolation."""

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

    def wrap(self, argv: list[str], cwd: str) -> list[str]:
        return list(argv)


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
        if not shutil.which("bwrap"):
            return False, "bubblewrap (bwrap) is not installed — cannot build a network namespace"
        try:
            with open("/proc/sys/kernel/apparmor_restrict_unprivileged_userns") as fh:
                if fh.read().strip() == "1":
                    return False, (
                        "kernel.apparmor_restrict_unprivileged_userns=1 — unprivileged user "
                        "namespaces are blocked, so bwrap cannot create a network namespace "
                        "(fix: sysctl -w kernel.apparmor_restrict_unprivileged_userns=0)"
                    )
        except FileNotFoundError:
            pass  # not an Ubuntu-24.04-style kernel; check_seal's live probe is the real check
        return True, "bwrap present, unprivileged user namespaces permitted"

    def wrap(self, argv: list[str], cwd: str) -> list[str]:
        # We deliberately do NOT pass --uid 0: the capability works at our real uid, and
        # becoming root-in-namespace breaks uid-matched services (e.g. Postgres peer auth).
        # Least privilege here is not hygiene, it is correctness — a grader that breaks the
        # thing it observes is worse than no grader.
        return [
            "bwrap", "--dev-bind", "/", "/", "--unshare-net",
            "--cap-add", "CAP_NET_ADMIN",
            "--chdir", cwd,
        ] + list(argv)


def get_isolation(name: str) -> Isolation:
    if name in ("netns", "seal"):
        return NetnsIsolation()
    if name in ("none", ""):
        return NoIsolation()
    raise ValueError(f"unknown isolation {name!r} — expected 'netns' or 'none'")

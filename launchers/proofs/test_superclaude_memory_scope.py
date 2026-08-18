"""Proof: a runaway Claude Code session dies ALONE, and superclaude is what makes that true.

THE FAILURE THIS GRIPS IS MEASURED, THREE TIMES, IN THE KERNEL LOG. Claude Code grew to
~12-14GB anon RSS on a 15GB box and the kernel took the whole machine's biggest process:

    2026-08-11 13:36  pid  98105 (2.1.226)  anon-rss 13.7GB
    2026-08-13 15:35  pid 516164 (2.1.229)  anon-rss 12.5GB
    2026-08-18 14:57  pid 251468 (2.1.232)  anon-rss 12.4GB

All three were GLOBAL (``constraint=CONSTRAINT_NONE``), and a global kill does not stop at
the offender: systemd marked the enclosing Konsole scope ``Failed with result 'oom-kill'``
and its siblings went too. On the third one that included the running ``sudo_relay`` — the
live root window — and Akien's report was "the whole terminal including the sudo relay were
gone." The session dying is survivable; the terminal and the privileged daemon dying with it
is the defect.

THE FALSIFIER: "a session that balloons can still take processes down with it that are not
the session." Two halves, and the second is the one a hollow build fails.

  - MECHANISM, on a synthetic balloon: a scope with a real limit contains its own runaway
    (``CONSTRAINT_MEMCG``), the balloon dies, and THIS process — the sibling standing in for
    the terminal and the relay — is still here afterwards. Plus the arm that makes it
    non-hollow: the SAME cap with swap left unbounded does NOT contain, which is exactly the
    trap the first attempt at this fix walked into (a 100M MemoryMax sailed past 400MB into
    swap). A build that set MemoryMax alone would pass a proof that only checked MemoryMax.

  - IN SITU, against the real launcher: superclaude is driven end-to-end through a pty with
    a stand-in CLAUDE_BIN, and the launched process reports its own cgroup's three limits.
    Reading the script for the flags would be structure standing in for behaviour; this runs
    it and asks the kernel.

AND THE PRIME DIRECTIVE IS ITSELF A CLAUSE. "From parse to exec, nothing may abort the
launch" outranks the cap: if the scope is declined or unavailable the launch still reaches
Claude, unbounded, and SAYS SO in the boot log. A cap that could strand Akien without a
session on a broken box would be a worse defect than the one it fixes.

    python3 launchers/proofs/test_superclaude_memory_scope.py     # exit 0 = green
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))     # launchers/proofs -> repo root

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SUPERCLAUDE = REPO / "launchers" / "superclaude"

# Every reach into the system temp directory goes through scratch_dir (its own docstring says
# why), and the boot log is redirected out of ~/.cairn so a proof run never becomes evidence
# about a launch — the contamination test_reported_but_unfixed_probe.py found the hard way.
_SCRATCH = scratch_dir("cairn-proof-memscope-")
_PROOF_BOOT_LOG = str(_SCRATCH / "boot")

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{name}: {detail}")


def _env(**extra: str) -> dict[str, str]:
    e = dict(os.environ)
    e["CAIRN_BOOT_LOG"] = _PROOF_BOOT_LOG
    e.update(extra)
    return e


# ── the synthetic balloon ────────────────────────────────────────────────────
# Touches every page it allocates: an untouched bytearray can sit in the allocator without
# ever charging the cgroup, which would make a green here mean nothing.
_BALLOON = (
    "b=[]\n"
    "for i in range(400):\n"
    "    p=bytearray(1024*1024)\n"
    "    for j in range(0,1024*1024,4096): p[j]=1\n"
    "    b.append(p)\n"
    "print('REACHED', len(b))\n"
)


def _run_ballooned(limits: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemd-run", "--user", "--scope", "--quiet", *limits, "--", sys.executable, "-c", _BALLOON],
        capture_output=True, text=True, timeout=120, env=_env(),
    )


def half_one_mechanism() -> None:
    print("\nMECHANISM — a limited scope contains its own runaway, and only its own")

    capped = _run_ballooned(["-p", "MemoryMax=100M", "-p", "MemorySwapMax=0"])
    check(
        "a 100M scope with swap capped kills the balloon",
        "REACHED" not in capped.stdout,
        f"stdout={capped.stdout.strip()!r} rc={capped.returncode}",
    )
    # The whole point: the sibling is still standing. This process IS the terminal and the
    # relay for the purposes of this proof, and on 2026-08-18 the equivalent of it died.
    check(
        "the sibling that did not balloon is still alive",
        os.getpid() > 0 and Path(f"/proc/{os.getpid()}").exists(),
        f"pid {os.getpid()}",
    )

    # THE NON-HOLLOW ARM. Same limit, swap left alone. If this ever starts containing too,
    # the swap cap has become belt-and-braces rather than load-bearing and this proof should
    # be re-read — but today it is the difference between a cap and a cap that works.
    unswapped = _run_ballooned(["-p", "MemoryMax=100M"])
    check(
        "the same cap WITHOUT MemorySwapMax does not contain (why the swap limit is not optional)",
        "REACHED" in unswapped.stdout,
        f"stdout={unswapped.stdout.strip()!r} rc={unswapped.returncode}",
    )


# ── in situ ──────────────────────────────────────────────────────────────────
_REPORTER = """#!/usr/bin/env bash
cg=$(cut -d: -f3 /proc/self/cgroup)
echo "CGROUP=$cg"
echo "MAX=$(cat /sys/fs/cgroup${cg}/memory.max 2>/dev/null)"
echo "HIGH=$(cat /sys/fs/cgroup${cg}/memory.high 2>/dev/null)"
echo "SWAP=$(cat /sys/fs/cgroup${cg}/memory.swap.max 2>/dev/null)"
echo "ARGV=$*"
"""


def _launch(extra_env: dict[str, str]) -> str:
    """Drive the REAL superclaude through a pty, with a stand-in for the claude binary.

    A pty because that is how it is launched, and because a scope that broke the terminal
    would be a defect this proof exists to catch.
    """
    stand_in = _SCRATCH / "claude-stand-in"
    stand_in.write_text(_REPORTER)
    stand_in.chmod(0o755)
    env = _env(CLAUDE_BIN=str(stand_in), **extra_env)
    cmd = f"{SUPERCLAUDE} --no-preflight"
    out = subprocess.run(
        ["script", "-qec", cmd, "/dev/null"],
        capture_output=True, text=True, timeout=120, env=env, cwd=str(REPO),
    )
    return out.stdout


def _limits(report: str) -> dict[str, str]:
    return dict(re.findall(r"^(CGROUP|MAX|HIGH|SWAP|ARGV)=(.*)$", report, re.M))


def half_two_in_situ() -> None:
    print("\nIN SITU — the real launcher, driven through a pty, asked of the kernel")

    got = _limits(_launch({}))
    check("the launch reaches the binary at all (the prime directive)", "ARGV" in got, repr(got))
    check(
        "the launched process sits in a superclaude scope, not the terminal's",
        got.get("CGROUP", "").rstrip("/").split("/")[-1].startswith("superclaude-"),
        got.get("CGROUP", "<none>"),
    )
    for key, label in (("MAX", "MemoryMax"), ("HIGH", "MemoryHigh"), ("SWAP", "MemorySwapMax")):
        v = got.get(key, "")
        check(
            f"{label} is a finite limit on the launched process",
            v.isdigit() and int(v) > 0,
            f"{key}={v!r}",
        )
    # Ordering is the whole design: High throttles before Max kills, so a runaway goes
    # visibly slow before it dies. Reversed, the soft limit would never be reached.
    if all(got.get(k, "").isdigit() for k in ("MAX", "HIGH")):
        check(
            "MemoryHigh sits BELOW MemoryMax (throttle before kill)",
            int(got["HIGH"]) < int(got["MAX"]),
            f"high={got['HIGH']} max={got['MAX']}",
        )
    # Bounded well under this host: a cap above the observed 12.4GB blowup would never fire.
    if got.get("MAX", "").isdigit():
        check(
            "the cap is below the smallest measured blowup (12.4GB, 2026-08-18)",
            int(got["MAX"]) < 12_427_624 * 1024,
            f"max={int(got['MAX'])/2**30:.1f}GiB",
        )


def half_three_the_directive_outranks_the_cap() -> None:
    print("\nTHE PRIME DIRECTIVE — declining or losing the scope costs the launch nothing")

    got = _limits(_launch({"SUPERCLAUDE_NO_SCOPE": "1"}))
    check("SUPERCLAUDE_NO_SCOPE still reaches the binary", "ARGV" in got, repr(got))
    check(
        "and it launches OUTSIDE a superclaude scope",
        not got.get("CGROUP", "").rstrip("/").split("/")[-1].startswith("superclaude-"),
        got.get("CGROUP", "<none>"),
    )
    # Law 7 at a diagnostic surface: unbounded is a real risk and the log says which of the
    # two reasons it was. "declined" and "unavailable" are different facts about the host.
    log = Path(_PROOF_BOOT_LOG).read_text() if Path(_PROOF_BOOT_LOG).exists() else ""
    check(
        "the boot log names the unbounded launch, and says it was DECLINED not unavailable",
        "scope: declined by SUPERCLAUDE_NO_SCOPE" in log,
        "last line: " + (log.strip().splitlines() or ["<empty>"])[-1],
    )
    check(
        "a scoped launch says so too, with its limits",
        re.search(r"scope: MemoryHigh=\S+ MemoryMax=\S+ MemorySwapMax=\S+", log) is not None,
        next((l for l in log.splitlines() if "scope: Memory" in l), "NO scope: line in the boot log"),
    )

    # --dry-run is not a launch: it must print the plain exec line and start nothing.
    dry = subprocess.run(
        [str(SUPERCLAUDE), "--dry-run", "--no-preflight"],
        capture_output=True, text=True, timeout=60, env=_env(), cwd=str(REPO),
    )
    check("--dry-run still exits 0 and prints its exec line", dry.returncode == 0 and "exec " in dry.stdout,
          f"rc={dry.returncode}")


def main() -> int:
    if not SUPERCLAUDE.exists():
        print(f"RED: no launcher at {SUPERCLAUDE}")
        return 1
    have_systemd_run = subprocess.run(
        ["systemd-run", "--user", "--scope", "--quiet", "--", "true"],
        capture_output=True, text=True,
    ).returncode == 0
    if not have_systemd_run:
        # Not a skip dressed as green (Law 9): this host is the one the incidents happened on.
        print("RED: `systemd-run --user --scope` does not work here — the containment this")
        print("     proof grips cannot exist on this host, and that is a finding, not a skip.")
        return 1

    print(f"superclaude memory scope — boot log redirected to {_PROOF_BOOT_LOG}")
    half_one_mechanism()
    half_two_in_situ()
    half_three_the_directive_outranks_the_cap()

    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — a runaway session dies alone, and the launch is still unstoppable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

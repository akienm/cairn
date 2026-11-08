"""guard — the atomic single-start claim (ticket an-entry-point-starts-the-loop-only-once).

READ-THEN-ACT IS NOT ATOMIC. Two entry points can both find no loop inside the same instant
and both start one — the falsifier's expensive direction (every callback fires twice). So
starting is decided by ONE syscall, not by a read: ``claim_singleton`` takes an exclusive,
non-blocking lock on a stable lock file in the loop's own device space, and exactly one
claimant wins. The lock itself is the base tool ``cairn/tools/base/singleton.py`` (ticket
6208d0a27d6e), so a shim can ask ``held`` without importing this device (RULE 1).

WHY A SEPARATE FILE AND NOT THE RECORD: the record (beat.json) is rewritten atomically every
beat via ``os.replace``, which swaps the inode out from under any held lock. The lock file
(``run.lock``) is never replaced, so the winner's claim rides one inode for the process's
whole life.

THE LOCK DECIDES; THE RECORD EXPLAINS. A losing claimant reads the record only to name what
is running (its pid); its refusal never rests on that read, and it never signals the holder
(Q#53: no takeover). A loop alive-but-slow still holds its lock, so no second loop starts.
"""

from __future__ import annotations

from pathlib import Path

from cairn.tools.base.singleton import Claim, ClaimRefused, claim, held as _held

LOCK_NAME = "run.lock"

SingletonClaim = Claim

__all__ = ["LOCK_NAME", "ClaimRefused", "SingletonClaim", "claim_singleton", "held"]


def claim_singleton(home: Path) -> Claim:
    """ONE atomic claim on the loop's own device space; win or refuse loudly, never block.
    Hold the returned claim for the process's whole life — the runner's release is its death."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    return claim(home / LOCK_NAME)


def held(home: Path) -> bool:
    """Is a loop holding the claim in ``home``? Asking creates nothing."""
    return _held(Path(home) / LOCK_NAME)

"""Proof for ticket 8902708b6212 — only a bare ``cairn sudorelay`` acquires root.

Measured 2026-10-11: ``cairn sudorelay --help`` started the privileged daemon, because
daemon.main() ran run() for every argument except --status. Root never enters this test:
``daemon.run`` is replaced with a stand-in that raises, so reaching it is the reading.

Teeth a hollow main could not pass:
  1. --help / -h (any case — system words fold) print the usage and exit 0, never reaching run.
  2. an unknown argument names itself on stderr and exits 2, never reaching run.
  3. a bare call still reaches run — the fix did not close the one door that should open.

    python3 cairn/devices/sudo_relay/proofs/test_only_a_bare_call_acquires_root.py   # exit 0 = green
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.sudo_relay import daemon  # noqa: E402

PROVES = {
    "8902708b6212": {
        "1": "test_help_prints_usage_and_starts_nothing",
        "2": "test_an_unknown_argument_refuses_and_starts_nothing",
        "3": "test_a_bare_call_still_starts_the_daemon",
    },
}


class _RunReached(AssertionError):
    pass


def _call(argv: list) -> tuple:
    """main(argv) with run() replaced by a tripwire; returns (rc or _RunReached, stdout, stderr)."""
    real = daemon.run

    def tripwire():
        raise _RunReached("run reached")

    daemon.run = tripwire
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = daemon.main(argv)
            except _RunReached as e:
                rc = e
    finally:
        daemon.run = real
    return rc, out.getvalue(), err.getvalue()


def test_help_prints_usage_and_starts_nothing():
    for word in ("--help", "-h", "--HELP"):
        rc, out, _ = _call([word])
        assert not isinstance(rc, _RunReached), f"{word} reached run() — it would acquire root"
        assert rc == 0, f"{word} exited {rc}, want 0"
        assert "usage: cairn sudorelay" in out, f"{word} printed no usage: {out!r}"


def test_an_unknown_argument_refuses_and_starts_nothing():
    rc, _, err = _call(["--bogus"])
    assert not isinstance(rc, _RunReached), "--bogus reached run() — a typo would acquire root"
    assert rc == 2, f"--bogus exited {rc}, want 2"
    assert "'--bogus'" in err and "usage: cairn sudorelay" in err, f"refusal did not name the word: {err!r}"


def test_a_bare_call_still_starts_the_daemon():
    rc, _, _ = _call([])
    assert isinstance(rc, _RunReached), f"a bare call returned {rc} without reaching run()"


def _main() -> int:
    checks = [test_help_prints_usage_and_starts_nothing,
              test_an_unknown_argument_refuses_and_starts_nothing,
              test_a_bare_call_still_starts_the_daemon]
    failed = 0
    for check in checks:
        try:
            check()
        except Exception as e:  # noqa: BLE001 — a tooth's failure is its reading, printed whole
            failed += 1
            print(f"  FAILED  {check.__name__}: {type(e).__name__}: {e}")
        else:
            print(f"  PASS  {check.__name__}")
    if failed:
        print(f"red — sudorelay args: {failed} of {len(checks)} teeth failed")
        return 1
    print("green — sudorelay: only a bare call acquires root; --help prints usage, an unknown word refuses")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""The sudo_relay daemon — the one privileged process, and the only thing Akien starts.

This is the thin wrapper the proof cannot exercise (it needs a password/TTY). Every piece
of logic UNDER it — the protocol, the audit record, retention, the expiry decision, the
visible status — lives in ``relay.py`` and is proven green without root. Here we only:

  1. acquire sudo ONCE (Akien's password act = his consent),
  2. keep it warm while work is happening,
  3. run each pending command as root via ``relay.root_executor`` (the injected seam),
  4. keep the root-holding WINDOW VISIBLE (heartbeat ``daemon.status``), and
  5. RELEASE root (``sudo -k``) the moment we go idle, hit the absolute cap, or exit.

Start it:   python3 cairn/sudo_relay/daemon.py
Watch it:   python3 cairn/sudo_relay/daemon.py --status
Stop it:    Ctrl-C  (releases root immediately)

Consent model (as in the UU relay it replaces): running this IS the approval. The daemon
stores no credential; when it exits, root is gone.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Run directly as a script (Akien: `python3 cairn/sudo_relay/daemon.py`) — put the repo
# root on the path so `cairn` imports. daemon.py is at cairn/sudo_relay/daemon.py, so the
# repo root is parents[2] (the proofs, one level deeper, use parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.sudo_relay import relay

_POLL_S = 2.0
_KEEPALIVE_EVERY_S = 60.0


def _say(msg: str) -> None:
    print(f"[sudo_relay] {datetime.now().isoformat(timespec='seconds')}  {msg}", flush=True)


def _acquire_sudo() -> bool:
    """One interactive ``sudo -v`` — prompts Akien for his password on the terminal, once."""
    return subprocess.run(["sudo", "-v"]).returncode == 0


def _keepalive() -> bool:
    """Refresh the sudo timestamp non-interactively; False if it has lapsed (we then exit)."""
    return subprocess.run(["sudo", "-n", "-v"], capture_output=True).returncode == 0


def _release() -> None:
    subprocess.run(["sudo", "-k"], capture_output=True)


def _print_status() -> int:
    s = relay.daemon_status()
    if not s.get("live"):
        _say(f"no live daemon — {s.get('reason', 'not running')}")
        return 1
    _say(
        f"live (pid {s['pid']}) — up since {s['started_at']}; "
        f"hard-expires {s['hard_expires_at']}; idle-expires {s['idle_expires_at']}"
    )
    return 0


def run() -> int:
    idir = relay.instance_dir()
    relay._ensure(relay.relay_dir(), relay.audit_dir())
    pid = os.getpid()

    _say(f"starting — instance {idir}")
    _say(
        f"root window: idle {relay.DEFAULT_IDLE_TIMEOUT_S}s / hard cap "
        f"{relay.DEFAULT_MAX_LIFETIME_S}s (both visible in daemon.status)"
    )
    if not _acquire_sudo():
        _say("sudo auth failed — exiting, no root acquired")
        return 1

    started = datetime.now()
    last_activity = started
    last_keepalive = time.monotonic()

    def _cleanup(*_a) -> None:
        _say("exiting — releasing root (sudo -k)")
        _release()
        relay.clear_status()
        _say("root released.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    now = started
    relay.write_status(pid=pid, started_at=started, last_activity=last_activity, now=now)
    hard_expires = started + timedelta(seconds=relay.DEFAULT_MAX_LIFETIME_S)
    _say(f"root acquired. window is VISIBLE — hard-expires {hard_expires.isoformat(timespec='seconds')}. "
         f"Ctrl-C to release now.")

    try:
        while True:
            time.sleep(_POLL_S)
            now = datetime.now()

            expire, why = relay.should_expire(started, last_activity, now)
            if expire:
                _say(f"releasing root — {why}")
                break

            if time.monotonic() - last_keepalive >= _KEEPALIVE_EVERY_S:
                if not _keepalive():
                    _say("sudo lapsed (keepalive failed) — releasing and exiting")
                    break
                last_keepalive = time.monotonic()
                relay.write_status(pid=pid, started_at=started, last_activity=last_activity, now=now)

            record = relay.process_pending(relay.root_executor, now=now)
            if record is not None:
                last_activity = now
                relay.write_status(pid=pid, started_at=started, last_activity=last_activity, now=now)
                rc = record["returncode"]
                _say(f"ran command → exit {rc}; audited {record['id']}")
    finally:
        _release()
        relay.clear_status()
        _say("root released.")
    return 0


def main(argv: list | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--status":
        return _print_status()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())

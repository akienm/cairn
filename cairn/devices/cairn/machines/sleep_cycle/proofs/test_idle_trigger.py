"""PROOF — the cairn device starts a sleep cycle after the idle threshold, and never while active.

Ticket 9b6b392ebcfe (idle-detection-trigger). The falsifier is unnumbered, so this proof
declares ONE composite tooth against clause ``all``; it runs the narrow teeth below end to end,
and each prints its own PASS/FAIL so a red names its piece:

  (a) quiet past the threshold everywhere → the pulse asks for one mint and records it;
  (b) a human turn in a transcript ten minutes old → not due, nothing asked;
  (c) a transcript holding only peer and task-notification turns is not activity;
  (d) a web_server ``serve`` record, a librarian ``chat`` record and a terminal's atime each
      hold sleep on their own;
  (e) a second pulse in the same quiet spell asks nothing; fresh activity then a new quiet
      spell asks again;
  (f) a source that cannot be read is named ``unread`` and holds sleep — never silence;
  (g) inside an away window sleep is due at once, over activity a minute old; clearing the
      window removes away.json, through the device's ``away`` verb;
  (h) the threshold is a parameter: the same quiet is due under 1h and not under 3h, and the
      device's settings carry 3h with its provenance;
  (i) ``python3 -m cairn.devices.cairn pulse`` under a scratch HOME writes its decision record
      and, with no transcripts folder there, names cc unread and asks nothing.

What a hollow build cannot pass (Law 8): without ``idle.py`` every tooth fails to import its
subject; a ``pulse`` that always mints reds (b)(d)(e)(f); one that never mints reds (a)(g); one
that counts every transcript turn reds (c); one that reads a missing source as silence reds (f);
a ``device.py`` without the ``away`` verb or the settings reds (g)(h); no ``__main__.py`` reds (i).

THE WORLD IS A FIXTURE: a temp roots table, a temp transcripts tree, a temp terminal folder whose
atimes are set by ``os.utime``, and an injected asker standing in for the ``sleep-cycle`` verb —
it records the call and writes the closed cycle an empty-roster mint would. Nothing here touches
``~/.cairn``, ``~/.claude`` or a bus.

    python3 cairn/devices/cairn/machines/sleep_cycle/proofs/test_idle_trigger.py   # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# One clause, one declarable tooth (proof_coverage: an unnumbered falsifier is clause "all").
PROVES = {
    "9b6b392ebcfe": {
        "all": "test_the_cairn_device_sleeps_after_quiet_and_never_while_active",
    },
}

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
H = timedelta(hours=1)


class _World:
    """One fixture world: roots, transcripts, terminals, and an asker that mints."""

    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cairn-proof-idle-trigger-"))
        self.roots = {"repo": self.tmp, "commons": self.tmp, "instance": self.tmp / "instance"}
        self.transcripts = self.tmp / "transcripts"
        self.pts = self.tmp / "pts"
        self.asked: list[datetime] = []
        self.now = NOW
        (self.transcripts / "-proj").mkdir(parents=True)
        self.pts.mkdir()
        for dev in ("web_server", "librarian"):
            (self.roots["instance"] / "logs" / dev / "0").mkdir(parents=True)
        self.terminal(NOW - 5 * H)

    def turn(self, at: datetime, kind: str | None = "human", entrypoint: str = "cli") -> None:
        e = {"type": "user", "timestamp": at.isoformat().replace("+00:00", "Z"),
             "entrypoint": entrypoint, "message": {"role": "user", "content": "hello"}}
        if kind is not None:
            e["origin"] = {"kind": kind}
        with open(self.transcripts / "-proj" / "s.jsonl", "a") as fh:
            fh.write(json.dumps(e) + "\n")

    def terminal(self, at: datetime, n: str = "0") -> None:
        p = self.pts / n
        p.touch()
        os.utime(p, (at.timestamp(), at.timestamp()))

    def log(self, dev: str, gate: str, at: datetime) -> None:
        name = at.strftime("%Y%m%d.%H%M%S.%f") + f".{gate}.json"
        (self.roots["instance"] / "logs" / dev / "0" / name).write_text("{}")

    def ask(self) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        self.asked.append(self.now)
        cycle = {"cycle_id": f"c{len(self.asked)}", "roster": [], "position": 0, "visited": [],
                 "opened_at": self.now.isoformat(), "closed_at": self.now.isoformat(),
                 "closed_by": "nothing to visit"}
        token._write(cycle, self.roots)
        return {"cycle": cycle}

    def pulse(self, at: datetime, **kw) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import idle
        self.now = at
        return idle.pulse(roots=self.roots, now=at, transcripts=self.transcripts, pts=self.pts,
                          ask=self.ask, **kw)


def tooth_a_quiet_past_the_threshold_mints_once():
    w = _World()
    w.turn(NOW - 4 * H)
    w.log("web_server", "WebServerDevice.serve", NOW - 4 * H)
    r = w.pulse(NOW)
    assert r["due"] and len(w.asked) == 1, r
    assert r["minted"] == "c1", r
    from cairn.devices.cairn.machines.sleep_cycle import idle
    on_disk = json.loads(idle.pulse_path(w.roots).read_text())
    assert on_disk["due"] is True and on_disk["minted"] == "c1", on_disk


def tooth_b_a_human_turn_holds_sleep():
    w = _World()
    w.turn(NOW - 10 * timedelta(minutes=1))
    r = w.pulse(NOW)
    assert not r["due"] and w.asked == [], r
    assert r["sources"]["cc"]["at"] is not None, r


def tooth_c_machine_turns_are_not_activity():
    w = _World()
    w.turn(NOW - 10 * timedelta(minutes=1), kind="peer")
    w.turn(NOW - 5 * timedelta(minutes=1), kind="task-notification")
    w.turn(NOW - 2 * timedelta(minutes=1), kind=None, entrypoint="sdk-cli")
    r = w.pulse(NOW)
    assert r["sources"]["cc"]["at"] is None, r
    assert r["due"] and len(w.asked) == 1, r


def tooth_d_each_other_source_holds_sleep_alone():
    for name, act in (("web_server", lambda w: w.log("web_server", "WebServerDevice.serve", NOW - 5 * timedelta(minutes=1))),
                      ("librarian", lambda w: w.log("librarian", "LibrarianDevice.chat", NOW - 5 * timedelta(minutes=1))),
                      ("command_line", lambda w: w.terminal(NOW - 5 * timedelta(minutes=1), "3"))):
        w = _World()
        act(w)
        r = w.pulse(NOW)
        assert not r["due"] and w.asked == [], (name, r)
        assert r["sources"][name]["at"] is not None, (name, r)


def tooth_e_one_sleep_per_quiet_spell():
    w = _World()
    w.pulse(NOW)
    assert len(w.asked) == 1, w.asked
    r = w.pulse(NOW + timedelta(minutes=10))
    assert not r["due"] and len(w.asked) == 1, r
    w.turn(NOW + 1 * H)
    r = w.pulse(NOW + 2 * H)
    assert not r["due"] and len(w.asked) == 1, r
    r = w.pulse(NOW + 4 * H + timedelta(minutes=1))
    assert r["due"] and len(w.asked) == 2, r


def tooth_f_an_unread_source_is_never_silence():
    w = _World()
    (w.roots["instance"] / "logs" / "librarian" / "0").rmdir()
    r = w.pulse(NOW)
    assert r["sources"]["librarian"]["unread"], r
    assert not r["due"] and w.asked == [], r
    assert "unread" in r["why"], r


def tooth_g_an_away_window_sleeps_at_once_through_the_verb():
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.machines.sleep_cycle import idle
    w = _World()
    w.turn(NOW - timedelta(minutes=1))
    dev = CairnDevice(roots=w.roots)
    verb = dev.declared_verbs()["away"]
    got = verb({"body": {"act": "set", "start": (NOW - timedelta(minutes=2)).isoformat(),
                         "end": (NOW + H).isoformat(), "why": "proof"}})
    assert got.get("away"), got
    r = w.pulse(NOW)
    assert r["due"] and len(w.asked) == 1, r
    r = w.pulse(NOW + timedelta(minutes=5))
    assert not r["due"] and len(w.asked) == 1, r
    assert verb({"body": {"act": "show"}})["away"]["why"] == "proof"
    verb({"body": {"act": "clear"}})
    assert not idle.away_path(w.roots).exists()
    bad = verb({"body": {"act": "set", "start": NOW.isoformat(), "end": NOW.isoformat()}})
    assert bad.get("accepted") is False, bad


def tooth_h_the_threshold_is_a_parameter():
    from cairn.devices.cairn.device import CairnDevice
    w = _World()
    w.turn(NOW - 2 * H)
    r = w.pulse(NOW, threshold_s=3 * 3600)
    assert not r["due"] and w.asked == [], r
    r = w.pulse(NOW, threshold_s=1 * 3600)
    assert r["due"] and len(w.asked) == 1, r
    s = CairnDevice().settings()
    assert s.get("idle_threshold_s") == 10800, s
    assert "2026-08-24" in s.get("idle_threshold_provenance", ""), s


def tooth_i_the_entry_point_runs_once_and_records():
    home = Path(tempfile.mkdtemp(prefix="cairn-proof-idle-trigger-home-"))
    env = {**os.environ, "HOME": str(home), "PYTHONPATH": str(_REPO_ROOT)}
    p = subprocess.run([sys.executable, "-m", "cairn.devices.cairn", "pulse"], cwd=_REPO_ROOT,
                       env=env, capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    assert "not due" in p.stdout, p.stdout
    assert "unread cc" in p.stderr, p.stderr
    rec = json.loads((home / ".cairn/devices/cairn/0/machines/sleep_cycle/pulse.json").read_text())
    assert rec["due"] is False and rec["minted"] is None and rec["sources"]["cc"]["unread"], rec


NARROW = [tooth_a_quiet_past_the_threshold_mints_once, tooth_b_a_human_turn_holds_sleep,
          tooth_c_machine_turns_are_not_activity, tooth_d_each_other_source_holds_sleep_alone,
          tooth_e_one_sleep_per_quiet_spell, tooth_f_an_unread_source_is_never_silence,
          tooth_g_an_away_window_sleeps_at_once_through_the_verb,
          tooth_h_the_threshold_is_a_parameter, tooth_i_the_entry_point_runs_once_and_records]


def test_the_cairn_device_sleeps_after_quiet_and_never_while_active():
    failed = []
    for t in NARROW:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — every tooth prints, the first red stops nothing
            failed.append(t.__name__)
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    assert not failed, failed


def _run_all() -> int:
    rc = 0
    for tid, k in sorted((tid, k) for tid in PROVES for k in PROVES[tid]):
        t = globals()[PROVES[tid][k]]
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    return rc


if __name__ == "__main__":
    sys.exit(_run_all())

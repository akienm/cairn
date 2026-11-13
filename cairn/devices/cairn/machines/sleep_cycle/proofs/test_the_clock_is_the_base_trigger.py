"""PROOF — the clock is sleep's base trigger, measurement overrides it, and Cairn sleeps first.

Ticket 4de7baf7e255 (sleep-cycle-token, re-cast 2026-11-13 to outline 5.3.3). One tooth per
falsifier clause:

  1  with a source unread, a pulse at 23:10 is due, its why naming the clock, and asks one mint;
     a second pulse at 23:40 the same night asks nothing;
  2  with a source unread, a pulse at 12:00 holds and asks nothing, its why naming the source;
  3  with every source read, activity ten minutes old holds a 23:10 pulse, and quiet past the
     threshold makes a 15:00 pulse due: measurement overrides the clock both ways;
  4  the device's sleep-cycle mint over a one-device roster has swept a 31-day-old log before
     the first hand is posted, and the answer that closes the rotation sweeps nothing (a
     40-day-old log planted after the mint survives the close);
  5  the clock is a parameter (clock_hour 2 is due at 02:10, not at 23:10), and the device's
     settings carry sleep_clock 23:00 with provenance naming outline 5.3.3.4.

What a hollow build cannot pass (Law 8): the pre-clock ``decide`` holds every unread pulse, which
reds 1 and 5; a ``decide`` that ignores measurement reds 3; a device that sweeps at the close
reds 4 both ways; settings without the clock red 5.

THE WORLD IS A FIXTURE: temp roots, a temp transcripts tree (absent when cc must read unread),
a temp terminal folder, an injected asker that writes the closed cycle an empty-roster mint
would, and a fake bus for the device. Every time is UTC and every decision is passed
``tz=timezone.utc``, so the proof reads the same on every box at every hour. Nothing here
touches ``~/.cairn``, ``~/.claude`` or a live bus. Subjects are imported inside each tooth.

    python3 cairn/devices/cairn/machines/sleep_cycle/proofs/test_the_clock_is_the_base_trigger.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "4de7baf7e255": {
        "1": "test_an_unread_pulse_sleeps_once_at_the_clock",
        "2": "test_an_unread_pulse_holds_away_from_the_clock",
        "3": "test_measurement_overrides_the_clock_both_ways",
        "4": "test_cairn_sleeps_before_the_first_hand_and_not_at_the_close",
        "5": "test_the_clock_is_a_parameter_with_provenance",
    },
}

UTC = timezone.utc
NIGHT = datetime(2026, 11, 13, 23, 10, tzinfo=UTC)
NOON = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
MIN = timedelta(minutes=1)
DAY_S = 86400


class _World:
    """roots, terminals, two log folders; transcripts only when ``cc_read``."""

    def __init__(self, cc_read: bool) -> None:
        self.tmp = Path(scratch_dir("cairn-proof-sleep-clock-"))
        self.roots = {"repo": self.tmp, "commons": self.tmp, "instance": self.tmp / "instance"}
        self.transcripts = self.tmp / "transcripts"
        self.pts = self.tmp / "pts"
        self.asked: list[datetime] = []
        self.now = NOON
        if cc_read:
            (self.transcripts / "-proj").mkdir(parents=True)
        self.pts.mkdir()
        p = self.pts / "0"
        p.touch()
        old = datetime(2026, 11, 12, 0, 0, tzinfo=UTC).timestamp()
        os.utime(p, (old, old))
        for dev in ("web_server", "librarian"):
            (self.roots["instance"] / "logs" / dev / "0").mkdir(parents=True)

    def turn(self, at: datetime) -> None:
        e = {"type": "user", "timestamp": at.isoformat().replace("+00:00", "Z"),
             "entrypoint": "cli", "origin": {"kind": "human"},
             "message": {"role": "user", "content": "hello"}}
        f = self.transcripts / "-proj" / "s.jsonl"
        with open(f, "a") as fh:
            fh.write(json.dumps(e) + "\n")
        # read_cc skips a file untouched since its floor; the fixture night may lie ahead of the
        # real clock, so the file is stamped at the turn, as a live write at that moment would be.
        os.utime(f, (at.timestamp(), at.timestamp()))

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
        kw.setdefault("tz", UTC)
        return idle.pulse(roots=self.roots, now=at, transcripts=self.transcripts, pts=self.pts,
                          ask=self.ask, **kw)


def test_an_unread_pulse_sleeps_once_at_the_clock():
    w = _World(cc_read=False)
    r = w.pulse(NIGHT)
    assert r["sources"]["cc"]["unread"], r
    assert r["due"] and len(w.asked) == 1, r
    assert "clock" in r["why"] and "23:00" in r["why"], r["why"]
    r = w.pulse(NIGHT + 30 * MIN)
    assert not r["due"] and len(w.asked) == 1, ("a second pulse the same night asked again", r)


def test_an_unread_pulse_holds_away_from_the_clock():
    w = _World(cc_read=False)
    r = w.pulse(NOON)
    assert not r["due"] and w.asked == [], r
    assert "unread" in r["why"] and "cc" in r["why"], r["why"]


def test_measurement_overrides_the_clock_both_ways():
    w = _World(cc_read=True)
    w.turn(NIGHT - 10 * MIN)
    r = w.pulse(NIGHT)
    assert not any(s["unread"] for s in r["sources"].values()), r["sources"]
    assert not r["due"] and w.asked == [], ("activity ten minutes old did not hold the clock", r)
    q = _World(cc_read=True)
    r = q.pulse(datetime(2026, 11, 13, 15, 0, tzinfo=UTC))
    assert r["due"] and len(q.asked) == 1, ("measured quiet did not open sleep at 15:00", r)


class _OneSleeperBus:
    """A bus with one device announcing ``sleep``; every post records whether the old log
    still stood at that moment."""

    def __init__(self, device: str, old: Path) -> None:
        self.device, self.old = device, old
        self.posts: list[dict] = []

    def post(self, **kw):
        self.posts.append({**kw, "old_log_stood": self.old.exists()})
        return {"id": f"proof-sleep-clock-{len(self.posts)}"}

    def read(self, **kw):
        if kw.get("to") == self.device and kw.get("channel") == "announce":
            return [{"body": {"verbs": ["sleep"]}}]
        return []


def _plant(path: Path, age_days: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x")
    t = time.time() - age_days * DAY_S
    os.utime(path, (t, t))
    return path


def test_cairn_sleeps_before_the_first_hand_and_not_at_the_close():
    from cairn.devices.cairn.device import CairnDevice
    tmp = Path(scratch_dir("cairn-proof-sleep-clock-dev-"))
    roots = {"repo": tmp / "repo", "commons": tmp / "commons", "instance": tmp / "instance"}
    logs = roots["instance"] / "logs" / "fx_dev" / "0"
    roster_root = tmp / "roster"
    (roster_root / "cairn" / "devices" / "fx_sleeper").mkdir(parents=True)
    old = _plant(logs / "old.jsonl", 31)
    bus = _OneSleeperBus("fx_sleeper", old)
    dev = CairnDevice(bus=bus, roots=roots, roster_root=roster_root)
    dev.set_diagnostic_receiver(None)
    verbs = dev.declared_verbs()
    got = verbs["sleep-cycle"]({"verb": "sleep-cycle", "body": {"act": "mint"}})
    cycle = got["cycle"]
    assert cycle["roster"] == ["fx_sleeper"] and cycle["closed_at"] is None, got
    hands = [p for p in bus.posts if p.get("to") == "fx_sleeper" and p.get("channel") == "personal"]
    assert len(hands) == 1, bus.posts
    assert hands[0]["old_log_stood"] is False, "the first hand was posted before Cairn swept its logs"
    assert not old.exists() and got.get("logs", {}).get("deleted") == 1, got
    late = _plant(logs / "late.jsonl", 40)
    closed = verbs["sleep-token"]({"verb": "sleep-token",
                                   "body": {"sleep_token": cycle["cycle_id"], "device": "fx_sleeper",
                                            "answer": "slept"}})
    assert closed.get("accepted") and closed.get("closed"), closed
    assert late.is_file(), "the close swept the logs: Cairn's sleep ran last, not first"
    assert "logs" not in closed, closed


def test_the_clock_is_a_parameter_with_provenance():
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.machines.sleep_cycle import idle
    sources = {"cc": {"at": None, "unread": "FileNotFoundError: fixture"},
               "command_line": {"at": None, "unread": None}}
    last = datetime(2026, 11, 12, 0, 0, tzinfo=UTC)
    two = datetime(2026, 11, 13, 2, 10, tzinfo=UTC)
    due, why = idle.decide(sources, last, now=two, threshold_s=3 * 3600, away=None, cycle=None,
                           clock_hour=2, tz=UTC)
    assert due and "02:00" in why, why
    due, why = idle.decide(sources, last, now=NIGHT, threshold_s=3 * 3600, away=None, cycle=None,
                           clock_hour=2, tz=UTC)
    assert not due, why
    s = CairnDevice().settings()
    assert s.get("sleep_clock") == "23:00", s
    assert "5.3.3.4" in s.get("sleep_clock_provenance", ""), s


def main() -> int:
    rc = 0
    for k, name in sorted(PROVES["4de7baf7e255"].items()):
        try:
            globals()[name]()
            print(f"  PASS  {k} {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth prints
            rc = 1
            print(f"  FAIL  {k} {name}: {type(exc).__name__}: {exc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

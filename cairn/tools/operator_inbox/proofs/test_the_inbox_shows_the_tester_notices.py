"""The operator inbox shows the tester's notices, with the rate (ticket 81c41e528d6f).

Akien's answer to open-ed0a56ce6357: a green the measurement cannot vouch for completes "AND
notify me", and "if i get inundated, we'll change it". The tester posts those notices
(b5871526384a); this lane is where he sees them. It asks the tester's `notices` verb over the
bus — never the tester's store (RULE 1) — shows each unseen notice with the head of its diff
and the notices-per-day rate (the instrument that says whether he is inundated), and is loud
when the tester could not be asked: an unasked lane must never read as "0 unseen" (Law 7).
`cairn operator notice-seen <id>` marks one seen through the tester's `notice-seen` verb.

Every tooth imports the inbox INSIDE its body, so a reverted inbox.py reds teeth instead of
breaking this file's import — which is what lets the hollow run read it.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"81c41e528d6f": {
    "1": "test_the_reader_asks_the_tester_notices_verb",
    "2": "test_the_lane_shows_each_notice_and_the_rate_among_his_sections",
    "3": "test_a_tester_that_cannot_be_asked_is_loud",
    "4": "test_the_summary_carries_the_count_and_the_rate",
    "5": "test_notice_seen_asks_the_tester_verb",
    "6": "test_the_live_tester_answers_the_lane",
}}

_RATE = {"total": 3, "first": "2026-10-04T00:00:00+00:00", "days": 2, "per_day": 1.5}
_LONG_DIFF = "\n".join(f"+line {i}" for i in range(20))
_NOTICES = [
    {"id": "n-111111111111", "ticket": "aaaaaaaaaaaa", "file": "x.py",
     "line": "aaaaaaaaaaaa: x.py reverted and no declared tooth redded — LINEMARKER-ONE",
     "diff": _LONG_DIFF, "posted_at": "2026-10-04T00:00:00+00:00", "seen_at": None},
    {"id": "n-222222222222", "ticket": "bbbbbbbbbbbb", "file": "y.py",
     "line": "bbbbbbbbbbbb: y.py reverted and no declared tooth redded — LINEMARKER-TWO",
     "diff": "-old\n+new", "posted_at": "2026-10-04T01:00:00+00:00", "seen_at": None},
]


def _reply(body: dict) -> dict:
    return {"sender": "tester", "addressee": "operator_inbox", "kind": "record", "body": body}


def _two():
    return _reply({"unseen": [dict(n) for n in _NOTICES], "rate": dict(_RATE)})


def _none():
    return _reply({"unseen": [], "rate": dict(_RATE)})


def _down():
    raise ConnectionError("bus down")


class _Recorder:
    """Stands in for cairn.tools.bus_client.reach: records who was reached and what was asked."""

    def __init__(self, answer: dict):
        self.answer, self.reached, self.asked = answer, [], []

    def __call__(self, *devices):
        self.reached.append(devices)
        return self

    def request(self, **kw):
        self.asked.append(kw)
        return _reply(self.answer)


@contextlib.contextmanager
def _reach(rec: _Recorder):
    import cairn.tools.bus_client as bc
    saved = bc.reach
    bc.reach = rec
    try:
        yield rec
    finally:
        bc.reach = saved


def test_the_reader_asks_the_tester_notices_verb():
    from cairn.tools.operator_inbox import inbox
    with _reach(_Recorder({"unseen": [dict(_NOTICES[0])], "rate": dict(_RATE)})) as rec:
        got = inbox.read_notices()
    assert rec.reached == [("tester",)], rec.reached
    assert len(rec.asked) == 1, rec.asked
    kw = rec.asked[0]
    assert (kw.get("sender"), kw.get("to"), kw.get("verb")) == ("operator_inbox", "tester", "notices"), kw
    assert got["error"] is None, got
    assert got["count"] == 1 and [n["id"] for n in got["unseen"]] == ["n-111111111111"], got
    assert got["rate"] == _RATE, got["rate"]


def test_the_lane_shows_each_notice_and_the_rate_among_his_sections():
    from cairn.tools.operator_inbox import inbox
    data = inbox.gather_all(notices_ask=_two)
    out = inbox.format_inbox(data)
    head = "NOTICES FROM THE TESTER (2 unseen; 1.5/day over 2 day(s), 3 total)"
    assert head in out, out
    for n in _NOTICES:
        assert n["id"] in out and n["line"] in out, n["id"]
    assert "+line 0" in out and "+line 7" in out and "+line 8" not in out, out
    assert "(+12 more diff line(s))" in out, out
    assert "-old" in out and "+new" in out, out
    assert "mark seen with: cairn operator notice-seen <id>" in out, out
    i_q, i_n, i_d = out.find("QUESTIONS"), out.find(head), out.find("DESIGN")
    assert -1 < i_q < i_n < i_d, (i_q, i_n, i_d)
    troubles = [i for i in (out.find("  TROUBLES:"), out.find("LIVE TROUBLES (")) if i > -1]
    assert troubles and i_n < min(troubles), (i_n, troubles)
    zero = inbox.format_inbox(dict(data, notices=inbox.read_notices(ask=_none)))
    assert "NOTICES: 0 unseen (3 total, 1.5/day over 2 day(s))" in zero, zero
    assert "NOTICES FROM THE TESTER" not in zero, zero


def test_a_tester_that_cannot_be_asked_is_loud():
    from cairn.tools.operator_inbox import inbox
    got = inbox.read_notices(ask=_down)
    assert got["count"] is None and got["rate"] is None, got
    assert got["error"] and "ConnectionError" in got["error"] and "bus down" in got["error"], got
    out = inbox.format_inbox(inbox.gather_all(notices_ask=_down))
    assert "!! NOTICES:" in out and "bus down" in out, out
    assert "NOTICES: 0 unseen" not in out, out


def test_the_summary_carries_the_count_and_the_rate():
    from cairn.tools.operator_inbox import inbox
    data = inbox.gather_all(notices_ask=_two)
    assert "2 unseen notice(s) (1.5/day)" in inbox.format_summary(data), inbox.format_summary(data)
    down = dict(data, notices=inbox.read_notices(ask=_down))
    assert "notices: could not ask the tester" in inbox.format_summary(down), inbox.format_summary(down)


def _main(argv):
    from cairn.tools.operator_inbox import inbox
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = inbox.main(argv)
    return rc, out.getvalue(), err.getvalue()


def test_notice_seen_asks_the_tester_verb():
    nid = "n-aaaaaaaaaaaa"
    with _reach(_Recorder({"seen": nid})) as rec:
        rc, out, err = _main(["notice-seen", nid])
    assert rec.reached == [("tester",)], rec.reached
    kw = rec.asked[0]
    assert (kw.get("to"), kw.get("verb"), kw.get("body")) == ("tester", "notice-seen", {"id": nid}), kw
    assert rc == 0 and f"seen {nid}" in out, (rc, out, err)
    refusal = f"no notice {nid!r} — nothing was marked"
    with _reach(_Recorder({"refused": refusal})):
        rc, out, err = _main(["notice-seen", nid])
    assert rc == 1 and refusal in err, (rc, out, err)


def test_the_live_tester_answers_the_lane():
    from cairn.tools.operator_inbox import inbox
    got = inbox.read_notices()
    assert got["error"] is None, got["error"]
    assert set(got["rate"]) >= {"total", "first", "days", "per_day"}, got["rate"]
    assert got["count"] == len(got["unseen"]), got


def main() -> int:
    fails = 0
    for name in PROVES["81c41e528d6f"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

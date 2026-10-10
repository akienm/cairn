"""Proof for ticket 4818f7f37e1e — the chart verbs print the drain's failure line and exit non-zero.

Akien, 2026-10-10: "we need to make the queue record stderr. and the result code for heavens
sake." Codemother's drain now renders the DEPOSIT FAILED line once and carries it in the
drained entry (637d206be821); these verbs print THAT line, still serve, and then exit 3, so a
caller sees the failure in the exit status as well as on stderr.

The bus seam (live._ask_codemother) and the walk/embed/dial are monkeypatched, so no device,
host or tree is on any tooth's path. One tooth per numbered falsifier clause:

  1. LEARN SERVES, PRINTS THE CARRIED LINE, EXITS 3. A drain reply carrying one failed entry
     with stderr 'X' → stderr holds exactly 'X' (no second rendering), stdout holds the learn
     JSON, the return is 3.
  2. COUNSEL LIKEWISE. Same drain reply → counsel serves its JSON and returns 3.
  3. A CLEAN DRAIN IS 0, A REFUSAL IS 1. No failed entry → both return 0; a refused deposit
     returns 1, with or without a failed drain (the verb's own failure outranks).

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/chart/proofs/test_the_verbs_exit_nonzero_on_a_failed_drain.py
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"4818f7f37e1e": {"1": "learn_serves_prints_the_carried_line_exits_3",
                           "2": "counsel_serves_and_exits_3",
                           "3": "a_clean_drain_is_0_a_refusal_is_1"}}

BERTH = "/fixture/4818f7f37e1e/packets/verdict-stuck-fixture.json"
CARRIED = "X-the-drain's-own-line-for-%s" % BERTH
FAILED = {"berth": BERTH, "failed": "VerdictRefused: fixture", "still_pending": True,
          "stderr": CARRIED, "result_code": "VerdictRefused"}
LANDED = {"berth": BERTH, "deposited": ["n1"], "parts": 1, "duplicates": 0, "tokens": 0,
          "nexus": "hypothesize"}


def _live(drained: list[dict], *, deposit_accepted: bool = True):
    """skills.chart.live with its one bus seam and the walk answered by fixtures."""
    from skills.chart import live

    def ask(verb, body):
        if verb == "drain":
            return {"accepted": True, "drained": drained}
        if verb == "deposit":
            if not deposit_accepted:
                return {"accepted": False, "reason": "fixture refusal"}
            return {"accepted": True, "learn": {"node_id": "n0"}, "nexus": "orient"}
        raise AssertionError("unexpected verb %r" % verb)

    live._ask_codemother = ask
    live._embed = lambda text: [0.0, 0.0, 1.0]
    live.counsel = lambda vector, nexus, **kw: {"floor": 0.5, "walk": []}
    live.dial = lambda: {"nexi": {}}
    return live


def _run(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn(argv)
    return rc, out.getvalue(), err.getvalue()


def learn_serves_prints_the_carried_line_exits_3() -> None:
    live = _live([FAILED])
    rc, out, err = _run(live._learn, ["/fixture/4818f7f37e1e/packets/orient-x.json"])
    assert err.splitlines() == [CARRIED], ("stderr is exactly the carried line", err)
    served = json.loads(out)
    assert served.get("learn") == {"node_id": "n0"} and served.get("drained") == [FAILED], served
    assert rc == 3, ("a served learn over a failed drain exits 3", rc)


def counsel_serves_and_exits_3() -> None:
    live = _live([FAILED])
    rc, out, err = _run(live._counsel, ["a fixture request"])
    assert err.splitlines() == [CARRIED], ("stderr is exactly the carried line", err)
    served = json.loads(out)
    assert served.get("request") == "a fixture request" and served.get("drained") == [FAILED], served
    assert rc == 3, ("a served counsel over a failed drain exits 3", rc)


def a_clean_drain_is_0_a_refusal_is_1() -> None:
    for drained in ([], [LANDED]):
        live = _live(drained)
        rc, out, err = _run(live._learn, ["/fixture/4818f7f37e1e/packets/orient-x.json"])
        assert rc == 0 and err == "" and json.loads(out)["learn"], ("clean learn", drained, rc, err)
        live = _live(drained)
        rc, out, err = _run(live._counsel, ["a fixture request"])
        assert rc == 0 and err == "" and json.loads(out)["request"], ("clean counsel", drained, rc, err)
    for drained in ([], [FAILED]):
        live = _live(drained, deposit_accepted=False)
        rc, out, err = _run(live._learn, ["/fixture/4818f7f37e1e/packets/orient-x.json"])
        assert rc == 1, ("a refused deposit returns 1, drain failed=%s" % bool(drained), rc)
        assert "DEPOSIT REFUSED" in err, err


TEETH = (learn_serves_prints_the_carried_line_exits_3, counsel_serves_and_exits_3,
         a_clean_drain_is_0_a_refusal_is_1)


def main() -> int:
    from skills.chart import live
    saved = {k: getattr(live, k) for k in ("_ask_codemother", "_embed", "counsel", "dial")}
    failed = 0
    try:
        for tooth in TEETH:
            try:
                tooth()
                print("  green %s" % tooth.__name__)
            except Exception as e:  # noqa: BLE001 — a tooth's every failure is a red, named
                failed += 1
                print("  RED   %s — %s: %s" % (tooth.__name__, type(e).__name__, e))
    finally:
        for k, v in saved.items():
            setattr(live, k, v)
    print("%d passed, %d failed out of %d" % (len(TEETH) - failed, failed, len(TEETH)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

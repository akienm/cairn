"""PROOF — the sleep token rotates through the roster and comes back to cairn.

Ticket bf146e9e3967 (token-rotation-mechanism). The falsifier is unnumbered, so this proof
declares ONE composite tooth against clause ``all`` and it asserts, in one run:

  (1) the roster is the alpha-sorted list of devices holding ``SLEEP_PROBE`` — [a, b, c];
  (2) after a mint and enough beats the cycle is closed, ``visited`` is exactly [a, b, c] in
      that order, and each fixture device's own recorder holds its one work record;
  (3) at every point at most one device holds an unanswered token;
  (4) exactly four announce records carry the cycle_id — three hands and one close;
  (5) an answer carrying a stale cycle_id is refused ``accepted: False`` and the standing
      cycle is untouched;
  (6) an empty roster closes at mint with ``nothing to visit``.

What a hollow build cannot pass (Law 8): a ``token.py`` that never hands (no inbound record
at a, (2)); one that hands to everyone at once ((3) reads three holders); one that forgets the
close ((2) never closes, (4) reads three); a ``mail_probe`` that never fires or fires without
answering ((2) stalls at position 0); a ``device.py`` without the ``sleep-token`` verb (the
poke BOUNCES and (2) stalls); an ``_answer`` that takes any cycle_id ((5)).

THE WORLD IS A FIXTURE (D6/D7). No live device carries a sleep probe and this proof berths
none: three fixture devices live under a tmp root, their probes are the three-line
``answers_mail`` declaration written to disk and imported with ``discovery.load_module`` —
the same door the ground loop uses — and their mailboxes record at ``instance_path(id, 0,
fixture_roots)`` rather than at ``~/.cairn`` (``_FeedbackDevice`` has no roots seam, so the
shims here are hand-held). The bus is ``BusDevice.scratch`` (Postgres; drops at close).

THE BEAT ORDER IS c, b, a — DELIBERATELY. Every subscribed shim pulses once per beat, so
subscribing a first would let one beat run the whole rotation (a fires, hands to b, b
pulses next and fires, ...) and (3) could only be measured at the end. Reversed, each beat
advances exactly one hand and the holder count is read between beats.

    python3 cairn/devices/cairn/machines/sleep_cycle/proofs/test_token_rotation.py   # exit 0 = green
"""

from __future__ import annotations

import contextlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402
from cairn.devices.cairn.shim import CairnShim  # noqa: E402

_TICKET = "bf146e9e3967"

# One clause, one declarable tooth (proof_coverage: an unnumbered falsifier is clause "all").
# A LITERAL, not ``_TICKET``: ``proof_coverage.declared`` reads this with ``ast.literal_eval``.
PROVES = {
    "bf146e9e3967": {
        "all": "test_the_token_rotates_through_the_roster_and_returns_to_cairn",
    },
}

_SCRATCH = contextlib.ExitStack()
NOW = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
FIXTURE_DEVICES = ("fx_sleep_a", "fx_sleep_b", "fx_sleep_c")

# The D5 three-liner, verbatim what a device berths to join the rotation.
_SLEEP_PROBE_SOURCE = '''from cairn.tools.base.mail_probe import answers_mail
def _sleep(body): return {"slept": body["sleep_token"], "position": body["position"]}
PROBE = answers_mail("sleep_token", _sleep, device_file=__file__, why="answers the sleep token", verb="sleep-token")
'''


class FixtureMailbox:
    """What ``_FeedbackDevice.receive`` writes, at fixture roots instead of ``~/.cairn``."""

    def __init__(self, device_id: str, roots: dict) -> None:
        from cairn.tools.base.address import instance_path
        from cairn.tools.data_recorder.data_recorder import DataRecorder
        self._device_id = device_id
        self.recorder = DataRecorder(
            instance_path(device_id, 0, roots) / "tools" / "data_recorder" / "inbound")

    @property
    def device_id(self) -> str:
        return self._device_id

    def receive(self, envelope: dict) -> dict:
        self.recorder.write({
            "finding": envelope.get("why", "bus message received"),
            "inspector_target": self._device_id,
            "probe_source": envelope.get("sender", "unknown"),
            "envelope_id": envelope.get("id"),
            "verb": envelope.get("verb", ""),
            "body": envelope.get("body", {}),
        })
        return {"accepted": True, "device": self._device_id}


class FixtureShim(BaseShim):
    """A discovered device's shim, hand-held: ONLINE from birth, one probe loaded off disk."""

    def __init__(self, device_id: str, mailbox: FixtureMailbox, probe, bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = mailbox
        self._probe = probe
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def probes(self):
        return [self._probe]

    def _start_device(self):
        return self._device


class FixtureCairnShim(CairnShim):
    """The real cairn shim, its device pointed at the fixture roots and roster."""

    def __init__(self, bus, roots: dict, roster_root: Path) -> None:
        super().__init__(bus=bus)
        self._roots = roots
        self._roster_root = roster_root

    def _start_device(self):
        from cairn.devices.cairn.device import CairnDevice
        return CairnDevice(bus=self._bus, roots=self._roots, roster_root=self._roster_root)


def _fixture_world(tmp: Path) -> tuple[dict, Path]:
    """Three devices under ``tmp/devices``, each holding the three-line probe."""
    for dev in FIXTURE_DEVICES:
        probes = tmp / "devices" / dev / "probes"
        probes.mkdir(parents=True)
        (probes / "sleeps_when_the_token_arrives.py").write_text(_SLEEP_PROBE_SOURCE)
    roots = {"repo": tmp, "commons": tmp, "instance": tmp / "instance"}
    return roots, tmp


def _holders(roots: dict) -> list[str]:
    """Which fixture devices hold an unanswered token right now."""
    from cairn.tools.base.mail_probe import pending
    return [d for d in FIXTURE_DEVICES if pending(d, "sleep_token", roots)]


def _announces(bus, cycle_id: str) -> list[dict]:
    return [e for e in bus.read(to="cairn", channel="announce")
            if (e.get("body") or {}).get("cycle_id") == cycle_id]


def _rig(bus, roots: dict, roster_root: Path):
    from cairn.devices.cairn.machines.ground_loop.discovery import load_module
    loop = GroundLoopDevice(bus=bus)
    cairn_shim = FixtureCairnShim(bus, roots, roster_root)
    loop.subscribe(cairn_shim)
    boxes = {}
    for dev in reversed(FIXTURE_DEVICES):        # c, b, a — see the module docstring
        probe_file = roster_root / "devices" / dev / "probes" / "sleeps_when_the_token_arrives.py"
        probe = load_module(probe_file).PROBE
        boxes[dev] = FixtureMailbox(dev, roots)
        loop.subscribe(FixtureShim(dev, boxes[dev], probe, bus=bus))
    return loop, cairn_shim, boxes


_MACHINE_CHARTER = "cairn/devices/cairn/machines/sleep_cycle/intention+why.json"
_BASE_CHARTER = "cairn/tools/base/intention+why.json"


def _charters_stand() -> None:
    """The two charters this build wrote are evidence too (the hollow check reverts them):
    the machine's charter berths beside its code naming THIS proof, and base's charter
    declares the ``answers_mail`` invoke a device's three-liner imports."""
    import json
    machine = _REPO_ROOT / _MACHINE_CHARTER
    assert machine.is_file(), f"{_MACHINE_CHARTER} is not on disk — the machine has no charter"
    charter = json.loads(machine.read_text(encoding="utf-8"))
    assert charter.get("component") == "sleep_cycle" and charter.get("runtime_role") == "machine", charter
    assert charter.get("proof") == "cairn/devices/cairn/machines/sleep_cycle/proofs/test_token_rotation.py", charter.get("proof")
    for field in ("what", "why", "falsifier", "owner"):
        assert str(charter.get(field, "")).strip(), f"{_MACHINE_CHARTER}: {field} is blank"
    base = json.loads((_REPO_ROOT / _BASE_CHARTER).read_text(encoding="utf-8"))
    assert "from cairn.tools.base.mail_probe import answers_mail" in str(base.get("invoke", "")), (
        f"{_BASE_CHARTER} does not declare the mail_probe invoke")


# --- the tooth ---------------------------------------------------------------

def test_the_token_rotates_through_the_roster_and_returns_to_cairn():
    """THE COMPOSITE TOOTH — clauses (1)..(6) of the module docstring, one run."""
    from cairn.devices.cairn.machines.sleep_cycle import token
    from cairn.tools.base.mail_probe import pending

    _charters_stand()
    tmp = Path(_SCRATCH.enter_context(tempfile.TemporaryDirectory(prefix="sleep_cycle_fx_")))
    roots, roster_root = _fixture_world(tmp)
    bus = _SCRATCH.enter_context(BusDevice.scratch("sleep_cycle"))
    loop, cairn_shim, boxes = _rig(bus, roots, roster_root)

    # (1) the roster is read from disk, filtered to the sleep probe, alpha order.
    assert token.roster(roster_root) == list(FIXTURE_DEVICES), token.roster(roster_root)
    assert token.standing(roots) is None

    # Beat 0 wires every shim's delivery (nothing pending, nothing fires).
    loop.beat(NOW, {"roots": roots})
    assert _holders(roots) == [], _holders(roots)

    # Mint through the operator's verb on the bus — the hand lands inside post() (the bus
    # pokes a's shim at post time), and the reply to us rides personal.
    bus.post(sender="proof", to="cairn", channel="personal", verb="sleep-cycle",
             why="mint the rotation", body={"act": "mint"})
    cycle = token.standing(roots)
    assert cycle is not None and cycle["closed_at"] is None, cycle
    cycle_id = cycle["cycle_id"]
    assert cycle["roster"] == list(FIXTURE_DEVICES) and cycle["position"] == 0, cycle
    assert _holders(roots) == ["fx_sleep_a"], _holders(roots)          # (3) one holder
    assert len(_announces(bus, cycle_id)) == 1, _announces(bus, cycle_id)

    # One beat per hand (c, b, a order): the holder answers, cairn hands onward.
    expected_holder = ["fx_sleep_b", "fx_sleep_c", None]
    for i, nxt in enumerate(expected_holder, start=1):
        loop.beat(NOW + timedelta(seconds=60 * i), {"roots": roots})
        holders = _holders(roots)
        assert len(holders) <= 1, f"beat {i}: {holders}"                # (3) never two
        assert holders == ([nxt] if nxt else []), f"beat {i}: {holders} != {nxt}"
        standing = token.standing(roots)
        assert standing["position"] == i, (i, standing)
        assert [v["device"] for v in standing["visited"]] == list(FIXTURE_DEVICES[:i]), standing

    # (2) closed, visited in order, each device's recorder holds its one work record.
    closed = token.standing(roots)
    assert closed["closed_at"] is not None and closed["closed_by"] == "rotation complete", closed
    assert [v["device"] for v in closed["visited"]] == list(FIXTURE_DEVICES), closed
    for dev in FIXTURE_DEVICES:
        hands = [r for r in boxes[dev].recorder.read()
                 if (r.get("body") or {}).get("sleep_token") == cycle_id]
        assert len(hands) == 1, (dev, hands)
        assert pending(dev, "sleep_token", roots) == [], dev
        answered = [v for v in closed["visited"] if v["device"] == dev]
        assert answered and answered[0]["answer"] == {"slept": cycle_id, "position": FIXTURE_DEVICES.index(dev)}, answered
        # the shim posted cairn's reply back to the device: an accepted record with no token key
        replies = [r for r in boxes[dev].recorder.read()
                   if (r.get("body") or {}).get("accepted") is True and "sleep_token" not in (r.get("body") or {})]
        assert replies, (dev, boxes[dev].recorder.read())

    # (4) three hands + one close on the announce feed, nothing more.
    feed = _announces(bus, cycle_id)
    assert [e["body"]["event"] for e in feed] == ["hand", "hand", "hand", "closed"], feed
    assert [e["body"]["device"] for e in feed] == [*FIXTURE_DEVICES, None], feed

    # A further beat changes nothing: every token is answered, no probe fires.
    quiet = loop.beat(NOW + timedelta(seconds=600), {"roots": roots})
    assert token.standing(roots) == closed, quiet
    assert _holders(roots) == []

    # (5) a stale cycle_id is refused and leaves the cycle untouched — through the verb.
    bus.post(sender="proof", to="cairn", channel="personal", verb="sleep-cycle",
             why="mint a second rotation", body={"act": "mint"})
    second = token.standing(roots)
    assert second["cycle_id"] != cycle_id and second["closed_at"] is None, second
    bus.post(sender="proof", to="cairn", channel="personal", verb="sleep-token",
             why="a stale answer", body={"sleep_token": cycle_id, "device": "fx_sleep_a", "answer": "x"})
    replies = [e for e in bus.read(to="proof", channel="personal") if e.get("why") == "sleep-token reply"]
    assert replies and replies[-1]["body"]["accepted"] is False, replies
    assert replies[-1]["body"]["reason"] == "stale cycle_id", replies[-1]
    assert token.standing(roots) == second, token.standing(roots)
    out_of_turn = token.receive_answer(bus, {"sleep_token": second["cycle_id"], "device": "fx_sleep_c"}, roots=roots)
    assert out_of_turn == {"accepted": False, "reason": "out of turn", "cycle_id": second["cycle_id"],
                           "device": "fx_sleep_c", "holder": "fx_sleep_a"}, out_of_turn
    assert token.standing(roots) == second

    # (6) an empty roster closes at mint with "nothing to visit" — one announce record.
    empty_root = Path(_SCRATCH.enter_context(tempfile.TemporaryDirectory(prefix="sleep_cycle_empty_")))
    empty_roots = {"repo": empty_root, "commons": empty_root, "instance": empty_root / "instance"}
    assert token.roster(empty_root) == []
    nothing = token.mint(bus, roots=empty_roots, roster_root=empty_root)
    assert nothing["roster"] == [] and nothing["closed_by"] == "nothing to visit", nothing
    assert [e["body"]["event"] for e in _announces(bus, nothing["cycle_id"])] == ["closed"]
    assert token.receive_answer(bus, {"sleep_token": nothing["cycle_id"], "device": "x"}, roots=empty_roots)["reason"] == "no open cycle"

    print("  green: rotation a->b->c closed in 3 beats, 4 announce records, stale/out-of-turn refused, empty roster closes")


def _run_all() -> int:
    rc = 0
    try:
        for k in sorted(PROVES[_TICKET]):
            t = globals()[PROVES[_TICKET][k]]
            try:
                t()
                print(f"  PASS  {t.__name__}")
            except Exception as exc:  # noqa: BLE001
                rc = 1
                print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    finally:
        _SCRATCH.close()
    return rc


if __name__ == "__main__":
    sys.exit(_run_all())

"""Proof for BaseShim — the device's always-on front: fires probes, receives mail, wakes.

The shim is where the goof is corrected: the ground_loop only BEATS; the FIRING lives here.
This proof exercises the three jobs against a spy bus (hermetic — no DB; the real bus is
proven in cairn/devices/cairn/machines/bus/proofs/test_bus.py, and the full heartbeat→shim→bus chain in the system
device's proof).

Teeth a hollow shim could not pass:
  - ON A PULSE, DUE PROBES POKE THE BUS; held ones do not. The pulse-record names what
    fired and what held — a pulse is evidence, a record, never a silent ``RUNNING``. (This
    line said "LEARNING, not silent RUNNING" until 2026-07-30, when ticket
    watchme-emits-a-probe dissolved ``LEARNING`` as a node state; the tooth never changed.)
  - AN ARMED-AND-NEVER-FIRED PROBE IS LOUD (falsifier clause (2), 2026-07-30): a watch past
    its declared horizon that has never poked surfaces under its OWN key — a healthy resting
    watch and one dead since it was armed must never read the same (Law 7).
  - A BATCH DOES NOT DIE ON ONE BAD PROBE (CP2, Law 7): a trigger that raises becomes a
    permanent 'refused' entry and the rest still fire.
  - THE DEVICE IS STARTED ON DEMAND (the wake-to-a-poke): delivering mail wakes the device
    (its ``receive`` gets the envelope) and flips it running; a shim delivered to with no
    ``_start_device`` refuses loudly (CP1).
  - IT IS A SHIM (Law 2): composes CP1-CP6.

Runnable bare (no DB, no framework):
    python3 cairn/tools/base/proofs/test_shim.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.probe import Probe
from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.shim import BaseShim, NEVER_BOOTED, ONLINE


class _SpyBus:
    """A stand-in for the bus that records posts — the shim's contract is 'it pokes via post'."""

    def __init__(self) -> None:
        self.posted: list[dict] = []
        self._delivery_hooks: dict[str, object] = {}

    def post(self, **envelope) -> dict:
        envelope = {"id": f"env{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        self._delivery_hooks[device_id] = deliver

    def read(self, **kw) -> list[dict]:
        return []


class _Woken:
    """A minimal device the shim wakes on demand; records what it received."""

    def __init__(self) -> None:
        self.mail: list[dict] = []

    def receive(self, envelope: dict) -> str:
        self.mail.append(envelope)
        return "handled"


class _Shim(BaseShim):
    """A concrete shim carrying a fixed probe list and a device it wakes on demand."""

    def __init__(self, bus=None, probes=None) -> None:
        super().__init__(bus=bus)
        self._probes = probes or []
        self.started = 0

    @property
    def device_id(self) -> str:
        return "spec"

    def probes(self):
        return self._probes

    def _start_device(self):
        self.started += 1
        return _Woken()


def test_a_pulse_fires_due_probes_and_holds_the_rest():
    bus = _SpyBus()
    due = Probe(why="wake ops", trigger=lambda now, ctx: ctx.get("cpu", 0) >= 80,
                   to="ops/personal", body={"crossed": 80})
    not_due = Probe(why="wake night", trigger=lambda now, ctx: now == "midnight", to="night/personal")
    shim = _Shim(bus=bus, probes=[due, not_due])

    rec = shim.on_pulse(now="noon", context={"cpu": 95})

    assert rec["fired_count"] == 1 and len(rec["held"]) == 1
    pokes = [e for e in bus.posted if e.get("channel") != "announce"]
    assert len(pokes) == 1, "only the due probe pokes the bus (non-announce)"
    poke = pokes[0]
    assert poke["to"] == "ops/personal" and poke["sender"] == "spec"
    assert poke["body"] == {"crossed": 80}, "the poke carries only that the line was crossed"
    assert rec["held"][0]["to"] == "night/personal"


def test_a_batch_does_not_die_on_one_bad_probe():
    bus = _SpyBus()
    def boom(now, ctx):
        raise RuntimeError("trigger blew up")
    bad = Probe(why="explodes", trigger=boom, to="x/personal")
    good = Probe(why="fine", trigger=lambda now, ctx: True, to="y/personal")
    shim = _Shim(bus=bus, probes=[bad, good])

    rec = shim.on_pulse(now="noon")

    outcomes = {f["to"]: f["outcome"] for f in rec["fired"]}
    assert outcomes["x/personal"] == "refused" and "RuntimeError" in dict(
        (f["to"], f.get("error", "")) for f in rec["fired"])["x/personal"]
    assert outcomes["y/personal"] == "ok", "the good probe still fires after the bad one"
    pokes = [e for e in bus.posted if e.get("channel") != "announce"]
    assert len(pokes) == 1, "the kicked-back probe did not poke; the good one did"


def test_an_armed_and_never_fired_probe_is_loud():
    """THE SILENCE TOOTH (ticket watchme-emits-a-probe falsifier clause (2), 2026-07-30).

    The clause: *"A probe is armed and never fires, and nothing is loud about it — a watcher
    emitted into a heartbeat nobody runs learns nothing while LOOKING like learning."* That is
    the LEARNME failure — carried by everybody, satisfied by nobody — re-committed one level
    up, so it gets a row rather than a promise.

    The teeth that a hollow ``overdue()`` (one that returns ``[]``, or that reads ``held``)
    could not pass: a never-fired probe past its horizon is loud AND names its own numbers; a
    probe that DID fire is silent forever after even while its trigger rests false; a probe
    that declared no horizon is never overdue; and the finding sits under its OWN key, so a
    healthy resting watch and a dead one cannot be read for each other."""
    bus = _SpyBus()
    dead = Probe(why="watches something that never happens", trigger=lambda now, ctx: False,
                 to="ops/personal", horizon=2)
    alive = Probe(why="fires immediately", trigger=lambda now, ctx: True, to="live/personal",
                  horizon=2)
    forever = Probe(why="a standing watch that declared no deadline",
                    trigger=lambda now, ctx: False, to="quiet/personal")
    shim = _Shim(bus=bus, probes=[dead, alive, forever])

    for _ in range(2):
        rec = shim.on_pulse(now="noon")
    assert rec["overdue"] == [], "standing FOR its horizon is not yet standing PAST it"

    rec = shim.on_pulse(now="noon")
    whys = [o["why"] for o in rec["overdue"]]
    assert whys == ["watches something that never happens"], \
        f"exactly the never-fired, horizon-carrying probe is loud — got {whys}"
    assert rec["overdue"][0]["pulses_stood"] == 3 and rec["overdue"][0]["horizon"] == 2, \
        "the finding carries its own numbers, not just a flag (complete on the first pass)"
    assert shim.overdue() == rec["overdue"], "the read-side door and the pulse-record agree"

    # The dead probe is ALSO in `held` with an ordinary reason — which is exactly why the
    # finding needs its own key. A hollow build that reported silence by scanning `held`
    # would indict the standing watch and the fired one too.
    assert any(h["to"] == "quiet/personal" for h in rec["held"]), "the no-horizon watch rests"
    assert "quiet/personal" not in [o["to"] for o in rec["overdue"]], \
        "a probe that declared no horizon can never be overdue — that is its own choice"
    assert "live/personal" not in [o["to"] for o in rec["overdue"]], \
        "a probe that has fired is never overdue, however long it rests afterwards"


def test_a_horizon_is_declared_not_inferred():
    """A horizon is OPTIONAL and REFUSED WHEN NONSENSE (CP1, at n=1). Zero would make a probe
    overdue before it was ever evaluated — loud about everything is loud about nothing — and a
    duration would be the clock this design is bounded away from."""
    assert Probe(why="w", trigger=lambda n, c: True, to="x/personal").horizon is None, \
        "no probe may acquire a deadline it never declared"
    for bad in (0, -1, 2.5, "10 minutes", True):
        try:
            Probe(why="w", trigger=lambda n, c: True, to="x/personal", horizon=bad)
            raise AssertionError(f"a horizon of {bad!r} must be refused at construction")
        except (ValueError, TypeError):
            pass


def test_the_device_is_started_on_demand():
    shim = _Shim()
    assert not shim.running, "a shim starts with its device asleep"
    assert shim.presence == NEVER_BOOTED, "presence is NEVER_BOOTED before any poke"
    out = shim.deliver({"id": "e1", "body": {"hi": 1}})
    assert out == "handled" and shim.running and shim.started == 1
    assert shim.presence == ONLINE, "presence is ONLINE after poke"
    # A second delivery does NOT restart the device — it is already awake.
    shim.deliver({"id": "e2"})
    assert shim.started == 1, "the device is woken once, then stays awake"


def test_a_shim_with_no_start_hook_refuses_loudly():
    class _NoStart(BaseShim):
        @property
        def device_id(self) -> str:
            return "nostart"
    try:
        _NoStart().deliver({"id": "e"})
        raise AssertionError("a shim delivered to with no _start_device must refuse loudly (CP1)")
    except NotImplementedError:
        pass


def test_it_is_a_shim():
    shim = _Shim()
    assert isinstance(shim, CoreValuesMixin), "a shim must compose the core values (Law 2)"
    assert [v.id for v in shim.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]


# --- bounce-to-sender teeth (ticket undeliverable-mail-returns-to-sender) ------

class _VerbDevice:
    """A device that declares specific verbs — the bounce tests deliver unknown ones."""
    def __init__(self):
        self.handled = []
    def declared_verbs(self):
        return {"ping": self._ping}
    def _ping(self, envelope):
        self.handled.append(envelope)
        return "pong"


class _VerbShim(BaseShim):
    """A shim whose device declares verbs, wired to a spy bus for bounce tests."""
    def __init__(self, bus=None):
        super().__init__(bus=bus)
        self._verb_device = _VerbDevice()
        self.set_diagnostic_receiver(None)
    @property
    def device_id(self):
        return "verb_device"
    def _start_device(self):
        return self._verb_device


class _OverrideShim(BaseShim):
    """A shim that overrides handle_bounce — proves the override fires."""
    def __init__(self, bus=None):
        super().__init__(bus=bus)
        self.bounces_handled = []
    @property
    def device_id(self):
        return "override_device"
    def _start_device(self):
        return _Woken()
    def handle_bounce(self, bounce_envelope):
        self.bounces_handled.append(bounce_envelope)
        return {"handled": True, "custom": True}


def test_bounce_fires_on_unknown_verb():
    """Delivering a message with an unknown verb bounces it back to the sender via the bus
    instead of raising NotImplementedError."""
    bus = _SpyBus()
    shim = _VerbShim(bus=bus)
    envelope = {"id": "e1", "sender": "alice", "addressee": "verb_device",
                "verb": "nonexistent", "body": {}}
    result = shim.deliver(envelope)
    assert result["bounced"] is True, f"expected bounce, got {result}"
    assert result["to"] == "alice", "bounce goes to the original sender"
    assert len(bus.posted) == 1, "exactly one bounce message posted"
    bounce = bus.posted[0]
    assert bounce["to"] == "alice" and bounce["sender"] == "verb_device"
    assert bounce["body"]["is_bounce"] is True, "bounce carries the guard flag"
    assert "nonexistent" in bounce["body"].get("original_verb", "")


def test_handle_bounce_default_emits_diagnostic():
    """The default handle_bounce emits a diagnostic (Law 7) and returns handled=False."""
    bus = _SpyBus()
    shim = _VerbShim(bus=bus)
    bounce_env = {"id": "b1", "sender": "target", "body": {
        "is_bounce": True, "reason": "no verb foobar", "original_verb": "foobar"}}
    result = shim.deliver(bounce_env)
    assert result["handled"] is False, "default handle_bounce says handled=False"
    diags = shim.held_diagnostics()
    bounce_diags = [d for d in diags if d.get("gate") == "bounced_mail"]
    assert len(bounce_diags) == 1, f"expected 1 bounced_mail diagnostic, got {len(bounce_diags)}"
    assert bounce_diags[0]["values"]["reason"] == "no verb foobar"


def test_handle_bounce_override_fires():
    """A device that overrides handle_bounce gets the override called instead of the default."""
    bus = _SpyBus()
    shim = _OverrideShim(bus=bus)
    bounce_env = {"id": "b2", "sender": "target", "body": {
        "is_bounce": True, "reason": "test bounce", "original_verb": "x"}}
    result = shim.deliver(bounce_env)
    assert result["handled"] is True and result.get("custom") is True, \
        "override handle_bounce must fire and return its own result"
    assert len(shim.bounces_handled) == 1, "override received the bounce envelope"
    assert shim.bounces_handled[0] is bounce_env


def test_is_bounce_guard_prevents_infinite_loop():
    """A message with is_bounce=True and an unknown verb raises instead of bouncing again."""
    bus = _SpyBus()
    shim = _VerbShim(bus=bus)
    bounce_env = {"id": "e2", "sender": "alice", "addressee": "verb_device",
                  "verb": "nonexistent", "body": {"is_bounce": True, "reason": "prior bounce"}}
    result = shim.deliver(bounce_env)
    assert result["handled"] is False, "is_bounce envelope triggers handle_bounce, not re-bounce"
    assert len(bus.posted) == 0, "no second bounce posted — the guard holds"


# --- last-known capture and persistence teeth (ticket the-shim-remembers-last-known) ------

def test_last_known_is_none_before_boot():
    """A shim that has never booted has no last-known record — None, not a guess."""
    shim = _Shim()
    assert shim.last_known is None, "last_known must be None before any poke"


def test_last_known_captured_on_boot(tmp_path):
    """After _ensure_device, last_known is populated with presence and a timestamp."""
    shim = _Shim()
    shim._diagnostic_instance = 0
    shim.deliver({"id": "e1", "body": {"hi": 1}})
    lk = shim.last_known
    assert lk is not None, "last_known must be populated after boot"
    assert lk["presence"] == "ONLINE", f"presence must be ONLINE, got {lk['presence']}"
    assert "timestamp" in lk and len(lk["timestamp"]) > 10, \
        "last_known must carry a real ISO timestamp"


def test_last_known_persisted_to_instance_space(tmp_path, monkeypatch):
    """The last-known record is written atomically to instance-space and matches in-memory."""
    import json as _json
    from cairn.tools.base import address as _addr
    monkeypatch.setattr(_addr, "ROOTS", {"instance": tmp_path})
    shim = _Shim()
    shim.deliver({"id": "e1", "body": {}})
    device_name = shim.diagnostic_device
    lk_file = tmp_path / "devices" / device_name / "0" / "last_known.json"
    assert lk_file.exists(), f"last_known.json must exist at {lk_file}"
    on_disk = _json.loads(lk_file.read_text())
    assert on_disk == shim.last_known, \
        f"on-disk record must match in-memory: disk={on_disk}, mem={shim.last_known}"


# --- device contract teeth (ticket the-shim-declares-its-device-contract) ------

def test_contract_default_is_empty():
    """The default contract returns empty verb and pane lists — a shim with no override
    is honest, not broken."""
    shim = _Shim()
    c = shim.declared_contract()
    assert c == {"verbs": [], "panes": []}, f"default contract must be empty, got {c}"


def test_contract_readable_without_waking():
    """declared_contract() is readable from a never-booted shim without triggering
    _ensure_device — the contract is static, not a wake-to-discover."""
    shim = _Shim()
    assert shim.presence == NEVER_BOOTED, "shim must start never-booted"
    c = shim.declared_contract()
    assert shim.presence == NEVER_BOOTED, \
        f"declared_contract() must not wake the device — presence is {shim.presence}"
    assert isinstance(c, dict), "contract must be a dict"


def test_contract_override_declares_capabilities():
    """A concrete shim that overrides declared_contract() returns its device's capabilities."""
    class _ContractShim(BaseShim):
        @property
        def device_id(self):
            return "contracted"
        def declared_contract(self):
            return {"verbs": ["ping", "status"], "panes": ["console", "chat"]}
    shim = _ContractShim()
    c = shim.declared_contract()
    assert c["verbs"] == ["ping", "status"], f"verbs mismatch: {c['verbs']}"
    assert c["panes"] == ["console", "chat"], f"panes mismatch: {c['panes']}"
    assert shim.presence == NEVER_BOOTED, "contract read must not wake the device"


def _main() -> int:
    for check in (test_a_pulse_fires_due_probes_and_holds_the_rest,
                  test_a_batch_does_not_die_on_one_bad_probe,
                  test_an_armed_and_never_fired_probe_is_loud,
                  test_a_horizon_is_declared_not_inferred,
                  test_the_device_is_started_on_demand,
                  test_a_shim_with_no_start_hook_refuses_loudly,
                  test_it_is_a_shim,
                  test_bounce_fires_on_unknown_verb,
                  test_handle_bounce_default_emits_diagnostic,
                  test_handle_bounce_override_fires,
                  test_is_bounce_guard_prevents_infinite_loop,
                  test_last_known_is_none_before_boot,
                  test_contract_default_is_empty,
                  test_contract_readable_without_waking,
                  test_contract_override_declares_capabilities):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — BaseShim: probes fire, device wakes on demand, bounce returns to sender, last-known captured, contract declared")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

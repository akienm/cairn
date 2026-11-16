"""Proof for ticket 8e7c7add550f: the probe-carry proof's live-bus poke is marked as testing.

Measured 2026-11-16: the live trouble lane held 8 mail-testing-ad7caca4d54c-recipient-*-has-no-
receiver troubles, raised by the live bus's _raise_undeliverable_bounce on 2026-11-13. Each came
from test_probe_carry.py's end-to-end tooth. That tooth posts to a fresh testing-named recipient
on the live bus, from a fresh testing-named watcher. Its names are testing-marked but the body is
not. No shim answers either name, so the bus returns the letter, the return cannot land, and the
bus raises it. The bus disposes of a returned letter only when the body carries the testing mark
(b3386f431ae3). Ticket ad7caca4d54c meant "every name and body marked as testing"; the console
and chat pane proofs mark their bodies, and this one did not.

  1. every letter the end-to-end tooth posts on the live bus carries a well-formed testing mark,
     read back from the live bus by its envelope id;
  2. the end-to-end tooth itself still passes: one fire, one poke, the carrier's text intact.

The world: the live bus through its published client (RULE 1), wrapped so each post the tooth
makes is recorded. The tooth's own names are fresh testing-marked ones per run.

    python3 cairn/tools/base/proofs/test_the_probe_carry_poke_is_marked_as_testing.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"8e7c7add550f": {
    "1": "test_every_letter_the_tooth_posts_is_marked",
    "2": "test_the_end_to_end_tooth_still_passes"}}

PROOF_TIMEOUT_S = 300

_CARRY = Path(__file__).with_name("test_probe_carry.py")


def _carry_module():
    spec = importlib.util.spec_from_file_location("base_probe_carry_under_proof_8e7c", _CARRY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Recording:
    """The live bus, every post recorded as (to, body, envelope id)."""

    def __init__(self, bus):
        self._bus, self.posts = bus, []

    def post(self, *args, **kwargs):
        env = self._bus.post(*args, **kwargs)
        self.posts.append((kwargs.get("to"), kwargs.get("body"), (env or {}).get("id")))
        return env

    def __getattr__(self, name):
        return getattr(self._bus, name)


def _run_tooth():
    from cairn.tools.bus_client import bus_client
    real = bus_client.reach
    box: dict = {}

    def reach(*a, **k):
        box["bus"] = _Recording(real(*a, **k))
        return box["bus"]

    bus_client.reach = reach
    try:
        _carry_module().test_the_shim_fires_the_carrier_against_the_pulse_context()
    finally:
        bus_client.reach = real
    return box["bus"]


def test_every_letter_the_tooth_posts_is_marked():
    from cairn.tools.base import testing_mark
    rec = _run_tooth()
    assert rec.posts, "the tooth posted nothing"
    for to, body, env_id in rec.posts:
        assert to and to.startswith("testing-"), to
        assert testing_mark.mark_of(body) is not None, f"an unmarked body went to {to}: {body}"
        got = [e for e in rec.read(to=to, channel="personal") if e.get("id") == env_id]
        assert got, f"envelope {env_id} to {to} is not on the live bus"
        assert testing_mark.mark_of(got[0].get("body")) is not None, got[0]


def test_the_end_to_end_tooth_still_passes():
    rec = _run_tooth()
    assert len(rec.posts) == 1, rec.posts
    assert rec.posts[0][1]["text"] == "ticket detected at PROVEME as {'id': 'T-7', 'gate': 'PROVEME'}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

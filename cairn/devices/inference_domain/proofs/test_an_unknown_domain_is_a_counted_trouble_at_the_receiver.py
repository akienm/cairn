"""Proof: an ask for a domain row that does not exist is a counted trouble at inference_domain's
own address (ticket e9a2d8ae7d43).

RULED 2026-10-05 (decision 8h), Akien: *"Any component that gets a request that it can't fill,
that's a trouble ticket ... every requester that gets something they can't do should throw a
ticket. Because we need to stop people throwing things at them that they can't do."* The
receiver raises it, at its own address, and each repeat counts. The first case he named is
this one: codemother asked inference_domain for a 'codemother' row that does not exist about
1,000 times a day, and every ask was refused in silence. ``_domain_dressed`` raises
``RouteRefused`` before any call is made. The host-refusal lane raises a trouble (ticket
ea4a6151300f); this pre-call lane raised nothing, so the bad caller stayed invisible.

A trouble is not a row: the refusal still costs no host call and lands no cache row, exactly
as ``test_inference_domain.py``'s ``test_an_unknown_domain_is_refused_before_any_spend`` pins.

Teeth a hollow build could not pass:
  1. an ask for an unknown domain raises ONE trouble through the receiver's own sink, whose
     identity names the domain asked for and whose detail names the caller, and the caller
     still gets RouteRefused with no host call;
  2. the same unknown domain asked twice raises the SAME identity twice (the trouble device's
     drain folds on identity, so that is the counter), and a different unknown name raises a
     DIFFERENT identity;
  3. a raiser that explodes does not change the caller's answer: RouteRefused still arrives
     with its own words;
  4. an ask for a domain that exists raises no trouble at all (no alarm on a fillable ask).

    python3 cairn/devices/inference_domain/proofs/test_an_unknown_domain_is_a_counted_trouble_at_the_receiver.py
"""
from __future__ import annotations

import contextlib
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain import domain  # noqa: E402
from cairn.devices.inference_domain.machines.route.route import RouteRefused  # noqa: E402

PROVES = {"e9a2d8ae7d43": {
    "1": "test_an_unknown_domain_raises_ONE_trouble_at_the_receiver_and_still_refuses",
    "2": "test_a_repeat_raises_the_SAME_identity_and_another_name_a_DIFFERENT_one",
    "3": "test_a_raiser_that_explodes_does_not_change_the_callers_answer",
    "4": "test_a_domain_that_exists_raises_NO_trouble",
}}

_RUN = uuid.uuid4().hex[:8]
_SCRATCH = contextlib.ExitStack()
_HELD: list[str] = []


def _table() -> str:
    if not _HELD:
        _HELD.append(_SCRATCH.enter_context(domain.scratch_cache("unknown_domain_trouble")))
    return _HELD[0]


class _Sink:
    """The receiver's own diagnostic sink, injected so the proof files nothing into the live
    trouble store (a proof seeding the tree it reads)."""

    def __init__(self, *, explode: bool = False):
        self.raised, self.explode = [], explode

    def emit(self, *a, **k):
        return {}

    def raise_trouble(self, identity, *, why, detail=None, now=None):
        if self.explode:
            raise RuntimeError("fixture: the trouble lane is down, deliberately")
        self.raised.append({"identity": identity, "why": why, "detail": detail or {}})
        return {}


class _Resolver:
    def __init__(self):
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        return {"answer": {"text": "fixture"}, "cost": 1.0, "horizon": "",
                "provenance": {"host": "fixture-host"}}


def _ask(name: str, sink: _Sink, r: _Resolver):
    return domain.resolve({"q": f"unknown_domain_{_RUN}", "kind": "generate", "prompt": "p",
                           "domain": name}, resolver=r, table=_table(), sink=sink,
                          caller="unknown-domain-fixture")


def test_an_unknown_domain_raises_ONE_trouble_at_the_receiver_and_still_refuses():
    sink, r = _Sink(), _Resolver()
    try:
        _ask(f"no-such-vertical-{_RUN}", sink, r)
        raise AssertionError("an unknown domain must still refuse")
    except RouteRefused as e:
        assert f"no-such-vertical-{_RUN}" in str(e)
    assert r.calls == 0, "the refusal must land before the host is touched"
    assert len(sink.raised) == 1, (
        f"an ask the receiver cannot fill raised {len(sink.raised)} troubles, not one: "
        f"{sink.raised}")
    t = sink.raised[0]
    assert f"no-such-vertical-{_RUN}" in t["identity"], (
        f"the trouble's identity does not name the domain asked for: {t['identity']!r}")
    assert (t["detail"].get("caller") or {}).get("identity") == "unknown-domain-fixture", (
        f"the trouble does not name the caller that asked: {t['detail']}")


def test_a_repeat_raises_the_SAME_identity_and_another_name_a_DIFFERENT_one():
    sink, r = _Sink(), _Resolver()
    for name in (f"repeat-{_RUN}", f"repeat-{_RUN}", f"other-{_RUN}"):
        with contextlib.suppress(RouteRefused):
            _ask(name, sink, r)
    ids = [t["identity"] for t in sink.raised]
    assert len(ids) == 3, f"each refused ask must raise, so the drain can count it: {ids}"
    assert ids[0] == ids[1], f"a repeat raised a different identity, so it would not count: {ids}"
    assert ids[2] != ids[0], f"a different unknown name folded into the first one's trouble: {ids}"


def test_a_raiser_that_explodes_does_not_change_the_callers_answer():
    sink, r = _Sink(explode=True), _Resolver()
    try:
        _ask(f"lane-down-{_RUN}", sink, r)
        raise AssertionError("an unknown domain must still refuse when the trouble lane is down")
    except RouteRefused as e:
        assert f"lane-down-{_RUN}" in str(e), f"the refusal lost its own words: {e}"
    assert r.calls == 0


def test_a_domain_that_exists_raises_NO_trouble():
    sink, r = _Sink(), _Resolver()
    out = domain.resolve({"q": f"known_domain_{_RUN}", "kind": "generate", "prompt": "p"},
                         resolver=r, table=_table(), sink=sink, caller="unknown-domain-fixture")
    assert out["answer"] is not None and r.calls == 1, out
    assert sink.raised == [], f"a fillable ask raised a trouble: {sink.raised}"


def _main() -> int:
    checks = [
        test_an_unknown_domain_raises_ONE_trouble_at_the_receiver_and_still_refuses,
        test_a_repeat_raises_the_SAME_identity_and_another_name_a_DIFFERENT_one,
        test_a_raiser_that_explodes_does_not_change_the_callers_answer,
        test_a_domain_that_exists_raises_NO_trouble,
    ]
    # THE WHOLE RUN IN A FIXTURE WORLD, as test_inference_domain.py does: tooth 4's fillable ask
    # writes a task ticket beside the trail, and with the roots left live this proof's first
    # runs landed fixture tickets in the LIVE ~/.cairn/logs/inference_domain/0/tickets
    # (measured 2026-10-06). In process, so the one scratch table closes here, not at shutdown.
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.tools.base import address as _address
    _move_roots = getattr(domain, "set_diagnostic_roots", None)
    if _move_roots:
        _move_roots({**_address.ROOTS, "instance": scratch_dir("cairn_unknown_domain_proof_")})
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        if _move_roots:
            _move_roots(None)
        _SCRATCH.close()
    print("green — inference_domain: an unfillable domain ask is one counted trouble at the receiver, naming the caller; the refusal is unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

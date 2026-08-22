"""Proof for the inference_domain TRAIL — does a call at this door leave a record on disk?

Ticket ``an-inference-call-logs-that-it-started``, the first child of Akien's 2026-08-18
brief: *"every single everyting is supposed to log major boundry crossings and state
changes... but starting an inference call sure should. a probe firing at a gate crossing
should. the logs are the picture of what just happened when we have a problem."*

WHAT IS UNDER TEST, AND WHAT IS DELIBERATELY NOT. The mechanism half — the record shape, the
receiver, the address arithmetic — was composed whole from ``DiagnosticBase`` and was proved
at its own address before this build began. What is new here is one class, one instance, and
three ``emit`` calls in ``resolve``, so the teeth below ask exactly the questions that only
this device can answer:

  - A MISS LANDS A LINE, AND THE LINE NAMES THE FAR END. The one place the host is touched
    writes a record carrying which vertical rode, which host answered, over which path, with
    which model — read by opening the file and parsing the bytes back.
  - THE DEVICE NAMED ITSELF. The trail resolves to ``logs/inference_domain/0/`` with nothing
    in ``domain.py`` spelling that name — it is derived from the class's ``__module__``. A
    build that hand-spelled it would pass every other tooth here and fail this one.
  - A HIT RECORDS THE CROSSING THAT DID NOT HAPPEN. Without it a trail of misses alone is
    unreadable against the meter: it looks identical whether the hits went unrecorded or
    never happened.
  - A REFUSAL LEAVES A LINE, AND THE EXCEPTION STILL REACHES THE CALLER AS THE VERY INSTANCE
    THE RESOLVER RAISED. Observing a failure may not become handling it.
  - THE TRAIL AND THE METER AGREE. Miss lines in the trail == ``verdict='miss'`` rows in the
    store, over the same window. Two records of one event that disagree are worse than one.
    And the tooth carries its OWN NON-VACUITY WITNESS: it re-runs itself with the trail
    pointed at a different world and asserts the two numbers then DIVERGE, so a pass cannot be
    two zeros agreeing or an equality that could not have failed.
  - AN UNREPORTED ENDPOINT KEY IS ABSENT, NOT NULL. "The resolver did not report a provider"
    and "the resolver reported no provider" are different facts about the host.

ISOLATION COMES FROM ``set_diagnostic_roots``, NEVER FROM A SUBSTITUTED RECEIVER, and the
distinction is the difference between proving the mechanism and proving the scaffolding.
``DiagnosticBase`` says it in its own words: a proof wanting isolation "should reach for this
— it leaves the mechanism under test intact, where wiring a hand-built receiver would quietly
prove the receiver instead of the default." So this file contains no receiver of its own, and
every trail assertion reads bytes back off disk rather than trusting ``emit``'s return value.
Grepping this file for the receiver-substituting setter is an acceptance instrument, and it
must come back empty — which is why the name is described here rather than spelled: the first
draft asserted the count was zero in a sentence that made it one, and the instrument measured
its own claim about itself. The setter is the ``set_diagnostic_``-prefixed sibling of
``set_diagnostic_roots``; the exact string lives in ``cairn/tools/base/diagnostic.py`` and in
the ticket's acceptance criterion, and it deliberately does not live here.

Requires the db_domain provisioning (an OS-named LOGIN CREATEDB role); uses an ephemeral table
dropped on the way out and a fresh temp instance-root per tooth, so neither the real
``inference_calls`` store nor the live logs tree is touched.

    python3 cairn/devices/inference_domain/proofs/test_an_inference_call_logs_that_it_started.py
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.inference_domain import domain
from cairn.devices.tester.scratch import scratch_dir
from cairn.tools.base import address

_NONCE = f"{os.getpid()}_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
_TABLE = f"_probe_trail_{_NONCE}"


class _Resolver:
    """The injected host seam, returning a provenance shaped like the real one.

    Defaults mirror ``ollama_resolver`` plus the two keys ``_routed_resolver`` adds when rungs
    were skipped, because those five are exactly what a trail line is supposed to carry back.
    ``calls`` counts, so a tooth can tell "the trail cost a host call" from "it did not" —
    compile-once is a standing contract this build must leave alone.
    """

    def __init__(self, provenance: dict | None = None, cost: float = 7.0):
        self.calls = 0
        self._cost = cost
        self._provenance = provenance if provenance is not None else {
            "host": "http://hex.local:11434",
            "path": "/api/generate",
            "model": "qwen2.5:7b",
            "provider": "ollama",
            "route_walked": ["local", "hex"],
            "counters": {"prompt_eval_count": 41},
        }

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        return {"answer": {"text": f"answer {self.calls}"}, "cost": self._cost,
                "provenance": dict(self._provenance)}


class _Refusing(_Resolver):
    """The seam RAISING rather than returning — the shape every refusal has at this door."""

    def __init__(self, error: Exception, **kw):
        super().__init__(**kw)
        self._error = error

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        raise self._error


@contextlib.contextmanager
def _isolated_trail():
    """Point the device's OWN trail at a fresh instance-root and hand back that root.

    The seam is ``set_diagnostic_roots``: the receiver under test stays exactly the one a live
    call would use, and only the universe its address resolves in moves. Restored to the live
    world on the way out, unconditionally — a proof that leaves a device pointed at a deleted
    temp tree has broken the next tooth in the same process.
    """
    tmp = scratch_dir("cairn_trail_")
    domain.set_diagnostic_roots({**address.ROOTS, "instance": tmp})
    try:
        yield tmp
    finally:
        domain.set_diagnostic_roots(None)


def _lines(trail_dir: Path) -> list[dict]:
    """The trail read the way a human at a terminal reads it: list the directory, parse the files.

    Never ``emit``'s return value. A tooth that asserts against the returned record proves the
    function built a dict and says nothing about whether anything reached disk — which is the
    entire claim this ticket makes.
    """
    if not trail_dir.exists():
        return []
    from cairn.tools.base.breadcrumb_log import RECORD_NAME
    out = []
    jsonl = trail_dir / RECORD_NAME
    if jsonl.is_file():
        out.extend(json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip())
    for p in sorted(trail_dir.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def test_a_miss_lands_a_line_that_names_the_far_end():
    """The crossing Akien's brief names in so many words — and the line's contents."""
    with _isolated_trail() as tmp:
        trail = domain.diagnostic_trail()

        # THE DEVICE NAMED ITSELF. Nothing in domain.py spells "inference_domain" for the
        # trail; the address is derived from the door class's __module__. A build that
        # hand-spelled it passes every other tooth in this file and fails here.
        assert trail == tmp / "logs" / "inference_domain" / "0", (
            f"the trail must resolve to the device's own berth in the logs tree, got {trail}")

        # The before-witness, taken inside the proof rather than remembered from a shell.
        assert not trail.exists(), f"the fixture world must start with no trail: {trail}"

        r = _Resolver()
        out = domain.resolve({"q": f"miss_{_NONCE}"}, resolver=r, table=_TABLE)
        assert out["hit"] is False and r.calls == 1

        records = _lines(trail)
        assert len(records) == 1, f"one miss must leave exactly one line, got {records}"
        rec = records[0]
        assert rec["gate"] == "miss", f"the gate must name the branch: {rec}"
        assert rec["home"] == "sent", f"the record must have reached a home, not been held: {rec}"
        assert rec["source"] == "inference_domain.domain.resolve", rec
        assert rec["pointer"] == domain.canonical_digest(out["canonical"]), (
            f"the pointer must be a digest of the canonical, joinable to the store's canonical column: {rec}")

        v = rec["values"]
        assert v["host"] == "http://hex.local:11434", f"the line must name the host: {v}"
        assert v["path"] == "/api/generate" and v["model"] == "qwen2.5:7b", v
        assert v["provider"] == "ollama" and v["route_walked"] == ["local", "hex"], v
        assert v["domain"] == "general", f"the line must say which vertical rode: {v}"

        # THE SPLIT, AND IT IS ALSO A REGRESSION TOOTH. Spend belongs to the meter: it is
        # already on the row this line points at, and a number kept in two records can drift
        # apart — which is the very thing the agreement criterion below forbids. It is a
        # regression tooth because the first draft DID carry spend, and the hit line came back
        # from the receiver degraded: a stored cost is a postgres Decimal and the trail is a
        # JSONL file. So the absence below is load-bearing twice over.
        for meters in ("cost", "avoided", "counters"):
            assert meters not in v, (
                f"spend is the METER's record, not the trail's — {meters!r} must not be on a "
                f"trail line: {v}")
        assert "values_unwritable" not in rec, (
            f"every value on a trail line must survive the JSONL receiver intact: {rec}")


def test_a_hit_records_the_crossing_that_did_not_happen():
    """A trail carrying only misses cannot be read against the meter: it looks the same whether
    the hits went unrecorded or never happened. And the trail must not cost a host call."""
    with _isolated_trail():
        trail = domain.diagnostic_trail()
        r = _Resolver()
        tag = {"q": f"hit_{_NONCE}"}
        domain.resolve(dict(tag), resolver=r, table=_TABLE)
        hit = domain.resolve(dict(tag), resolver=r, table=_TABLE)

        assert hit["hit"] is True and r.calls == 1, (
            "compile-once is a standing contract — observing the door must not touch the host")

        records = _lines(trail)
        assert [rec["gate"] for rec in records] == ["miss", "hit"], (
            f"both branches must be on the trail, in order: {records}")
        v = records[1]["values"]
        assert v["served_from"], f"a hit's line says where the answer was served from: {v}"
        assert v["domain"] == "general", v
        assert "values_unwritable" not in records[1], (
            "a hit's values must survive the JSONL receiver — this is where a postgres Decimal "
            f"off the stored row degraded the line in the first draft: {records[1]}")


def test_a_refusal_leaves_a_line_and_the_exception_reaches_the_caller_unchanged():
    """Observing a failure may not become handling it. The tooth asserts identity, not type:
    the caller must get back the very instance the resolver raised."""
    with _isolated_trail():
        trail = domain.diagnostic_trail()
        boom = RuntimeError("the host refused this ask")
        r = _Refusing(boom)

        try:
            domain.resolve({"q": f"refused_{_NONCE}"}, resolver=r, table=_TABLE)
            raise AssertionError("a raising resolver must PROPAGATE — recording is not handling")
        except AssertionError:
            raise
        except RuntimeError as caught:
            assert caught is boom, (
                f"the trail must not swallow or substitute the refusal, got {caught!r}")
        assert r.calls == 1, "the ask must have reached the seam"

        records = _lines(trail)
        assert len(records) == 1 and records[0]["gate"] == "refused", (
            f"a refused ask must leave exactly one line, naming the branch: {records}")
        v = records[0]["values"]
        assert v["refused"] == "RuntimeError", f"the line must name the exception TYPE: {v}"
        assert "the host refused this ask" in v["detail"], f"and carry its own words: {v}"
        assert v["domain"] == "general", v


def test_an_endpoint_key_the_resolver_did_not_report_is_absent_not_null():
    """Two different facts about the host, and a record that collapses them is a record that
    cannot be counted: a null `provider` reads as "it reported nothing" where the truth is
    "it reported no such thing"."""
    with _isolated_trail():
        trail = domain.diagnostic_trail()
        r = _Resolver(provenance={"host": "http://loopback:11434"})
        domain.resolve({"q": f"sparse_{_NONCE}"}, resolver=r, table=_TABLE)

        v = _lines(trail)[0]["values"]
        assert v["host"] == "http://loopback:11434", v
        for missing in ("path", "model", "provider", "route_walked"):
            assert missing not in v, (
                f"{missing!r} was never reported by the resolver and must be ABSENT, not null: {v}")


def test_the_trail_and_the_meter_agree():
    """Miss lines on the trail == verdict='miss' rows in the store, over the same window.

    THE COUNT IS OF ROWS, never of ``yield_report``'s ``calls`` — that reader has counted
    refusals as calls since 2026-08-17 and is a different number by a known unclosed defect
    (the device charter's own clause-10 residue). Counting it here would make the tooth agree
    with a bug.

    THE NON-VACUITY WITNESS IS THE SECOND HALF, and it is not a comment about the tooth, it is
    the tooth exercising its own failure. Two zeros agree; so does an equality between numbers
    that could not have differed. So after asserting agreement, the trail is pointed at a
    DIFFERENT world for one more miss and the two numbers are asserted to DIVERGE. If the miss
    emit were removed, the first half would fail in exactly the way the second half here
    demonstrates is reachable.
    """
    with _isolated_trail() as tmp:
        trail = domain.diagnostic_trail()
        tag = f"agree_{_NONCE}"
        r = _Resolver()

        # Three distinct questions (three misses), one repeat (a hit), one refusal — so the
        # trail carries all three gates and the count cannot be right by having only one kind.
        for n in range(3):
            domain.resolve({"q": f"{tag}_{n}"}, resolver=r, table=_TABLE)
        domain.resolve({"q": f"{tag}_0"}, resolver=r, table=_TABLE)
        try:
            domain.resolve({"q": f"{tag}_bad"}, resolver=_Refusing(RuntimeError("nope")),
                           table=_TABLE)
        except RuntimeError:
            pass

        def trail_misses() -> int:
            return sum(1 for rec in _lines(trail) if rec["gate"] == "miss")

        def row_misses() -> int:
            rows = store.read(_TABLE, where="canonical LIKE %s AND verdict = 'miss'",
                              params=(f"%{tag}%",))
            return len(rows)

        assert trail_misses() == 3, f"the trail must carry one line per host call: {_lines(trail)}"
        assert row_misses() == 3, "and the store must carry one row per host call"
        assert trail_misses() == row_misses(), "the trail and the meter must agree"

        # THE WITNESS. Send the next crossing's line to a different world; the row still lands
        # in the same table. The equality above must now be false — which is what makes it a
        # measurement rather than a tautology.
        elsewhere = scratch_dir("cairn_trail_elsewhere_")
        try:
            domain.set_diagnostic_roots({**address.ROOTS, "instance": elsewhere})
            domain.resolve({"q": f"{tag}_9"}, resolver=r, table=_TABLE)
        finally:
            domain.set_diagnostic_roots({**address.ROOTS, "instance": tmp})

        assert row_misses() == 4, "the store recorded the fourth host call"
        assert trail_misses() == 3, "the trail did not — its line went to the other world"
        assert trail_misses() != row_misses(), (
            "the agreement tooth must be capable of failing; if this passes trivially the "
            "equality above proved nothing")


def _probe():
    from cairn.devices.inference_domain.probes import an_inference_call_logs_that_it_started as p
    return p


def _line(gate: str, canonical: str, ts: str = "2026-08-18T15:00:00-06:00") -> dict:
    """One trail line as the receiver writes it. Built to the SHAPE the real writer produces —
    the teeth above already assert that shape against bytes off disk, so these fixtures are
    tied to the producer rather than agreeing only with the reader that consumes them.
    The pointer is now a canonical digest, matching the real writer's output."""
    return {"ts": ts, "us": "000000", "source": "inference_domain.domain.resolve",
            "gate": gate, "pointer": domain.canonical_digest(canonical), "values": {}, "home": "sent"}


def _row(canonical: str, verdict: str = "miss",
         created: str = "2026-08-18T15:00:00-06:00") -> dict:
    return {"canonical": canonical, "verdict": verdict,
            "created": datetime.fromisoformat(created)}


def test_the_probe_cannot_clear_before_it_can_fire():
    """A watch that clears at n=0 is not a watch — an empty store disagrees with an empty trail
    about nothing, so the population floor is the whole non-vacuity tooth here."""
    p = _probe()
    empty = p.judge([], [], trail_exists=True)
    assert empty["store_misses"] == 0 and not empty["in_store_not_in_trail"]
    assert p._enough({"corpus": empty}) is False, (
        "a zero population must NOT clear the watch — it has never had the chance to fire")
    assert p._trigger(None, {"corpus": empty}) is False, "and nothing empty is a finding"


def test_the_probe_fires_on_a_call_the_trail_missed():
    """Shape 1: the store recorded the call and the picture does not show it."""
    p = _probe()
    s = p.judge([_line("miss", "{\"q\":1}")],
                [_row("{\"q\":1}"), _row("{\"q\":2}")])
    assert p._trigger(None, {"corpus": s}) is True, f"a missing trail line must fire: {s}"
    assert len(s["in_store_not_in_trail"]) == 1 and s["in_store_not_in_trail"][0]["short_by"] == 1, (
        f"and it must name WHICH call, not just how many: {s}")
    assert s["in_store_not_in_trail"][0]["canonical"] == domain.canonical_digest("{\"q\":2}"), (
        f"the finding carries the digest so it joins back to the store: {s}")
    assert p._enough({"corpus": s}) is False, "a disagreeing corpus must never clear"


def test_the_probe_fires_on_a_trail_line_the_store_never_got():
    """Shape 2 — the opposite drift, and it is watched because a trail that can invent a call
    is a trail whose agreement means nothing."""
    p = _probe()
    s = p.judge([_line("miss", "{\"q\":1}"), _line("miss", "{\"q\":3}")], [_row("{\"q\":1}")])
    assert p._trigger(None, {"corpus": s}) is True, f"an invented call must fire: {s}"
    assert len(s["in_trail_not_in_store"]) == 1 and s["in_trail_not_in_store"][0]["short_by"] == 1, s
    assert s["in_trail_not_in_store"][0]["canonical"] == domain.canonical_digest("{\"q\":3}"), s


def test_the_probe_sees_the_absence_that_looks_like_nothing():
    """Shape 3: no trail file at all. Invisible to any check that reads the trail's CONTENTS,
    which is exactly how a stopped emitter stays quiet — so it is its own reported field."""
    p = _probe()
    s = p.judge([], [_row("{\"q\":1}")], trail_exists=False)
    assert s["no_trail_at_all"] is True, f"a missing trail beside real calls is its own shape: {s}"
    assert p._trigger(None, {"corpus": s}) is True
    assert "NO TRAIL FILE" in p._carry({"corpus": s})["finding"], (
        "and the carry must say so in words, not leave the reader to infer it from a list")


def test_the_probe_counts_repeats_rather_than_comparing_sets():
    """One question can legitimately miss twice once its horizon expires. A set comparison
    would call that agreement, which is a hole shaped exactly like a dropped emit."""
    p = _probe()
    s = p.judge([_line("miss", "{\"q\":1}")], [_row("{\"q\":1}"), _row("{\"q\":1}")])
    assert s["store_misses"] == 2 and s["trail_misses"] == 1, s
    assert len(s["in_store_not_in_trail"]) == 1 and s["in_store_not_in_trail"][0]["short_by"] == 1, (
        f"the second miss of the same question must be visible as short_by 1: {s}")
    assert s["in_store_not_in_trail"][0]["canonical"] == domain.canonical_digest("{\"q\":1}"), s


def test_the_probe_ignores_everything_before_its_era():
    """2,616 rows written before the seam existed have no trail line and never could have.
    Counting them would make the probe fire forever about a world that no longer exists."""
    p = _probe()
    s = p.judge([], [_row("{\"q\":\"old\"}", created="2026-08-17T09:00:00-06:00")])
    assert s["post_era_rows"] == 0 and s["store_misses"] == 0, f"pre-era rows are not the population: {s}"
    assert p._trigger(None, {"corpus": s}) is False, "and they must not fire the watch"


def test_the_probe_reads_the_address_the_device_declares():
    """A probe carrying its own copy of the berth goes on reading an empty file if the device
    ever moves, and reports a catastrophe that is really a stale constant. So the live read
    must follow the device — measured by moving the world and watching the read follow."""
    p = _probe()
    with _isolated_trail() as tmp:
        r = _Resolver()
        domain.resolve({"q": f"follows_{_NONCE}"}, resolver=r, table=_TABLE)
        s = p.survey_the_corpus()
        assert s["trail_exists"] is True, (
            f"the probe must have found the trail at the device's CURRENT berth ({tmp}): {s}")
        assert s["trail_misses"] >= 1, (
            f"and read the line the device just wrote there: {s}")


def _cleanup():
    """Drop this run's ephemeral cache table and its registry row — leave no fixtures."""
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_a_miss_lands_a_line_that_names_the_far_end,
        test_a_hit_records_the_crossing_that_did_not_happen,
        test_a_refusal_leaves_a_line_and_the_exception_reaches_the_caller_unchanged,
        test_an_endpoint_key_the_resolver_did_not_report_is_absent_not_null,
        test_the_trail_and_the_meter_agree,
        test_the_probe_cannot_clear_before_it_can_fire,
        test_the_probe_fires_on_a_call_the_trail_missed,
        test_the_probe_fires_on_a_trail_line_the_store_never_got,
        test_the_probe_sees_the_absence_that_looks_like_nothing,
        test_the_probe_counts_repeats_rather_than_comparing_sets,
        test_the_probe_ignores_everything_before_its_era,
        test_the_probe_reads_the_address_the_device_declares,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        domain.set_diagnostic_roots(None)
        _cleanup()
    print("green — an inference call leaves a record in the device's own trail, and the trail "
          "agrees with the meter")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

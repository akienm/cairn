"""A green seal tells codemother, and nothing is lost if she is not listening.

Charter + why: cairn/devices/tester/intention+why.json
Ticket:        CairnCommons/tickets/1accdc1781aa-a-green-seal-crosses-the-boat-it-proves.json

THE SEAM THIS END OWNS. ``1accdc1781aa`` runs between three components, so its clauses
live in three proofs and the PROVED crossing names all three (``proven_by`` is read as
one-or-many precisely because a seam has ends in more than one place). Codemother's end —
what she DOES with a seal — is
``cairn/devices/codemother/proofs/test_codemother.py``. The harbor's end — what the door
REFUSES — is ``cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py``.
This file is the tester's end, and its question is narrower than either: **does the seal
say so, and does saying so cost the seal anything?**

WHAT BORE IT, and it is a measurement rather than a worry. On 2026-09-07 twelve tickets
stood at PROVEME with a green seal already sitting on the proof each of them named. Not
one of them was blocked: the crossing simply required a hand to remember, and twelve times
nobody did. The seal was already the event — it just never spoke. So the fix is not a
sweeper that periodically looks for forgotten boats (that is a poller, and the poller is
the thing this system keeps declining to build); it is one message at the moment the
verdict lands.

AND THE TELLING MUST NEVER BE ABLE TO COST A SEAL. That is clause (4), and it is the
half that decides whether this is safe to leave switched on: the record of truth is the
VALIDATION, the message is a courtesy to a device that may not be running, and a courtesy
that can unwind a record of truth is a Law 7 defect wearing a helpful face. So the seal
lands first, the telling is wrapped, and an undelivered message waits in the bus until
codemother's next beat takes it. Both halves are measured below, and the second one is
measured with codemother genuinely absent — not stubbed absent, actually never wired.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.devices.tester.scratch import scratch_dir
from cairn.devices.tester.validation_store import (
    read_validations,
    standing_seal,
    validations_path_for,
)
from cairn.tools.base import bus_client
from cairn.devices.db_domain import store

# Clause (1) is the message; clause (4) is the seal surviving codemother's absence.
# Clauses (2) and (5) are codemother's own (cairn/devices/codemother/proofs/test_codemother.py);
# clause (3) is the harbor door's (machines/harbor_master/proofs/test_clearance.py).
PROVES = {
    "1accdc1781aa": {
        "1": "test_a_green_seal_posts_EXACTLY_ONE_sealed_message_carrying_all_four_fields",
        "4": "test_with_codemother_UNWIRED_the_seal_stands_and_her_next_beat_drains_the_mail",
    },
}

# Every fixture table this run mints, dropped in the runner's ``finally``. The bus's own
# proofs do it this way and the reason is the same: a table named after a nonce is not a
# leak the next run trips over, it is a leak the DATABASE accumulates forever.
_NONCE = uuid.uuid4().hex[:8]
_TABLES: list[str] = []

_TOOTH = "test_nothing_is_nothing"


def _fixture_proof(tag: str) -> Path:
    """A component-shaped scratch directory holding one trivially green proof.

    COMPONENT-SHAPED, not merely a file in a folder, because the seal's address is DERIVED
    from the proof's path (``proofs/<stem>.py`` -> ``../validations/<stem>.json``). A proof
    that does not sit in a ``proofs/`` directory would seal to a different shape than every
    real proof does, and the field this tooth checks is exactly that address.

    ``history.json`` is here so that "no crossing faked" is a thing that can be READ off
    disk at the end rather than inferred from a return value.
    """
    comp = scratch_dir(tag) / "a_fixture_component"
    (comp / "proofs").mkdir(parents=True, exist_ok=True)
    proof = comp / "proofs" / "test_fixture.py"
    proof.write_text(
        f"def {_TOOTH}():\n"
        "    assert True\n"
        f'    print("PASS: {_TOOTH}")\n\n\n'
        'if __name__ == "__main__":\n'
        f"    {_TOOTH}()\n", encoding="utf-8")
    (comp / "history.json").write_text("[]", encoding="utf-8")
    return proof


def _fixture_bus() -> BusDevice:
    """A bus on an ephemeral table. ``table`` is injectable for exactly this."""
    bus = BusDevice(table=f"_seal_ann_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    return bus


def _seal_through_the_cli(proof: Path, bus: BusDevice, reached: list | None = None) -> int:
    """Run ``cairn test --seal <proof>`` for real, with its bus pointed at ``bus``.

    WHAT IS SUBSTITUTED IS THE BUS, AND NOTHING ELSE. The tester runs, the verdict is
    taken, the store's door is fired and the announcement is composed by the same
    ``_announce_seals`` the command always calls — only the table the envelope lands in is
    a fixture's. Patching the announcement itself would leave the tooth measuring a mock's
    obedience; patching ``reach`` leaves it measuring the command.

    ``reach`` is patched on the MODULE rather than on the import site because
    ``_announce_seals`` imports it inside the function body, so the name is looked up on
    ``bus_client`` at the moment of the call.

    ``reached``, when given, collects the device names the command asked for — see the
    stub below for why that argument is no longer thrown away.
    """
    from cairn.devices.tester import cli

    reached = reached if reached is not None else []

    saved = bus_client.reach

    def _reach(*devices):
        # THE ARGUMENT IS RECORDED, NOT DISCARDED, AND THAT IS A FIX. This stub was
        # ``lambda *_devices: bus`` — it swallowed the one thing the call says, which is
        # WHICH DEVICES THE ANNOUNCEMENT WIRES. No tooth in this file could see that
        # ``_announce_seals`` reached codemother and nothing else, so no tooth could see
        # that the crossing it exists to start had no door to knock on. The instrument was
        # structurally incapable of failing on the defect it was written to guard, which is
        # the hollow shape Law 8 names — and the underscore on ``_devices`` was the whole
        # of it. Measured 2026-09-09, on the first LIVE fire, in the one place a fixture
        # bus never looks: the real one, where harbor_master has to be wired for
        # codemother to cross anything.
        reached.extend(devices)
        return bus

    bus_client.reach = _reach
    try:
        return cli.main(["--seal", str(proof)])
    finally:
        bus_client.reach = saved


def _sealed_messages(bus: BusDevice) -> list[dict]:
    """Every ``sealed`` envelope addressed to codemother, read off the RECORD.

    ``read`` and not ``undelivered``: the record is the full truth and says what was POSTED
    (Law 7), while ``undelivered`` answers a different question — what has not yet ARRIVED.
    Counting "exactly one message" off the delivery view would make the count depend on
    whether anyone happened to be listening, which is the very thing clause (4) varies.
    """
    return [env for env in bus.read(to="codemother", channel="personal")
            if env.get("verb") == "sealed"]


# --- clause (1) -------------------------------------------------------------

def test_a_green_seal_posts_EXACTLY_ONE_sealed_message_carrying_all_four_fields():
    """FALSIFIER CLAUSE (1), verbatim: ``cairn test --seal <fixture proof>`` green produces
    exactly one ``sealed`` message in a fixture bus carrying proof path, verdict,
    source_fingerprint, validations path.

    EXACTLY ONE IS HALF THE CLAUSE AND IT IS THE HALF THAT BITES. A handler that fires per
    proof AND per record, or a retry that re-posts, reads green against "at least one" and
    would hand codemother the same crossing twice — and the second one arrives at a boat
    that is already PROVED, where it is either a spurious refusal or, worse, a crossing out
    of a terminal.

    AND EACH FIELD IS CHECKED AGAINST THE WORLD, NOT AGAINST ITSELF. The validations path
    is opened; the fingerprint is compared to the one in the record that just landed. A
    tooth asserting only that four keys are present passes over a message full of empty
    strings, which is precisely how this field was wrong when the tooth was written: the
    address was composed with ``validations_path_for_artifact`` and pointed one directory
    deeper than the seal ever lands.
    """
    proof = _fixture_proof("seal_ann_one_")
    bus = _fixture_bus()

    rc = _seal_through_the_cli(proof, bus)
    assert rc == 0, f"the fixture proof did not run green through `cairn test --seal` (rc={rc})"

    messages = _sealed_messages(bus)
    assert len(messages) == 1, (
        f"expected EXACTLY ONE sealed message for one sealed proof, got {len(messages)}: "
        f"{[m.get('body', {}).get('proof') for m in messages]}")

    body = messages[0].get("body") or {}
    assert body.get("proof") == str(proof), (
        f"the message names {body.get('proof')!r}, not the proof that was sealed ({proof})")
    assert body.get("verdict") == "green", (
        f"a green run announced verdict {body.get('verdict')!r} — the receiver decides "
        "whether to cross on this field, so a wrong one is a wrong crossing")

    trail = read_validations(str(proof))
    assert trail, "nothing landed in the validations trail — there was no seal to announce"
    landed = trail[-1]["evidence"]["source_fingerprint"]
    assert body.get("source_fingerprint") == landed, (
        f"the message carries fingerprint {body.get('source_fingerprint')!r} but the record "
        f"that just landed carries {landed!r} — the receiver re-checks drift against this, "
        "so a stale one silently authorises a crossing over moved code")

    where = body.get("validations_path") or ""
    assert where == validations_path_for(str(proof)), (
        f"the message points at {where!r}; the seal's derived address is "
        f"{validations_path_for(str(proof))!r}")
    assert os.path.isfile(where), (
        f"the message points at {where!r}, which is not a file — a field naming nothing on "
        "disk is indistinguishable from a real address to whoever reads it")

    print("PASS: test_a_green_seal_posts_EXACTLY_ONE_sealed_message_carrying_all_four_fields")


def test_THE_ANNOUNCEMENT_WIRES_THE_DOOR_THE_CROSSING_WILL_KNOCK_ON():
    """Clause (1)'s missing half, and the one the FIRST LIVE FIRE found (2026-09-09).

    Every tooth above measures the ENVELOPE — one message, four fields, each checked
    against the world. All of them read green on a run where not one boat crossed, because
    none of them asks the other question the announcement answers: WHO IS WIRED WHEN IT
    LANDS. ``post`` fires the addressee's delivery hook synchronously, in the announcing
    process, so codemother heard this seal inside ``cairn test`` rather than on her own
    beat — and there ``harbor_master`` did not exist. She refused every boat with the right
    words on her own trail; the command printed SEALED; the ticket stayed at PROVEME. A
    seam whose whole claim is "a green seal crosses the boat it proves" had a green proof
    on every part of the sentence except the verb.

    SO THE TOOTH IS ABOUT THE ARGUMENT, NOT THE MESSAGE. It reds if the announcement stops
    naming the harbor — which is exactly the edit that would silently restore the defect,
    and is the natural edit, because reaching only the device you are addressing is what
    ``reach`` reads like it means.

    AND IT REDS IF THE RING IS NOT FLUSHED. The fallback for a receiver that did not handle
    the message is the bus STORE, which is where ``_check_mail`` looks (``bus.undelivered``)
    — not the mail directory, and not the in-memory ring, which dies with this process. On
    the live run the envelope was afterwards in no channel at all: neither crossed nor
    waiting, simply gone. Both halves are one claim — the announcement leaves the crossing
    either DONE or RECOVERABLE, never neither.
    """
    proof = _fixture_proof("seal_ann_wired_")
    bus = _fixture_bus()
    reached: list = []

    rc = _seal_through_the_cli(proof, bus, reached)
    assert rc == 0, f"the fixture proof did not run green through `cairn test --seal` (rc={rc})"

    assert reached, (
        "the announcement reached no device at all — with nothing wired the post cannot "
        "be delivered and cannot be recovered")
    assert "codemother" in reached, (
        f"the announcement did not reach its addressee; it reached {reached!r}")
    assert "harbor_master" in reached, (
        f"the announcement reached {reached!r} — codemother is told, but the harbor door "
        "her crossing knocks on is not wired in the process where she will hear it, so "
        "every boat is refused with \"'harbor_master' is not wired on this bus\" and the "
        "command still prints SEALED. Measured on the live fire of 2026-09-09")

    assert not bus._ring, (
        f"{len(bus._ring)} envelope(s) were still in the in-memory ring when the command "
        "returned. The ring is batch-written by the ground loop's beat and a sealing run "
        "never fires one, so an envelope left here dies with the process: a message that "
        "was neither acted on nor stored. `bus.undelivered` reads the STORE")

    assert len(_sealed_messages(bus)) == 1, (
        "the flush must not cost the record its single message, nor duplicate it")

    print("PASS: test_THE_ANNOUNCEMENT_WIRES_THE_DOOR_THE_CROSSING_WILL_KNOCK_ON")


def test_a_run_that_seals_NOTHING_announces_nothing():
    """The clause-(1) neighbour: no seal, no message. Without it the tooth above passes on
    a handler that posts unconditionally, and a diagnostic run — the default, fired many
    times an hour — would be minting crossing attempts against boats nobody sealed.
    """
    proof = _fixture_proof("seal_ann_none_")
    bus = _fixture_bus()

    from cairn.devices.tester import cli
    saved = bus_client.reach
    bus_client.reach = lambda *_devices: bus
    try:
        rc = cli.main([str(proof)])          # no --seal: a diagnostic run
    finally:
        bus_client.reach = saved

    assert rc == 0, f"the fixture proof did not run green (rc={rc})"
    assert _sealed_messages(bus) == [], (
        "a run that sealed nothing announced a seal — the announcement is keyed to the "
        "record landing, never to the proof passing")
    print("PASS: test_a_run_that_seals_NOTHING_announces_nothing")


# --- clause (4) -------------------------------------------------------------

def test_with_codemother_UNWIRED_the_seal_stands_and_her_next_beat_drains_the_mail():
    """FALSIFIER CLAUSE (4), verbatim: with no codemother process, a seal still lands green
    and the message is drained by her next ``beat`` -- no seal lost, no crossing faked.

    CODEMOTHER IS NOT STUBBED ABSENT; SHE IS ABSENT. No shim is constructed before the run,
    so the bus has no delivery hook for her and the envelope has nowhere to go at post time.
    That is the real shape of the failure this clause guards: the tester seals at three in
    the morning, nothing is listening, and the question is whether the record of truth
    survives the courtesy failing.

    THEN HER BEAT IS REAL TOO. ``_load_device_shim`` finds the same shim class the ground
    loop would, and ``on_pulse`` is the same entry point a beat calls — it fires her probes,
    wires delivery, and drains the backlog through ``_check_mail``. Nothing here reaches
    into ``_handle_sealed`` directly; if the drain does not happen the way a beat makes it
    happen, this tooth reds.

    AND "NO CROSSING FAKED" IS READ OFF DISK. The fixture proof is named by no ticket at
    all, so a correct drain writes nothing anywhere. ``history.json`` beside the fixture
    component is checked after the beat: still an empty list, because a device that invents
    a crossing for a proof nobody is waiting on is worse than one that drops the message.
    """
    proof = _fixture_proof("seal_ann_unwired_")
    bus = _fixture_bus()

    rc = _seal_through_the_cli(proof, bus)

    # --- the seal stands, with nobody listening ---
    assert rc == 0, f"the seal did not land green with codemother absent (rc={rc})"
    assert standing_seal(str(proof)) is not None, (
        "no seal stands on the proof — the telling was allowed to unwind the record it was "
        "only supposed to describe (Law 7)")
    trail = read_validations(str(proof))
    assert trail and trail[-1]["verdict"] == "green", (
        f"the standing record is {trail[-1]['verdict'] if trail else 'absent'!r}, not green")

    # --- and the message is waiting, not gone ---
    waiting = [env for env in bus.undelivered(to="codemother") if env.get("verb") == "sealed"]
    assert len(waiting) == 1, (
        f"expected the sealed message to be sitting undelivered, found {len(waiting)}. A "
        "folder recorder at ~/.cairn/folders/codemother/ would swallow it into a file and "
        "make this read 0 — that is delivery to somewhere the shim never looks.")

    # --- her next beat takes it ---
    shim = bus_client._load_device_shim("codemother", bus)
    assert shim is not None, "codemother's shim did not load — the drain cannot be measured"
    record = shim.on_pulse(datetime.now(timezone.utc))

    still_waiting = [env for env in bus.undelivered(to="codemother")
                     if env.get("verb") == "sealed"]
    assert still_waiting == [], (
        f"{len(still_waiting)} sealed message(s) survived codemother's beat — the backlog "
        f"drain did not reach them. Pulse record: {record.get('mail')}")

    # --- and nothing was invented on the way through ---
    assert len(_sealed_messages(bus)) == 1, (
        "the record now holds more than one sealed message — the drain re-posted rather "
        "than consumed")
    history = json.loads((proof.parent.parent / "history.json").read_text(encoding="utf-8"))
    assert history == [], (
        f"a crossing was journaled for a proof no ticket names: {history}")

    print("PASS: test_with_codemother_UNWIRED_the_seal_stands_and_her_next_beat_drains_the_mail")


def test_a_bus_THAT_REFUSES_the_telling_still_leaves_the_seal_standing():
    """The other half of clause (4)'s "no seal lost": the failure that RAISES.

    An absent listener is the quiet failure; a bus that throws is the loud one, and it is
    the one that can actually unwind a run — an exception escaping ``_announce_seals`` would
    propagate out of ``main`` after the record had already been written, so the command
    would exit non-zero over a seal that landed perfectly well. Callers read that exit code.
    """
    proof = _fixture_proof("seal_ann_refused_")

    class _RefusingBus:
        def post(self, **_kw):
            raise RuntimeError("the fixture bus refuses this telling on purpose")

    from cairn.devices.tester import cli
    saved = bus_client.reach
    bus_client.reach = lambda *_devices: _RefusingBus()
    try:
        rc = cli.main(["--seal", str(proof)])
    finally:
        bus_client.reach = saved

    assert rc == 0, (
        f"a refused announcement changed the command's verdict (rc={rc}) — the seal landed; "
        "the telling is a courtesy and may not vote")
    assert standing_seal(str(proof)) is not None, (
        "the seal is gone after a refused announcement")
    print("PASS: test_a_bus_THAT_REFUSES_the_telling_still_leaves_the_seal_standing")


TEETH = [
    test_a_green_seal_posts_EXACTLY_ONE_sealed_message_carrying_all_four_fields,
    test_THE_ANNOUNCEMENT_WIRES_THE_DOOR_THE_CROSSING_WILL_KNOCK_ON,
    test_a_run_that_seals_NOTHING_announces_nothing,
    test_with_codemother_UNWIRED_the_seal_stands_and_her_next_beat_drains_the_mail,
    test_a_bus_THAT_REFUSES_the_telling_still_leaves_the_seal_standing,
]


def main() -> int:
    failures = 0
    try:
        for tooth in TEETH:
            try:
                tooth()
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {tooth.__name__}: {type(exc).__name__}: {exc}")
                import traceback
                traceback.print_exc()
    finally:
        try:
            conn = store.connect()
            with conn.cursor() as cur:
                for base in _TABLES:
                    for table in (f"{base}_delivery", base):
                        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                        cur.execute(
                            f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s',
                            (table,))
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        return 1
    print("green — a green seal tells codemother once, with every field, and costs nothing "
          "when nobody is listening")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

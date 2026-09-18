"""mail_probe.py — a probe that answers a device's mail: three lines on the device's side.

WHAT IT COMPOSES (ticket bf146e9e3967, D5). A discovered device already has a mailbox —
``_FeedbackDevice.receive`` (ground_loop/discovered.py) lands every verb-less envelope in
``instance_path(<device>, 0)/tools/data_recorder/inbound`` — and a beat that already pulses
its probes (``BaseShim.on_pulse``). What was missing is the piece between: something that
reads that inbox, does the device's own work on a message, and pokes the sender with the
answer. This is that piece, and a device that wants to answer a kind of mail writes:

    from cairn.tools.base.mail_probe import answers_mail
    def _sleep(body): return <its work>
    PROBE = answers_mail("sleep_token", _sleep, device_file=__file__, why="...", verb="sleep-token")

The device id is derived from the FILE'S ADDRESS, the way ``discovery.device_folders`` derives
it (the probes/ folder's parent) — a probe berths with what it watches, and its address is
its declaration. The roots come from the beat's context (``context["roots"]``), None live, so
a proof can point a fixture device at a fixture instance root without a global.

PENDING is inbound records whose body carries ``key`` and whose envelope has no answered
record yet — the answered recorder beside the inbox is the memory, so a device that is
restarted answers nothing twice. ``while_true`` is on so two tokens in one beat are answered
on consecutive beats instead of the second waiting for the trigger to fall; ``enough`` is
never — a mailbox does not retire. The survey is memoised per pulse with ``probe.once`` under
a key that names the device, because the beat's context is SHARED across every shim and two
devices' inboxes must never be served each other's world.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from cairn.tools.base.address import instance_path
from cairn.tools.base.probe import Probe, once

INBOUND = ("tools", "data_recorder", "inbound")
ANSWERED = ("tools", "data_recorder", "answered")


def device_id_of(device_file: str) -> str:
    """``<device>/probes/<file>.py`` → ``<device>`` — the roster's own rule."""
    return Path(device_file).resolve().parent.parent.name


def _recorder(device_id: str, parts: tuple, roots) :
    from cairn.tools.data_recorder.data_recorder import DataRecorder
    return DataRecorder(instance_path(device_id, 0, roots).joinpath(*parts))


def pending(device_id: str, key: str, roots=None) -> list[dict]:
    """Inbound records carrying ``key`` in their body, not yet answered, in write order."""
    inbox = _recorder(device_id, INBOUND, roots)
    done = {r.get("envelope_id") for r in _recorder(device_id, ANSWERED, roots).read()}
    return [r for r in inbox.read()
            if isinstance(r.get("body"), dict) and key in r["body"]
            and r.get("envelope_id") not in done]


def answers_mail(key: str, handle: Callable[[dict], object], *, device_file: str, why: str,
                 to: str = "cairn", verb: str = "", horizon: int | None = 1000) -> Probe:
    device_id = device_id_of(device_file)
    memo_key = f"mail_probe:{device_id}:{key}"

    def _survey(context: dict) -> list[dict]:
        return once(context, memo_key, lambda: pending(device_id, key, context.get("roots")))

    def _trigger(now, context: dict) -> bool:
        return bool(_survey(context))

    def _carry(context: dict) -> dict:
        record = _survey(context)[0]
        answer = handle(record["body"])
        _recorder(device_id, ANSWERED, context.get("roots")).write({
            "finding": f"answered {key}", "inspector_target": device_id,
            "probe_source": "mail_probe", "envelope_id": record.get("envelope_id"),
            "answer": answer})
        return {key: record["body"][key], "device": device_id, "answer": answer}

    return Probe(why=why, trigger=_trigger, to=to, verb=verb, channel="personal",
                 body={"device": device_id}, carry=_carry, while_true=True, horizon=horizon)

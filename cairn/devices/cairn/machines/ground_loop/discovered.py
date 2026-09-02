"""DiscoveredShim — the always-on front for a device the heartbeat found on DISK.

A device that has never been hand-registered still gets pulsed, because its ``probes/``
folder is its registration (see ``discovery.py``). This shim is what the loop pulses on its
behalf: a plain ``BaseShim`` whose ``probes()`` returns whatever the last discovery pass
handed it.

WHY A SHIM AT ALL, AND NOT THE LOOP FIRING DIRECTLY. Akien's wording was "the ground loop
runs it," and the shortest reading of that is a heartbeat that imports code and calls it.
That reading is the 584aa74 goof — a ground_loop that EXECUTES collapses heartbeat, firing
and scheduling into one device and loses the property the whole design is for: *a probe is
the same unit no matter what fires it.* So discovery changes WHERE THE ROSTER COMES FROM
(disk, every pass) and changes nothing about WHERE FIRING LIVES (the shim, which already
carries crossing-memory, the cleared set, the never-fired horizon, and per-probe error
isolation — none of which the heartbeat should learn a second copy of).

THIS PARAGRAPH USED TO SAY THE ROSTER WAS "UNSTALEABLE", AND THAT WORD WAS FALSIFIED —
recorded here rather than quietly deleted, because the sentence was true of the thing it
named and false about the thing a reader took from it. The ROSTER is genuinely re-read from
disk every pass and cannot go stale. The INTERPRETER READING IT can, and did: on 2026-08-13 a
daemon outlived a file move, so every probe it loaded bound a ``Probe`` class the daemon's
own frame no longer held, ``isinstance`` compared two class objects wearing one name, and
fifteen devices were benched under their own names for 29 hours. An unstaleable list read by
a stale reader is a stale answer. The predicate that now tells those apart lives at
``staleness.py``; the loop now self-restarts on staleness rather than benching devices.

The probe list is REPLACED each pass, not appended: a probe file deleted from disk leaves
the roster on the next beat. The shim's own memories are keyed by ``Probe.identity`` and
survive that replacement, so a watch whose file was merely re-saved does not forget that it
already poked (``BaseShim._was_true`` / ``_cleared`` / ``_first_seen``).

NO PAGE. This shim deliberately does not implement ``_start_device``: it fronts a device
for the BEAT, not for the web surface. A device that wants a page has a real shim of its
own with a real device behind it (``LibrarianShim``, ``GroundLoopShim``), and the loop
prefers that one when both exist — see ``GroundLoopDevice._reconcile``.
"""

from __future__ import annotations

from cairn.tools.base.probe import Probe
from cairn.tools.base.shim import BaseShim, ONLINE


class DiscoveredShim(BaseShim):
    """A disk-discovered device's shim. Holds an id, a folder, and this pass's probes."""

    def __init__(self, device_id: str, folder: str = "", bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._folder = folder
        self._probes: list[Probe] = []
        self._presence = ONLINE  # the shim is the always-on part; there is no heavier process here

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def folder(self) -> str:
        return self._folder

    def probes(self) -> list[Probe]:
        return self._probes

    def set_probes(self, probes: list[Probe], folder: str = "") -> None:
        """Take this pass's discovered probes. Called by the loop before the pulse, so the
        roster a beat fires is the roster that was on disk when that beat started."""
        self._probes = list(probes)
        if folder:
            self._folder = folder

    def _start_device(self):
        """Start a minimal device for mail receipt.

        A discovered device has no heavier process — its probes close over their own data.
        But it DOES receive mail: BaseDevice.receive() records to a DataRecorder, and that
        is the default handler every device gets. A page still needs a concrete shim holding
        a real device (the web server reaches the page through the shim, and a minimal
        feedback device has nothing to page)."""
        return _FeedbackDevice(self._device_id)


class _FeedbackDevice:
    """Minimal device for mail receipt by discovered devices.

    Not a BaseDevice subclass — it has no intention/state/settings to report and
    does not compose CoreValuesMixin (it is not a device in the charter sense, it
    is a mailbox). But it has receive() and device_id, which is all deliver() needs.
    """

    def __init__(self, device_id: str) -> None:
        self._device_id = device_id
        self._recorder = None

    @property
    def device_id(self) -> str:
        return self._device_id

    def _get_recorder(self):
        if self._recorder is None:
            from cairn.tools.data_recorder.data_recorder import DataRecorder
            from cairn.tools.base.address import instance_path
            self._recorder = DataRecorder(
                instance_path(self._device_id, 0) / "tools" / "data_recorder" / "inbound")
        return self._recorder

    def receive(self, envelope: dict) -> dict:
        self._get_recorder().write({
            "finding": envelope.get("why", "bus message received"),
            "inspector_target": self._device_id,
            "probe_source": envelope.get("sender", "unknown"),
            "envelope_id": envelope.get("id"),
            "verb": envelope.get("verb", ""),
            "body": envelope.get("body", {}),
        })
        return {"accepted": True, "device": self._device_id}

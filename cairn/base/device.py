"""BaseDevice — the Form v0 contract, embodied.

Every Cairn device subclasses this. Its whole job, right now, is two things:

  1. Compose ``CoreValuesMixin`` so every device carries CP1-CP6 structurally —
     you cannot be a device without the values (Law 2). This is the composition
     tooth the pin test enforces (proofs/test_composition.py).
  2. Declare the **Form v0 #2 introspection surface** (MAP.md:157): a device
     reports, *in order*, its intention, then its state, then its settings, then
     other things as we build them out. One uniform surface — the same protocol
     the tester probes and the web UI renders, so observability is not a separate
     build. A running device can always be asked what it is FOR; reported
     intention vs filed intention is a drift detector.

NOT carried from the quarry (a deliberate redesign, not an omission):
  - UU's 14 rack methods (who_am_i/capabilities/comms/health/block/halt/recovery
    …). Cairn's contract is the three ordered reports above, not that surface; and
    ``block``/``halt`` are the UU state-model + a word Cairn dropped on purpose.
  - UU's ``DiagnosticBase`` logging machinery (loguru, per-record JSON sinks under
    ``~/.unseen_university/logs/``). Cairn's evidence surface is VALIDATIONS + the
    learning store + journeys, and instance-space is ``~/.cairn/``. When a device
    needs a shared service it is spun off (Form v0 #3), never copied down here.

OPEN EDGE (filed, not faked): the return *shape* of the three reports is loose
(``dict``) on purpose in v0 — it firms up when its consumers exist (the tester
probes it; the web UI renders it; Form #2 says they share one protocol). Pinning a
rigid schema now, with no consumer, would be guessing.

Kept import-light on purpose: no DB, no logging backend, no device boot. Importing
this module must never eager-import a DB-bound one (the boot-order law).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cairn.base.core_values import CoreValuesMixin


class BaseDevice(CoreValuesMixin, ABC):
    """Abstract base for every Cairn device.

    Composes ``CoreValuesMixin`` — every device carries CP1-CP6 structurally (Law
    2, enforced by proofs/test_composition.py). Declares the Form v0 #2 surface:
    ``intention()`` → ``state()`` → ``settings()``, assembled in that order by the
    concrete ``introspect()``.
    """

    @abstractmethod
    def intention(self) -> dict:
        """What this device is FOR — its filed intention, reported live.

        The first thing a device reports (Form v0 #2). Comparing this against the
        device's filed ``intention+why.json`` is the reported-vs-filed drift
        detector — a device that has quietly become something other than its
        charter says shows up here (Law 3: measured, not assumed).
        """

    @abstractmethod
    def state(self) -> dict:
        """The device's current condition — reported second (Form v0 #2).

        Carries the node state-machine vocabulary as that lands (PROVED / LEARNING
        / the ``-ME`` summonses; MAP.md:812). v0: whatever the device can honestly
        say about where it rests right now.
        """

    @abstractmethod
    def settings(self) -> dict:
        """The device's configuration — reported third (Form v0 #2)."""

    def introspect(self) -> dict:
        """Assemble the Form v0 #2 surface, in order: intention, state, settings.

        Concrete on the base so the *ordering* is the contract, not each device's
        discretion (Law 4 — physics, not a convention every device re-implements).
        ``other`` is where later channels (e.g. chat) attach as we build them out;
        empty in v0. This is the single surface the tester probes and the web UI
        renders — one protocol, so observability is not a separate build.
        """
        return {
            "intention": self.intention(),
            "state": self.state(),
            "settings": self.settings(),
            "other": {},
        }

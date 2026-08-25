"""BaseDevice — the Form v0 contract, embodied.

CORRECTED 2026-08-11 (ticket ``device-ness-is-decided-at-the-shim``), and the superseded
words are kept because they were the load-bearing falsehood. This read:

    "Every Cairn device subclasses this."

IT DOES NOT DEFINE DEVICE-NESS AND NEVER DID. Akien ruled the axis on 2026-08-11 — *"a shim
fits TO the device; you + your shim = your device"*, and *"the unit is the FOLDER, not the
registration: a device is a directory with a ``probes/`` subdirectory, its id the
directory's own name."* Calibre was a device with no device code at all, just its shim,
because Calibre itself managed the books; no class read can ever see that member, so
inheritance cannot be the test. MEASURED the same day: twelve components are devices under
the ruling and ELEVEN of them subclass nothing here, while eight things subclass this and
are not on the roster the beat reads — including ``bus`` and ``ground_loop``, the spine.
Exactly one component, ``librarian``, is on both axes and carries a shim class as well.

WHERE THE ANSWER LIVES NOW, so this file points instead of asserting: the predicate is
``cairn/tools/base/deviceness.py`` (``is_device`` / ``fitted_device_ids`` / ``divergence``), and
the membership it composes is ``cairn/devices/ground_loop/discovery.py``'s, which is the mechanism
the ruling created and the one a running loop actually fits shims to
(``ground_loop/loop.py::_reconcile``). The divergence is watched by
``cairn/tools/base/probes/device_claims_match_shims.py``.

WHAT SURVIVES UNTOUCHED, because it was never the same claim: this class's real value is the
UNIFORM INTROSPECTION SURFACE — one protocol the tester probes and the web UI renders — and
that is the SAME axis Akien named. Inheritance was the delivery mechanism, not the value.
So BaseDevice stays subclassable, keeps composing ``CoreValuesMixin`` and ``DiagnosticBase``,
and keeps ``introspect()``'s ordering; three live charters are red by physics on exactly
those and none of them move. What ends is the claim to be the DEFINITION. What it is now:
what an IN-PYTHON device MAY compose.

Its whole job, right now, is two things:

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
    ``~/.unseen_university/logs/``). Cairn's durable evidence is VALIDATIONS + the
    learning store + journeys, and instance-space is ``~/.cairn/``.
    WHAT IS CARRIED (2026-07-22): a Cairn-native, transition-grade EMISSION mechanism —
    ``DiagnosticBase`` (``cairn/tools/base/diagnostic.py``), composed here so every device inherits
    ``emit()`` the way it inherits CP1-CP6. At a gate contact it sends a THIN breadcrumb home to
    CC's shim (the diagnostic mailbox, for now), pointing to the ticket and stamped to the
    microsecond (which indexes the fuller 30-day cache-class logs). The loguru/JSON-sink backend
    is NOT carried — only the µs-stamp mechanism; the intelligence lives in the interpreter that
    crawls, not in the base. This is what would have SPOKEN when ``system_rackmount`` went red
    silently (the gap that motivated it; Law 7).

OPEN EDGE (filed, not faked): the return *shape* of the three reports is loose
(``dict``) on purpose in v0 — it firms up when its consumers exist (the tester
probes it; the web UI renders it; Form #2 says they share one protocol). Pinning a
rigid schema now, with no consumer, would be guessing.

Kept import-light on purpose: no DB, no device boot. Importing this module must never
eager-import a DB-bound one (the boot-order law). ``DiagnosticBase`` is composed here and
is itself stdlib-only (``datetime``), so the emission surface costs nothing at import.

CORRECTED 2026-07-27 (Akien: "that is just flat wrong"). This line read "no DB, no logging
backend, no device boot" — true for a day or two early on, made FALSE by the 2026-07-22
paragraph twelve lines above (``DiagnosticBase`` composed, every device inherits ``emit()``),
and left standing. The damage is not the stale fact, it is the words ON PURPOSE: a transient
absence got written as INTENT, so every later session read "Cairn deliberately has no logging"
as a settled design decision and built accordingly — 7 ``emit()`` call sites in the whole tree,
none in ``bus``, against a map (MAP.md:434) that says every state transition and every boundary
crossing is logged. Law 1 running backwards: instead of an answered question becoming structure,
an UNBUILT thing became a justification. When a comment says "on purpose", it must name the
purpose and the condition that ends it — otherwise it outlives its reason and starts giving orders.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.diagnostic import DiagnosticBase


class BaseDevice(CoreValuesMixin, DiagnosticBase, ABC):
    """Abstract base for every Cairn device.

    Composes ``CoreValuesMixin`` — every device carries CP1-CP6 structurally (Law
    2, enforced by proofs/test_composition.py) — and ``DiagnosticBase``, so every device
    inherits ``emit()`` (the transition-grade diagnostic surface; ``cairn/tools/base/diagnostic.py``).
    Declares the Form v0 #2 surface:
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

        Carries the node state-machine vocabulary as that lands (``PROVED`` — the
        one rest since 2026-07-30, ticket watchme-emits-a-probe dissolved
        the second one — plus the ``-ME`` summonses; MAP.md, "Gates, not
        supervisors"). v0: whatever the
        device can honestly say about where it rests right now.
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

    # --- the web presentation surface: which panes this device OFFERS --------

    def declared_panes(self) -> list[dict]:
        """The surfaces this device OFFERS beyond the STATUS + SETTINGS floor.

        The web presentation surface (``web-server`` ticket, child a) renders a
        device's ACTIVE page as a stack of standard PANES. STATUS + SETTINGS are the
        guaranteed floor — the shim projects them from ``introspect()`` above, so a
        device gets them for free (Form v0 #2). Beyond the floor, a device *declares*
        which panes it fills and provides a HANDLER for each; the handler returns the
        pane's DATA (never HTML — the web server renders; Law 7). This is the reserved
        ``other`` channel made concrete.

        Each descriptor is ``{"kind": str, "label": str, "handler": callable|None}``.
        Panes are a declared LIST, not a fixed enum: a device may offer more than one
        of a kind (the librarian's chat-page + tool-page are two ``interaction`` panes,
        not a special case). A descriptor whose ``handler`` is ``None`` renders ABSENT
        (an offered-but-unwired pane is an honest empty, not a crash).

        Default empty: a device that offers only the floor is honest, not deficient.
        The machinery that ASSEMBLES the page lives in ``BaseShim.active_page`` — one
        home (Law 6), not re-implemented per device.
        """
        return []

    def declared_verbs(self) -> dict[str, "Callable"]:
        """The verbs this device handles — verb name → callable.

        The ONE public menu of what a device accepts (bus-completion child a). A caller
        knows an ADDRESS and a VERB; the method behind the verb is private and gets no
        system-term (Law 6 — the device resolves its own method internally). The shim's
        ``deliver()`` resolves verb → handler through this; an unknown verb goes RED.

        Default empty: a device that declares no verbs refuses all inbound mail, which
        is honest — an empty menu and a missing menu are the same refusal.
        """
        return {}

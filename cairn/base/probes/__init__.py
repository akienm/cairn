"""base/probes/ — the berths of probes THIS component's watches emitted.

Ticket ``watchme-emits-a-probe`` (2026-07-30). A probe berths WITH WHAT IT WATCHES, not with
the ticket it was compiled from (see ``cairn/base/probe.py``'s berthing doctrine): these
watch ``cairn/base``, so they live here, beside it. Each module declares module-level
``PROBE`` — a frozen ``cairn.base.probe.Probe``. The emission gate reads that declaration
without running construction logic it cannot predict.
"""

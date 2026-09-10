"""bus_client/probes/ — the berths of probes THIS tool's watches emitted.

Ticket ``watchme-emits-a-probe`` (2026-07-30). A probe berths WITH WHAT IT WATCHES, not with
the ticket it was compiled from (see ``cairn/tools/base/probe.py``'s berthing doctrine). These
watch the bus client, so when the client left ``cairn/tools/base/`` on 2026-09-09 (ticket
dd8ad9702b49) they came with it — and the move was not a pure rename for them: the probe names
``cairn/tools/bus_client/bus_client.py`` as DATA, in its runner roster and in the proof path it
reads a seal from, so a move that only relocated files would have left it watching an address
nothing occupies. Measured: with those strings left stale the proof's third tooth reds with
"roster names a file that is not there", which is what makes the green afterwards mean
something. Each module declares module-level ``PROBE`` — a frozen ``cairn.tools.base.probe.Probe``.
"""

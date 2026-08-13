"""BREADCRUMB LOG — the durable home DiagnosticBase's records have never had.

WHAT WAS MEASURED (2026-08-12, ticket ``a-record-reaches-disk``, layer 0 of the runtime-spine
trouble). Two findings, both re-measured the day this was built and both still true:

  #4  ``set_diagnostic_receiver`` has NO live caller. One definition, one passthrough
      (``charter/projector.py``), and every other hit under a ``proofs/`` directory. With no
      receiver, ``emit()`` marks the record ``home='held'`` and appends it to an in-memory list
      on a device object inside a process that is about to exit. All 22 live emit sites do this.
  #5  No device-emitted record exists on disk anywhere. A scan of every ``def
      receive_diagnostic`` in class-space found exactly TWO implementations — ``base/shim.py``
      and the ``Mailbox`` next door — and both are in-memory only. ``~/.cairn/logs/`` holds
      ``boot`` (a launcher), ``bash`` (a shell logger) and two shell REDIRECTS of the ground
      loop's stdout; not one is a record a device emitted.

The mechanism was never wrong. ``emit`` is deliberately loud — held-not-dropped is the right
design, and the charter next door has said since it was written that its ``Mailbox`` is "the v0
in-memory STAND-IN for the instance-space breadcrumb log ... NEVER the runtime home (that log is
a filed edge)". This file is that edge, closed. It answers the SAME TWO CONTRACTS the stand-in
answers — ``receive_diagnostic(record)`` and ``records()`` — so ``Inspector.inspect`` composes
over it with no change to ``inspector.py``, which is the strongest available evidence that the
stand-in was honest about what it stood for.

WHY IT IS NOT ``liveness.json``, and why the ticket's own filed edge was refuted rather than
answered. The edge proposed that the ground-loop liveness record was "the obvious candidate and
would collapse two builds into one". It already reaches disk — measured with the loop running,
pid 109150, a current advancing stamp — and it closes NEITHER finding, because neither finding
is about device state. Liveness is an OVERWRITTEN SNAPSHOT: it answers "is the loop alive right
now", and the answer replaces itself every second. This is a TRAIL: a line already written is
never rewritten, which is what makes it a record of truth rather than a second liveness (Law 7).
The two files sit in the same directory and that adjacency is the whole distinction on display.

WHERE IT LANDS, and this is a ruling not a preference. Finding #5 named ``~/.cairn/logs/``,
because that is where it looked. Akien ruled the address question on 2026-08-12, after the
trouble was written, and his test is OWNERSHIP rather than depth: "a file that answers 'what is
true of this machine' lives at the top; a file that answers 'what is true of this device' lives
under ``devices/<name>/<instance>/``" — with ``logs``, ``backups`` and ``venv`` named in the same
breath as legitimately top-level, machine-scoped things. A device's breadcrumb trail is that
device's own state, so it lands in that device's own space, one file per instance. That also
makes Law 6 hold for the FILE and not merely for the code: the bus's records never land in the
ground loop's space, and there is no shared trail for two owners to write into.

THE ADDRESS COMES FROM THE ONE OWNER. ``cairn.tools.base.address.instance_path`` — built 2026-08-12
out of ten hand-spelled derivations, importing ``pathlib`` and nothing else, which is what makes
it a legal floor even here. This module hand-spells nothing; there is no ``Path.home()`` below
and no literal ``.cairn``. The ``roots`` table rides through so a proof writes to a temp
directory instead of seeding the live tree it will later be read against — an acceptance
read-back cannot mean anything if running the proof could have written the file.

PURE APPEND, ON PURPOSE, AGAINST BOTH PRECEDENTS. The two JSONL writers already in the house
rebuild the whole file and ``os.replace`` it: ``learning_block.write_trace`` does it because it
EXPIRES debug records at the write, and ``liveness.write_liveness`` does it because it is
replacing a snapshot. This one expires nothing, so read-modify-write would buy nothing and would
make a record already on disk rewritable. The write is ``open(..., "a")``, one line, closed —
which is what carries the record past the death of the process that wrote it, the single
failure #4 names. No ``fsync``: the close hands the bytes to the OS, and surviving the PROCESS
is the falsifier's bar. Surviving a power cut is a different claim and this file does not make it.

TWO FAILURE MODES, DELIBERATELY DIFFERENT, and the difference is Law 7 read carefully.
An unserializable ``values`` payload DEGRADES: the crossing is still recorded, with the payload
replaced by a named failure, because losing the fact that a gate was crossed is the exact loss
this file exists to end. An I/O failure RAISES: a receiver that cannot write and says nothing is
finding #4 wearing a new face. The second one has a real cost — a raise inside a gate propagates
into the emitting device — and it is taken knowingly rather than swallowed. The runner is not
where it gets softened either (that file is charter-bound to grow no logic); if it ever bites,
that is a finding with a measurement behind it, which is the only thing that should buy a guard.

WHAT IS DELIBERATELY ABSENT. No rotation and no ~30-day evaporation: the charter next door
describes that tier, nothing in the falsifier needs it, and an expiry policy written before a
single record exists is the reverse of build-minimal. No consumer — no probe armed, no Inspector
constructed live, no pane — because nothing has asked to read this yet, and the ticket's own
``watchme`` assigns the standing question ("does it keep reaching disk") to the layer that first
depends on it. No new emit site anywhere: the 22 that exist are the population, and adding more
to make the trail look busy would be the firehose the discipline forbids AND would fake the
measurement.

    python3 cairn/machines/diagnostic_inspector/proofs/test_breadcrumb_log.py     # exit 0 = green
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import instance_path

RECORD_NAME = "diagnostics.jsonl"


class LogUnreadable(Exception):
    """The trail is on disk but could not be read back. Loud rather than partial: a diagnostic
    surface that silently drops the line it could not parse is reporting a world it did not
    read, and the line it drops is the one most likely to matter (Law 7)."""


class BreadcrumbLog:
    """A ``DiagnosticBase`` receiver whose home is the owning device instance's own space.

    Answers the two contracts the in-memory ``Mailbox`` answers, so it drops into the same
    places: ``receive_diagnostic(record)`` to write, ``records()`` to read back. Construction
    touches no disk — the directory is made at the first write, because computing an address
    must not create anything (``cairn.tools.base.address``'s own bound, and Law 6: provisioning is a
    different act with a different owner).
    """

    def __init__(self, device: str, instance: int = 0, *, roots: dict[str, Path] | None = None) -> None:
        self.device = device
        self.instance = instance
        self._path = instance_path(device, instance, roots) / RECORD_NAME

    @property
    def path(self) -> Path:
        """Where the trail lives. Exposed because the acceptance instrument is a human reading
        this file from another shell — an address you cannot ask for is one you have to
        re-derive, which is what put ten copies of it in class-space."""
        return self._path

    def receive_diagnostic(self, record: dict) -> None:
        """Append one breadcrumb, as one JSON line. The contract ``DiagnosticBase.emit`` calls.

        A record whose payload will not serialize is written ANYWAY, with the payload replaced
        by a named failure — the crossing is the thing that must not be lost. Everything else
        is left to fail loudly."""
        try:
            line = json.dumps(record, sort_keys=True)
        except (TypeError, ValueError) as exc:
            degraded = {k: v for k, v in record.items() if k != "values"}
            degraded["values"] = {}
            degraded["values_unwritable"] = (
                f"the payload could not be serialized ({type(exc).__name__}: {exc}) — the "
                f"crossing is recorded, the payload is not: {record.get('values')!r}")
            line = json.dumps(degraded, sort_keys=True, default=repr)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def records(self) -> list[dict]:
        """The trail, in the order it was written. The contract ``Inspector.inspect`` consumes.

        An absent trail is an EMPTY trail, not an error: nothing has crossed a gate yet, which
        is a true and common state. A trail that exists and will not parse is an error, named
        by line number — see ``LogUnreadable``."""
        if not self._path.exists():
            return []
        out: list[dict] = []
        for n, line in enumerate(self._path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError as exc:
                raise LogUnreadable(
                    f"{self._path}: line {n} is not readable JSON ({exc}). The trail is not "
                    f"silently truncated at it — the raw line is: {line!r}") from exc
        return out

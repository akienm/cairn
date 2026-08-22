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

WHERE IT LANDS — ``~/.cairn/logs/<device>/<instance>/``, ruled by Akien on 2026-08-18, and this
paragraph is the correction of the one that stood here before. That paragraph read "this is a
ruling not a preference" and sent the trail to ``devices/<name>/<instance>/`` on the strength of
his 2026-08-12 OWNERSHIP test. The test was quoted correctly and the conclusion was still wrong,
which is worth saying plainly because a superseded ruling left standing in confident prose is how
the next reader re-derives a dead address from a document that sounds authoritative.

The two rulings COMPOSE. 2026-08-12 named ``logs``, ``backups`` and ``venv`` in one breath as
legitimately top-level machine-scoped things, so it had already settled that ``logs`` IS a root;
what it never said was what the inside of it looks like. 2026-08-18 says: *"in
~/.cairn/logs/<device>/<instance>/<whatever else> so the path mirrors the code tree"* — and the
segments under ``logs`` are an INDEX, not a second ownership claim. The ownership test itself is
untouched: what is TRUE of a device (its state) still lives under ``devices/<name>/<instance>/``;
what HAPPENED to it lives here.

AND THE WHY IS RETENTION, which is what makes the two addresses different rather than redundant:
*"easy to delete everything in the logs tree over 30 days old in one go."* One root is one
deletion crossing nobody's gate; fourteen trails scattered through fourteen devices' own spaces
would be fourteen sweeps, each reaching into a space its owner gates. So the move does not weaken
Law 6 for the FILE, it is the thing that keeps the coming sweep from breaking it. What the old
paragraph got right survives unchanged: one file per instance, the bus's records are the bus's,
and there is no shared trail for two owners to write into.

WHY IT SITS AT THE FLOOR AND NOT IN ``diagnostic_inspector`` (moved 2026-08-18, ticket
``a-device-logs-without-being-wired``). Because ``DiagnosticBase`` — a TOOL, inherited by every
device — now constructs one by default, and a tool that imported a machine would be the
complexity axis running backwards. Same shape and same why as the ``ROOTS`` table's own lowering
out of ``skill_block`` on 2026-08-12: it was already right, and "what it lacked was an address
the rest of the system could stand on". The inspector is unaffected — it imports this from here,
which is a machine importing a tool, the direction that was always legal.

THE ADDRESS COMES FROM THE ONE OWNER. ``cairn.tools.base.address.log_path`` — built 2026-08-12
out of ten hand-spelled derivations, importing ``pathlib`` and nothing else, which is what makes
it a legal floor even here. This module hand-spells nothing; there is no ``Path.home()`` below
and no literal ``.cairn``. The ``roots`` table rides through so a proof writes to a temp
directory instead of seeding the live tree it will later be read against — an acceptance
read-back cannot mean anything if running the proof could have written the file.

PURE APPEND, ON PURPOSE, AGAINST BOTH PRECEDENTS — and then ONE FILE PER EMISSION (2026-08-19,
ticket ``an-emission-is-one-file-named-by-its-pointer``), which is MORE append-only, not less:
a written emission file is never reopened at all, where the appended trail was reopened by every
later write. The shape change also gives per-record mtime, which makes per-record expiry
expressible — Akien's 2026-08-18 "easy to delete everything over 30 days old in one go" can now
act on individual emissions rather than on an entire device's history. ``records()`` tolerates
both shapes during the retention window: the standing ``diagnostics.jsonl`` is read first, then
per-file emissions sorted by filename. The previous design (the paragraph that stood here) was
right when it was written: the two JSONL writers already in the house rebuilt the whole file and
``os.replace``'d it, and this one appended instead, which was the stronger shape for a trail.
The change is not a correction — it is a grain change driven by the filename carrying the task.

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
    python3 cairn/tools/base/proofs/test_device_logs_unwired.py                   # exit 0 = green
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import log_path

RECORD_NAME = "diagnostics.jsonl"

_SAFE = re.compile(r"[^a-zA-Z0-9_]")


def _emission_filename(record: dict) -> str:
    ts_str = record.get("ts", "")
    try:
        dt = datetime.fromisoformat(ts_str)
        utc = dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        utc = datetime.now(timezone.utc)
    stamp = utc.strftime("%Y%m%d.%H%M%S") + f".{utc.microsecond:06d}"
    source = _SAFE.sub("_", record.get("source", "unknown"))
    gate = _SAFE.sub("_", record.get("gate", "unknown"))
    return f"{stamp}.{source}.{gate}.json"


class LogUnreadable(Exception):
    """The trail is on disk but could not be read back. Loud rather than partial: a diagnostic
    surface that silently drops the line it could not parse is reporting a world it did not
    read, and the line it drops is the one most likely to matter (Law 7)."""


class BreadcrumbLog:
    """A ``DiagnosticBase`` receiver whose home is that device instance's berth in the logs tree.

    Answers the two contracts the in-memory ``Mailbox`` answers, so it drops into the same
    places: ``receive_diagnostic(record)`` to write, ``records()`` to read back. Construction
    touches no disk — the directory is made at the first write, because computing an address
    must not create anything (``cairn.tools.base.address``'s own bound, and Law 6: provisioning is a
    different act with a different owner).

    ONE FILE PER EMISSION (ticket ``an-emission-is-one-file-named-by-its-pointer``, 2026-08-19):
    each ``receive_diagnostic`` call writes a single JSON file named by its UTC-normalised stamp,
    source, and gate — not a line appended to a shared trail. ``records()`` tolerates BOTH
    shapes during the retention window: the standing ``diagnostics.jsonl`` is read first (its
    records predate all per-file emissions), then per-file emissions sorted by filename.
    """

    def __init__(self, device: str, instance: int = 0, *, roots: dict[str, Path] | None = None) -> None:
        self.device = device
        self.instance = instance
        self._dir = log_path(device, instance, roots)

    @property
    def path(self) -> Path:
        """Where the trail lives — the directory holding per-emission files. Exposed because
        the acceptance instrument is a human reading this directory from another shell."""
        return self._dir

    def receive_diagnostic(self, record: dict) -> None:
        """Write one emission as one file. The contract ``DiagnosticBase.emit`` calls.

        A record whose payload will not serialize is written ANYWAY, with the payload replaced
        by a named failure — the crossing is the thing that must not be lost. Everything else
        is left to fail loudly."""
        try:
            body = json.dumps(record, sort_keys=True)
        except (TypeError, ValueError) as exc:
            degraded = {k: v for k, v in record.items() if k != "values"}
            degraded["values"] = {}
            degraded["values_unwritable"] = (
                f"the payload could not be serialized ({type(exc).__name__}: {exc}) — the "
                f"crossing is recorded, the payload is not: {record.get('values')!r}")
            body = json.dumps(degraded, sort_keys=True, default=repr)
        self._dir.mkdir(parents=True, exist_ok=True)
        target = self._dir / _emission_filename(record)
        target.write_text(body + "\n", encoding="utf-8")

    def records(self) -> list[dict]:
        """The trail, in the order it was written. The contract ``Inspector.inspect`` consumes.

        An absent trail is an EMPTY trail, not an error: nothing has crossed a gate yet, which
        is a true and common state. A trail that exists and will not parse is an error, named
        by file — see ``LogUnreadable``.

        Tolerates both shapes: the old ``diagnostics.jsonl`` (read first, its records predate
        all per-file emissions) and individual ``.json`` emission files sorted by filename."""
        if not self._dir.exists():
            return []
        out: list[dict] = []
        jsonl = self._dir / RECORD_NAME
        if jsonl.is_file():
            for n, line in enumerate(jsonl.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError as exc:
                    raise LogUnreadable(
                        f"{jsonl}: line {n} is not readable JSON ({exc}). The trail is not "
                        f"silently truncated at it — the raw line is: {line!r}") from exc
        for p in sorted(self._dir.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except ValueError as exc:
                raise LogUnreadable(
                    f"{p}: not readable JSON ({exc}).") from exc
        return out

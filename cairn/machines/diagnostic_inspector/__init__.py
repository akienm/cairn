"""diagnostic_inspector — the smart reader of DiagnosticBase's dumb breadcrumbs.

See ``inspector.py``. An INSPECTOR that reacts to a probe, applies FILTERS to the log,
and produces FINDINGS — json whose audience is CC. Its remit (charter): save CC tokens
exploring an issue (the debugging analog of the prebuild step), and get better over time.
"""

from cairn.machines.diagnostic_inspector.inspector import (
    CompletenessRegistry,
    Inspector,
    Mailbox,
    by_gate,
    by_pointer,
)

__all__ = ["Inspector", "by_pointer", "by_gate", "CompletenessRegistry", "Mailbox"]

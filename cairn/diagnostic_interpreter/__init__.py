"""diagnostic_interpreter — the smart reader of DiagnosticBase's dumb breadcrumbs.

See ``interpreter.py``. Instantiates I-complete-diagnostic-on-first-pass: a report
that resolves the issue on the first pass, plus the learning-loop that folds each
forced-second-run's miss into the next report's completeness.
"""

from cairn.diagnostic_interpreter.interpreter import (
    CompletenessRegistry,
    Mailbox,
    assemble,
)

__all__ = ["assemble", "CompletenessRegistry", "Mailbox"]

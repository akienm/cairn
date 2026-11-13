"""The install inspector and gate (ticket bdd0ed77930f).

A box's install is measured, not remembered. CHECKS lists the install checks; each is a
'module:function' string or a callable (functools.partial included, so a proof can aim one at a
scratch repo) shaped `check(dry_run=...) -> {id, status, detail}`, or a list of those (the
host-seam install()). inspect() runs every check with dry_run=True, writes nothing, and returns
the reds: every status but already_applied, and a check that raises, its exception in the detail.
installed() is the gate: (False, reds) while any red stands, (True, []) once all are green.
The installer's fix_reds calls each red check once with dry_run=False.
"""

from __future__ import annotations

import functools
import importlib
from typing import Callable

GREEN = "already_applied"

CHECKS: list = [
    "cairn.devices.recovery.machines.installer.installer:install",
    "cairn.devices.recovery.machines.installer.installer:ensure_journal_merge_driver",
    "cairn.devices.recovery.machines.installer.installer:ensure_skill_links",
    "cairn.devices.recovery.machines.installer.installer:ensure_dev_extra",
    "cairn.devices.recovery.machines.installer.installer:check_spawn_interpreter",
]


def resolve(check) -> Callable:
    """A 'module:function' string becomes its function; a callable is returned as it is."""
    if callable(check):
        return check
    module, _, name = str(check).partition(":")
    return getattr(importlib.import_module(module), name)


def name_of(check) -> str:
    fn = check
    while isinstance(fn, functools.partial):
        fn = fn.func
    return str(check) if isinstance(check, str) else getattr(fn, "__name__", repr(check))


def results_of(check, **kw) -> list[dict]:
    """Call one check; a raise is a failed result (Law 7: loud, never swallowed), a list yields each item."""
    try:
        out = resolve(check)(**kw)
    except Exception as exc:  # noqa: BLE001 -- a raising check IS a red, carrying its exception
        return [{"id": name_of(check), "status": "failed",
                 "detail": f"{type(exc).__name__}: {exc}"}]
    return list(out) if isinstance(out, (list, tuple)) else [out]


def measure(checks=None) -> list[tuple]:
    """[(check, [result, ...])] with every check run dry. Writes nothing."""
    return [(c, results_of(c, dry_run=True)) for c in (CHECKS if checks is None else checks)]


def red_of(results: list[dict]) -> list[dict]:
    return [r for r in results if r.get("status") != GREEN]


def inspect(checks=None) -> list[dict]:
    """Every red across the checks, measured with dry_run=True."""
    return [r for _, results in measure(checks) for r in red_of(results)]


def installed(checks=None) -> tuple[bool, list[dict]]:
    """The gate: (False, reds) while any red stands, (True, []) once every check is green."""
    reds = inspect(checks)
    return (not reds), reds

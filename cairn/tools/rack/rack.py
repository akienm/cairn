"""rack — which devices exist, read from folder names alone (ticket a808e21d646f).

A device is a folder directly under ``cairn/devices/``, fronted by its shim (Akien, 2026-08-13:
"a DEVICE is a top level thingie. it's it's own process ... it goes in the rack"). A
``probes/`` folder no longer makes anything a device: measured 2026-09-30, that rule named
42 "devices" — tools such as base, question and artifact among them — against 13 rack
folders.

Two questions, two functions, both answered from paths and never from device code:

- ``rack(root)`` — the roster: every ``cairn/devices/<d>/`` with its ``shim.py``, or None
  where it has none. A shimless folder is a device without a front, listed by name, never
  dropped.
- ``shim_of(name, root)`` — the mail address: the ``shim.py`` that answers to ``name``. A
  machine a device holds keeps its own address (harbor_master, held by the cairn device since
  6d667ccebfeb, has 83 probes posting to it and self-serves its mail), so this resolves
  ``cairn/devices/<d>/machines/<name>/shim.py`` too. The roster is narrower than the address
  book on purpose; narrowing the roster must not cut a delivery address.
- ``answers_as(folder)`` / ``folder_of(name)`` — the name a device answers to on the command
  line and the bus, when it is not its folder's. The outline names a device's folder and its
  name apart (11.4: ``cairn/devices/inferenceproxy/``, "Device name on the command line and
  bus: inference"; 11.3 the same for dbproxy and database). The folder stays the identity the
  rack lists and every root's address follows; the declared name is one more entry in the
  address book, read from the device's own charter (``answers_as``), so a name is declared once,
  at the device, and never in a table here (ticket f942a413f26d).
"""

from __future__ import annotations

import json
from pathlib import Path

_SKIP = {"__pycache__"}


def repo_root() -> Path:
    """The class-space root this tool sits in — derived from its own address, never configured."""
    return Path(__file__).resolve().parents[3]


def _devices_dir(root: Path | str | None) -> Path:
    return (Path(root) if root is not None else repo_root()) / "cairn" / "devices"


def rack(root: Path | str | None = None) -> list[tuple[str, Path, Path | None]]:
    """``[(device_id, folder, shim_path_or_None)]`` sorted by name, one per folder directly
    under ``<root>/cairn/devices/``; names starting with ``_`` or ``.`` and ``__pycache__``
    are not devices. A missing devices folder is an empty rack."""
    devices = _devices_dir(root)
    if not devices.is_dir():
        return []
    out = []
    for folder in sorted(devices.iterdir()):
        if not folder.is_dir() or folder.name in _SKIP or folder.name.startswith(("_", ".")):
            continue
        shim = folder / "shim.py"
        out.append((folder.name, folder, shim if shim.is_file() else None))
    return out


def rack_ids(root: Path | str | None = None) -> list[str]:
    """The rack's device ids, sorted."""
    return [d for d, _folder, _shim in rack(root)]


def shim_of(name: str, root: Path | str | None = None) -> Path | None:
    """The ``shim.py`` that answers mail to ``name``: ``cairn/devices/<name>/shim.py``, else
    the one ``cairn/devices/<d>/machines/<name>/shim.py``, else None."""
    devices = _devices_dir(root)
    top = devices / name / "shim.py"
    if top.is_file():
        return top
    if not devices.is_dir():
        return None
    folder = folder_of(name, root)
    if folder is not None and (folder / "shim.py").is_file():
        return folder / "shim.py"
    for d, _folder, _shim in rack(root):
        nested = devices / d / "machines" / name / "shim.py"
        if nested.is_file():
            return nested
    return None


def answers_as(folder: Path | str) -> str | None:
    """The name ``folder``'s device answers to on the command line and bus, declared as
    ``answers_as`` in its ``intention+why.json``; None when it declares none (its folder name is
    its name) or its charter cannot be read."""
    try:
        doc = json.loads((Path(folder) / "intention+why.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    name = doc.get("answers_as") if isinstance(doc, dict) else None
    return name if isinstance(name, str) and name else None


def folder_of(name: str, root: Path | str | None = None) -> Path | None:
    """The rack folder whose device answers to ``name`` by declaration, or None. A folder that
    is itself named ``name`` is not looked up here: its name needs no declaring."""
    for _d, folder, _shim in rack(root):
        if answers_as(folder) == name:
            return folder
    return None

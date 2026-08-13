"""DISCOVERY — the pulse roster read from DISK, every pass, so no list can go stale.

RULED BY AKIEN 2026-08-11, standing the wiring down:

  "ON EACH PASS THE GROUND LOOP POLLS A FOLDER FOR EACH DEVICE AND IF THERE IS CODE
   THERE THE GROUND LOOP RUNS IT. THE PROBLEM WITH SUBSCRIBE IS NOW YOU HAVE A LIST
   THAT YOU HAVE TO MAINTAIN AND CAN BECOME STALE."

WHAT THE STALE LIST COST, MEASURED THE SAME DAY. ``loop.py`` filed folder-discovery as an
edge from birth and shipped ``subscribe(shim)`` as the v0. On 2026-08-11 the census read:
17 probe modules armed on disk; ``subscribe`` called from exactly one non-proof site
(``web_server/listener.py``), attaching two shims — neither of which overrides ``probes()``,
so both inherit ``BaseShim``'s empty list. Zero of the 17 were reachable from a beat. The
hand-maintained list did not go stale by drifting; it went stale by never being written at
all, and nothing was loud about it because an empty roster and a healthy roster have
byte-identical resting states. Disk cannot have that failure: a probe file that exists IS on
the roster, and the only way to leave the roster is to stop existing.

THE UNIT IS THE FOLDER, NOT THE REGISTRATION. A device is a directory with a ``probes/``
subdirectory in it; its id is the directory's own name (``cairn/devices/librarian/probes`` → the
``librarian`` device). Nothing declares itself and nothing is granted membership — the
address IS the declaration (Law 5: intent, its voyage and its proofs share an address, and
so does the thing that watches them).

RE-IMPORT ON CHANGE, NOT EVERY PASS. A module is imported once and cached against its
``mtime``; a file edited under a running loop is re-imported on the next pass, so arming a
probe does not require restarting the heartbeat. This is the "if there is code there the
ground loop runs it" clause taken literally — including code that appeared one second ago.

EVERY IMPORT IS GUARDED, AND A BAD MODULE IS DATA. A probe file that raises on import, or
declares no ``PROBE``, or declares something that is not one, does not propagate: it comes
back as a named failure for the caller to turn into a trouble ticket. The heartbeat cannot
be taken down by a device's syntax error (CP2, Law 7 — loud and permanent, never fatal).

THIS MODULE DECIDES NOTHING ABOUT WHAT TO DO WITH A FAILURE. It reports. Benching a broken
device and raising its ticket is the loop's act, at the loop's own address (Law 6).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from cairn.tools.base.probe import Probe

# The directory that holds a device's watchers. One name, here, so "where do probes live"
# is answered once (Law 1) — this is the same convention 17 armed modules already use.
PROBES_DIR = "probes"

# Where devices are looked for. The repo root's own component trees: every directory that
# holds a ``probes/`` folder is a device, at any depth under these — which is what makes
# ``skills/intent/probes`` and ``cairn/devices/librarian/probes`` the same kind of thing without
# either one being special-cased.
def repo_root() -> Path:
    """The class-space root this loop discovers under — derived from this file's own
    address, never configured. A loop is discovered-from where it is installed."""
    return Path(__file__).resolve().parents[3]


def device_folders(root: Path | None = None) -> list[tuple[str, Path]]:
    """Every (device_id, probes_folder) pair on disk, sorted for a stable pulse order.

    The scan is a directory walk for ``probes/`` folders, pruned at the usual noise
    (``__pycache__``, dot-dirs, ``.git``, venvs). A ``probes`` folder with no importable
    module still names a device — an empty watch folder is a device with nothing to fire,
    which is honest, not absent.
    """
    root = Path(root) if root is not None else repo_root()
    found: list[tuple[str, Path]] = []
    for folder in root.rglob(PROBES_DIR):
        if not folder.is_dir():
            continue
        parts = folder.relative_to(root).parts
        if any(p.startswith(".") or p in {"__pycache__", "node_modules", "venv"} for p in parts):
            continue
        device_id = folder.parent.name
        found.append((device_id, folder))
    return sorted(found)


def _module_files(folder: Path) -> list[Path]:
    """The probe modules in a folder: ``*.py`` less ``__init__``/private. Sorted, so two
    passes over an unchanged folder fire in the same order."""
    return sorted(p for p in folder.glob("*.py") if not p.name.startswith("_"))


def load_module(path: Path):
    """Import a probe module OFF ITS PATH, without touching ``sys.modules``' package graph.

    Loaded under a unique synthetic name so two devices may each hold a ``probes/x.py``
    without colliding, and so a re-import after an edit genuinely re-executes the file
    rather than handing back the cached first version.
    """
    name = "cairn._probes." + "_".join(path.with_suffix("").parts[-3:])
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"no import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeCache:
    """The imported probes, held against their files' mtimes.

    Stateful ON PURPOSE and owned by the loop that holds it: re-importing 17 modules once a
    second would be a poll pretending to be a heartbeat. The cache is keyed by path and
    invalidated by mtime, so the cost of a pass over unchanged code is a stat per file.
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, tuple[float, Probe]] = {}

    def probes_for(self, folder: Path) -> tuple[list[Probe], list[dict]]:
        """``(probes, failures)`` for one device folder — never raises.

        A failure is a dict naming the file and the lack, complete enough to resolve from
        the first report: the loop turns each one into a trouble ticket without going back
        to disk for more (I-complete-diagnostic-on-first-pass).
        """
        probes: list[Probe] = []
        failures: list[dict] = []
        for path in _module_files(folder):
            try:
                mtime = path.stat().st_mtime
            except OSError as exc:  # vanished between listing and stat — a real race, reported
                failures.append({"file": str(path), "lack": f"unstattable: {exc}"})
                continue
            cached = self._by_path.get(path)
            if cached is not None and cached[0] == mtime:
                probes.append(cached[1])
                continue
            try:
                module = load_module(path)
            except Exception as exc:  # noqa: BLE001 — a device's bad file cannot reach the beat
                self._by_path.pop(path, None)
                failures.append({"file": str(path),
                                 "lack": f"import raised {type(exc).__name__}: {exc}"})
                continue
            probe = getattr(module, "PROBE", None)
            if probe is None:
                failures.append({"file": str(path),
                                 "lack": "no module-level PROBE — a file in a probes/ folder "
                                         "that declares no watch is either unarmed or misplaced"})
                continue
            if not isinstance(probe, Probe):
                failures.append({"file": str(path),
                                 "lack": f"PROBE is {type(probe).__name__}, not a Probe"})
                continue
            self._by_path[path] = (mtime, probe)
            probes.append(probe)
        return probes, failures


def discover(root: Path | None = None, cache: ProbeCache | None = None,
             skip: set | None = None) -> dict:
    """One pass: every device on disk, its probes, and its import failures.

    Returns ``{device_id: {"folder": str, "probes": [...], "failures": [...]}}``. Devices
    are merged by id when the same name appears at two addresses (a skill and a component
    could share one) — the probes concatenate, because both folders genuinely belong to
    that device's watch.

    ``skip`` is the BENCH: device ids whose folders are not even opened this pass. A device
    benched for a bad import must not be re-imported every second — retrying a known-broken
    thing on a cadence is how a fault becomes a firehose, and the ruling is that a failing
    device waits for its trouble ticket to be cleared. Benched devices are still REPORTED
    (with ``benched: True``) so the roster never silently loses a name.
    """
    cache = cache if cache is not None else ProbeCache()
    skip = skip or set()
    out: dict[str, dict] = {}
    for device_id, folder in device_folders(root):
        if device_id in skip:
            entry = out.setdefault(device_id, {"folder": str(folder), "probes": [],
                                               "failures": [], "benched": True})
            entry["benched"] = True
            continue
        probes, failures = cache.probes_for(folder)
        entry = out.setdefault(device_id, {"folder": str(folder), "probes": [], "failures": []})
        entry["probes"].extend(probes)
        entry["failures"].extend(failures)
    return out

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

import hashlib
import importlib.util
import sys
from pathlib import Path

from cairn.tools.base.address import resolve
from cairn.tools.base.probe import Probe

# The directory that holds a device's watchers. One name, here, so "where do probes live"
# is answered once (Law 1) — this is the same convention 17 armed modules already use.
PROBES_DIR = "probes"

# The directory that holds a device's per-beat SERVICE (ticket
# the-pulse-file-is-the-subscription, Akien 2026-08-15): a ``groundloop/`` folder beside the
# component, at class level or instance level, and the one file in it that matters is
# ``pulse.py``. Presence activates the service; absence deactivates and unloads it. The file
# IS the subscription — same physics as ``probes/``, second registration folder.
GROUNDLOOP_DIR = "groundloop"
PULSE_FILE = "pulse.py"

# Where devices are looked for. The repo root's own component trees: every directory that
# holds a ``probes/`` folder is a device, at any depth under these — which is what makes
# ``skills/intent/probes`` and ``cairn/devices/librarian/probes`` the same kind of thing without
# either one being special-cased.
def repo_root() -> Path:
    """The class-space root this loop discovers under — derived from this file's own
    address, never configured. A loop is discovered-from where it is installed."""
    return Path(__file__).resolve().parents[5]


def device_folders(root: Path | None = None,
                   folder_name: str = PROBES_DIR) -> list[tuple[str, Path]]:
    """Every (device_id, registration_folder) pair on disk, sorted for a stable pulse order.

    The scan is a directory walk for ``folder_name`` folders (``probes/`` by default;
    ``groundloop/`` is the second registration folder, same walk), pruned at the usual
    noise (``__pycache__``, dot-dirs, ``.git``, venvs). A folder with no importable
    module still names a device — an empty watch folder is a device with nothing to fire,
    which is honest, not absent.
    """
    root = Path(root) if root is not None else repo_root()
    found: list[tuple[str, Path]] = []
    for folder in root.rglob(folder_name):
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


def discover(root: Path | None = None, cache: ProbeCache | None = None) -> dict:
    """One pass: every device on disk, its probes, and its import failures.

    Returns ``{device_id: {"folder": str, "probes": [...], "failures": [...]}}``. Devices
    are merged by id when the same name appears at two addresses (a skill and a component
    could share one) — the probes concatenate, because both folders genuinely belong to
    that device's watch. Import failures are reported but the heartbeat does not judge
    them — a failing probe is retried next pass (gated on mtime).
    """
    cache = cache if cache is not None else ProbeCache()
    out: dict[str, dict] = {}
    for device_id, folder in device_folders(root):
        probes, failures = cache.probes_for(folder)
        entry = out.setdefault(device_id, {"folder": str(folder), "probes": [], "failures": []})
        entry["probes"].extend(probes)
        entry["failures"].extend(failures)
    return out


# ---------------------------------------------------------------------------------------
# THE PULSE SURFACE (ticket the-pulse-file-is-the-subscription, Akien 2026-08-15).
# Same physics as the probes above — the file IS the subscription — with the one half the
# probes/ build never needed: UNLOAD. "next pass thru, the file is missing. so i remove it
# from my list. if i imported it, i now unload it." Identity is path+mtime, so an in-place
# edit is a remove+add in one beat. Unload is bounded to pulse-carried code (the ruled
# residue): the module this cache registered is evicted; transitively imported base modules
# are not touched, and the resident interpreter's own staleness is measured elsewhere.
# ---------------------------------------------------------------------------------------

def instance_devices_root() -> Path:
    """Where instance-space device addresses live: ``~/.cairn/devices``. A pulse at
    ``~/.cairn/devices/<device>/<instance>/groundloop/pulse.py`` is served the same beat
    as a class-level one — the unit is the FILE, both fire.

    RESOLVED, NEVER SPELLED (2026-08-17): a function whose entire body was the expression
    ``cairn.tools.base.address`` owns. It is the clearest of the seven conversions, and it
    puts the resolver's DEVICES token on the path of the one process that runs unattended.
    """
    return resolve("instance/devices")


def pulse_sites(class_root: Path | None = None,
                instance_home: Path | None = None) -> list[dict]:
    """Every pulse.py on disk this instant, both levels, sorted by path for a stable order.

    Each site is ``{"device_id", "level": "class"|"instance", "path"}``. Class-level rides
    the same walk as probes/ (``device_folders`` with the second folder name — same prune,
    same device_id-from-parent). Instance-level walks ``~/.cairn/devices``; the device_id
    is the first path segment under it, so a tool's pulse berthed under its holder answers
    to the holder — which is Law 6 said in a path.
    """
    sites: list[dict] = []
    for device_id, folder in device_folders(class_root, GROUNDLOOP_DIR):
        path = folder / PULSE_FILE
        if path.is_file():
            sites.append({"device_id": device_id, "level": "class", "path": path})
    home = Path(instance_home) if instance_home is not None else instance_devices_root()
    if home.is_dir():
        for folder in home.rglob(GROUNDLOOP_DIR):
            if not folder.is_dir():
                continue
            parts = folder.relative_to(home).parts
            if any(p.startswith(".") or p in {"__pycache__", "node_modules", "venv"}
                   for p in parts):
                continue
            path = folder / PULSE_FILE
            if not path.is_file():
                continue
            sites.append({"device_id": parts[0], "level": "instance", "path": path})
    return sorted(sites, key=lambda s: str(s["path"]))


def load_pulse(path: Path) -> tuple[str, object]:
    """Import a pulse module off its path AND register it in ``sys.modules`` — the
    registration is what makes unload real rather than roster bookkeeping.

    The synthetic name hashes the FULL path (not its last segments) because a class-level
    and an instance-level pulse for one device would collide under the probes' naming.
    On a failed exec the half-registered name is popped before the error propagates.
    """
    digest = hashlib.blake2s(str(path).encode()).hexdigest()[:8]
    name = f"cairn._pulse.{path.parent.parent.name}_{digest}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"no import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return name, module


class PulseCache:
    """The learned list: activated pulse modules held against path+mtime — never raises.

    Stateful on purpose and owned by the loop that holds it, like ``ProbeCache`` — with two
    deliberate differences. (1) UNLOAD: deactivation evicts the synthetic name from
    ``sys.modules`` in the same reconcile pass that drops the entry, so a vanished file's
    code genuinely leaves the interpreter and a re-added file re-executes fresh. (2) DAMPED
    RETRY: a pulse whose import raised is remembered against its mtime and not retried
    until the file changes — the probes' retry-every-pass is what the bench exists to stop,
    and a pulse has no bench, so the damping lives here.
    """

    def __init__(self) -> None:
        self._by_path: dict[Path, dict] = {}
        self._refused: dict[Path, tuple[float, str]] = {}

    def reconcile(self, sites: list[dict]) -> list[dict]:
        """Diff found-vs-known: activate the new, evict the gone, re-activate the changed.

        Returns this pass's events, each a complete dict (``activated`` | ``deactivated``
        | ``refused``) — the caller records them; this cache decides nothing about what a
        failure means (same division of labor as ``discover``).
        """
        events: list[dict] = []
        seen: set[Path] = set()
        for site in sites:
            path = site["path"]
            seen.add(path)
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue  # vanished between listing and stat — the next pass sees the absence
            held = self._by_path.get(path)
            if held is not None and held["mtime"] == mtime:
                continue
            if held is not None:  # changed in place: remove+add is ONE act, this pass
                self._evict(path, events, reason="rewritten in place — path+mtime identity")
            refused = self._refused.get(path)
            if refused is not None and refused[0] == mtime:
                continue  # known-bad at this mtime; retried only when the file changes
            try:
                name, module = load_pulse(path)
            except Exception as exc:  # noqa: BLE001 — a device's bad pulse cannot reach the beat
                lack = f"import raised {type(exc).__name__}: {exc}"
                self._refused[path] = (mtime, lack)
                events.append({"event": "refused", "device": site["device_id"],
                               "level": site["level"], "path": str(path),
                               "mtime": mtime, "lack": lack})
                continue
            self._refused.pop(path, None)
            self._by_path[path] = {"mtime": mtime, "name": name, "module": module,
                                   "site": dict(site)}
            events.append({"event": "activated", "device": site["device_id"],
                           "level": site["level"], "path": str(path), "mtime": mtime,
                           "hook": callable(getattr(module, "on_pulse", None))})
        for path in [p for p in self._by_path if p not in seen]:
            self._evict(path, events, reason="file no longer on disk")
        for path in [p for p in self._refused if p not in seen]:
            del self._refused[path]
        return events

    def _evict(self, path: Path, events: list[dict], reason: str) -> None:
        """Deactivate AND unload: drop the entry and pop the synthetic name from
        ``sys.modules`` in the same act — the two halves of Akien's sentence."""
        held = self._by_path.pop(path)
        sys.modules.pop(held["name"], None)
        events.append({"event": "deactivated", "device": held["site"]["device_id"],
                       "level": held["site"]["level"], "path": str(path),
                       "reason": reason})

    def active(self) -> list[dict]:
        """The learned list as data — which device carries a live pulse service, from
        where, at what mtime. In memory only; it rides ``state()`` into the liveness
        record, never a file of its own."""
        return [{"device": h["site"]["device_id"], "level": h["site"]["level"],
                 "path": str(p), "mtime": h["mtime"],
                 "hook": callable(getattr(h["module"], "on_pulse", None))}
                for p, h in sorted(self._by_path.items(), key=lambda kv: str(kv[0]))]

    def refusals(self) -> list[dict]:
        """The damped known-bad files — loud on the state surface, quiet on the beat."""
        return [{"path": str(p), "mtime": m, "lack": lack}
                for p, (m, lack) in sorted(self._refused.items(), key=lambda kv: str(kv[0]))]

    def modules_for(self, device_id: str) -> list:
        """The activated modules a device's shim fires this pass — firing stays in the
        shim (the 584aa74 goof stays dead); this is only the hand-off."""
        return [h["module"] for p, h in sorted(self._by_path.items(),
                                               key=lambda kv: str(kv[0]))
                if h["site"]["device_id"] == device_id]

"""Proof for ticket 4cbf6e28126e — db_domain publishes its socket client as a tool, and every
caller in the repo talks to the database through it.

RULE 1 agreed detail (2) (Akien, 2026-10-01): "there should still be a public interface everyone
uses, so we can change things about the db underneath." The client is a tool nested in the device
(published_by_device), talking straight to the db over its socket — no bus hop, for graph-tree
traffic volume. Measured before the build: 48 into_device rows targeted cairn/devices/db_domain,
every one through cairn.devices.db_domain.store.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING REACHES INTO db_domain. encapsulation_breaches carries no row targeting it.
  2. THE OLD DOOR IS GONE. No file imports cairn.devices.db_domain.store, the file is gone, and
     no charter's invoke names the old import.
  3. THE CLIENT IS PUBLISHED. Its charter declares published_by_device and exactly its one
     module, and that module exposes the surface callers use.

    python3 cairn/devices/db_domain/tools/client/proofs/test_client.py   # exit 0 = green
"""
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The build's names resolve AT CALL TIME, so `cairn test --hollow` taking the client away
    reads as red teeth rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")
_sieve = _Late("cairn.tools.import_sieve.sieve")

PROVES = {"4cbf6e28126e": {"1": "nothing_reaches_into_db_domain",
                           "2": "the_old_door_is_gone",
                           "3": "the_client_is_published"}}

DEVICE = "cairn/devices/db_domain"
CLIENT_DIR = _REPO_ROOT / DEVICE / "tools" / "client"
CLIENT = "cairn.devices.db_domain.tools.client.store"
OLD = "cairn.devices.db_domain.store"
SURFACE = ("connect", "read", "write", "update", "query", "delete", "create_owned_table",
           "owner_of", "scratch")

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def nothing_reaches_into_db_domain():
    rows = [b for b in _inspector.encapsulation_breaches(str(_REPO_ROOT)) if b["target"] == DEVICE]
    assert not rows, f"{len(rows)} reach(es) into db_domain: " + \
        "; ".join(f"{b['file']}:{b['line']} {b['module']}" for b in rows[:8])


def the_old_door_is_gone():
    graph = _sieve.import_graph(str(_REPO_ROOT))
    importers = sorted(f for f, names in graph.items()
                       if any(n == OLD or n.startswith(OLD + ".") for n in names))
    assert not importers, f"{len(importers)} file(s) still import {OLD}: {importers[:8]}"
    assert not (_REPO_ROOT / DEVICE / "store.py").exists(), f"{DEVICE}/store.py still stands"
    naming = [str(c.relative_to(_REPO_ROOT)) for c in _REPO_ROOT.rglob("intention+why.json")
              if ".git" not in c.parts
              and "db_domain import store" in str(json.loads(c.read_text()).get("invoke", ""))
              and CLIENT.rsplit(".", 1)[0] not in str(json.loads(c.read_text()).get("invoke", ""))]
    assert not naming, f"charter invoke still names the old import: {naming}"


def the_client_is_published():
    charter = json.loads((CLIENT_DIR / "intention+why.json").read_text())
    assert charter.get("published_by_device") is True, "the client is not published_by_device"
    assert charter.get("public_interface") == [CLIENT], charter.get("public_interface")
    import importlib
    mod = importlib.import_module(CLIENT)
    missing = [n for n in SURFACE if not callable(getattr(mod, n, None))]
    assert not missing, f"the client does not expose {missing}"


TEETH = [nothing_reaches_into_db_domain, the_old_door_is_gone, the_client_is_published]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

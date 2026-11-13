"""Proof for ticket fc4bb2062253 — the db client finds its passfile when a proof repoints the instance root.

Measured 2026-11-12 on akiendell: a proof that sets address.ROOTS['instance'] to a scratch dir made
store._conn_args() (no unix socket on Windows) name a pgpass that does not exist there, and the connect
failed with 'fe_sendauth: no password supplied'. The client now falls back to the pgpass under the
instance root the process started with.

    bin/cairn test cairn/devices/db_domain/tools/client/proofs/test_the_passfile_survives_a_repointed_instance_root.py
"""
from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"fc4bb2062253": {
    "1": "test_a_repointed_root_still_finds_the_startup_passfile",
    "2": "test_an_untouched_root_names_its_own_passfile",
}}


@contextlib.contextmanager
def _world():
    """A startup root holding a pgpass, a repointed root holding none, and no unix socket."""
    from cairn.devices.db_domain.tools.client import store
    from cairn.tools.base import address
    from cairn.tools.scratch.scratch import scratch_dir
    if True:
        td = Path(scratch_dir("passfile-proof-"))
        startup, repointed, nosock = td / "startup", td / "repointed", td / "nosock"
        for d in (startup / "devices/db_domain/0", repointed, nosock):
            d.mkdir(parents=True)
        (startup / "devices/db_domain/0/pgpass").write_text("127.0.0.1:5432:*:*:x\n", encoding="utf-8")
        saved = (address.ROOTS["instance"], getattr(store, "_STARTUP_INSTANCE", None),
                 os.environ.get("CAIRN_PG_SOCKET_DIR"))
        os.environ["CAIRN_PG_SOCKET_DIR"] = str(nosock)
        store._STARTUP_INSTANCE = startup
        try:
            yield store, address, startup, repointed
        finally:
            address.ROOTS["instance"] = saved[0]
            if saved[1] is None:
                with contextlib.suppress(AttributeError):
                    del store._STARTUP_INSTANCE
            else:
                store._STARTUP_INSTANCE = saved[1]
            if saved[2] is None:
                os.environ.pop("CAIRN_PG_SOCKET_DIR", None)
            else:
                os.environ["CAIRN_PG_SOCKET_DIR"] = saved[2]


def test_a_repointed_root_still_finds_the_startup_passfile():
    with _world() as (store, address, startup, repointed):
        address.ROOTS["instance"] = repointed
        got = Path(store._conn_args()["passfile"])
        assert got.is_file(), f"passfile {got} does not exist under the repointed root"
        assert got == startup / "devices/db_domain/0/pgpass", got
    print("repointed root: passfile names the startup pgpass")


def test_an_untouched_root_names_its_own_passfile():
    with _world() as (store, address, startup, repointed):
        own = repointed / "devices/db_domain/0"
        own.mkdir(parents=True)
        (own / "pgpass").write_text("127.0.0.1:5432:*:*:y\n", encoding="utf-8")
        address.ROOTS["instance"] = repointed
        got = Path(store._conn_args()["passfile"])
        assert got == own / "pgpass", got
    print("a pgpass under the current root still wins")


def main() -> int:
    bad = 0
    for t in (test_a_repointed_root_still_finds_the_startup_passfile, test_an_untouched_root_names_its_own_passfile):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

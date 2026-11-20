"""Proof for ticket c3d48108f9f4 — a shim's last_known berths under its rack folder, and the
alias-named strays migrate home.

Measured 2026-11-20 on akiendelllinux: ~/.cairn/devices/database/0/ and
~/.cairn/devices/inference/0/ stand beside dbproxy/ and inferenceproxy/, each holding only
last_known.json, because BaseShim kept last_known under its device_id and a proxy's device_id is
its charter's answers_as. The launcher resolves the alias to the folder; the shim did not.

1. clause_1_an_aliased_shim_remembers_under_its_folder: a shim whose device_id is dbproxy's
   answers_as ('database') persists last_known at instance_path('dbproxy', 0), and nothing is
   created at instance_path('database', 0);
2. clause_2_a_plain_shim_keeps_its_device_id: a shim whose device_id no charter declares persists
   at instance_path(device_id, 0)/last_known.json, the path unchanged;
3. clause_3_an_alias_record_migrates_home: with a record only at the old alias address, a fresh
   shim's cold read returns it, it then stands under the folder, and the alias file, its 0/ dir
   and the alias dir are gone;
4. clause_4_the_folder_record_wins: with a record at both addresses, the cold read returns the
   folder's and the alias file is gone;
5. clause_5_the_standing_callers_pass: test_shim.py, test_root_verbs.py,
   test_root_verb_vocabulary.py and bin/proofs/test_a_declared_name_outranks_a_stray_instance_dir.py
   pass unchanged.

Every tooth but 5 runs over a scratch instance root (address.ROOTS patched, as test_shim.py
does); the live ~/.cairn is never written. The subject is imported inside each tooth.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_shims_last_known_berths_under_its_folder.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "c3d48108f9f4": {
        "1": "clause_1_an_aliased_shim_remembers_under_its_folder",
        "2": "clause_2_a_plain_shim_keeps_its_device_id",
        "3": "clause_3_an_alias_record_migrates_home",
        "4": "clause_4_the_folder_record_wins",
        "5": "clause_5_the_standing_callers_pass",
    },
}

ALIAS, FOLDER = "database", "dbproxy"   # dbproxy's charter: "answers_as": "database"
PLAIN = "fixture-c3d4-plain"            # a device_id no charter declares
STANDING = [REPO / "cairn" / "tools" / "base" / "proofs" / n
            for n in ("test_shim.py", "test_root_verbs.py", "test_root_verb_vocabulary.py")] + [
            REPO / "bin" / "proofs" / "test_a_declared_name_outranks_a_stray_instance_dir.py"]
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail and not ok:
        print(f"        {detail[-1500:]}")
    if not ok:
        FAILURES.append(name)


class _Scratch:
    """A scratch instance root for the duration of a tooth: address.ROOTS['instance'] -> tmp."""

    def __enter__(self) -> Path:
        from cairn.tools.base import address
        self._addr, self._was = address, address.ROOTS
        self._tmp = tempfile.TemporaryDirectory(prefix="c3d4_last_known_")
        root = Path(self._tmp.name)
        address.ROOTS = {**self._was, "instance": root}
        return root

    def __exit__(self, *exc) -> None:
        self._addr.ROOTS = self._was
        self._tmp.cleanup()


def _shim(device_id: str):
    """A throwaway shim with ``device_id``, built without waking anything."""
    from cairn.tools.base import shim as shim_mod
    cls = type("_C3d4Shim", (shim_mod.BaseShim,), {"device_id": device_id})
    s = cls.__new__(cls)
    s._device = None
    s._presence = shim_mod.OFFLINE
    s._last_known = None
    s._diagnostic_instance = 0
    return s


def _at(root: Path, device: str) -> Path:
    return root / "devices" / device / "0" / "last_known.json"


def _write(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))


def tooth(fn):
    def run() -> None:
        name = fn.__name__
        try:
            ok, detail = fn()
            check(name, ok, detail)
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            check(name, False, f"{type(exc).__name__}: {exc}")
    return run


@tooth
def clause_1_an_aliased_shim_remembers_under_its_folder():
    from cairn.tools.base.address import instance_path
    with _Scratch() as root:
        _shim(ALIAS)._capture_last_known()
        want = instance_path(FOLDER, 0) / "last_known.json"
        stray = instance_path(ALIAS, 0)
        ok = want.is_file() and want == _at(root, FOLDER) and not stray.exists() \
            and not stray.parent.exists()
        return ok, (f"folder record {want} exists={want.is_file()}; alias dir {stray.parent} "
                    f"exists={stray.parent.exists()}; tree={sorted(p.name for p in (root / 'devices').iterdir())}")


@tooth
def clause_2_a_plain_shim_keeps_its_device_id():
    from cairn.tools.base.address import instance_path
    with _Scratch() as root:
        s = _shim(PLAIN)
        s._capture_last_known()
        want = instance_path(PLAIN, 0) / "last_known.json"
        ok = s._last_known_path() == want and want.is_file() and \
            sorted(p.name for p in (root / "devices").iterdir()) == [PLAIN]
        return ok, f"path={s._last_known_path()} want={want} exists={want.is_file()}"


@tooth
def clause_3_an_alias_record_migrates_home():
    with _Scratch() as root:
        rec = {"presence": "offline", "timestamp": "2026-11-18T00:00:00+00:00", "introspect": {"c3d4": 3}}
        _write(_at(root, ALIAS), rec)
        got = _shim(ALIAS)._read_last_known()
        home = _at(root, FOLDER)
        stood = json.loads(home.read_text()) if home.is_file() else None
        gone = not (root / "devices" / ALIAS).exists()
        ok = got == rec and stood == rec and gone
        return ok, f"read={got!r} folder={stood!r} alias dir gone={gone}"


@tooth
def clause_4_the_folder_record_wins():
    with _Scratch() as root:
        old = {"presence": "offline", "timestamp": "2026-11-18T00:00:00+00:00", "introspect": {"who": "alias"}}
        new = {"presence": "offline", "timestamp": "2026-11-20T00:00:00+00:00", "introspect": {"who": "folder"}}
        _write(_at(root, ALIAS), old)
        _write(_at(root, FOLDER), new)
        got = _shim(ALIAS)._read_last_known()
        alias_gone = not _at(root, ALIAS).exists()
        ok = got == new and alias_gone and json.loads(_at(root, FOLDER).read_text()) == new
        return ok, f"read={got!r} alias file gone={alias_gone}"


@tooth
def clause_5_the_standing_callers_pass():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    bad = []
    for p in STANDING:
        script = 'if __name__ == "__main__"' in p.read_text(encoding="utf-8")
        cmd = [sys.executable, str(p)] if script else \
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(p)]
        r = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            bad.append(f"{p.relative_to(REPO)} rc={r.returncode}: {(r.stdout + r.stderr)[-600:]}")
    return not bad, " | ".join(bad)


def main() -> int:
    for t in (clause_1_an_aliased_shim_remembers_under_its_folder, clause_2_a_plain_shim_keeps_its_device_id,
              clause_3_an_alias_record_migrates_home, clause_4_the_folder_record_wins,
              clause_5_the_standing_callers_pass):
        t()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

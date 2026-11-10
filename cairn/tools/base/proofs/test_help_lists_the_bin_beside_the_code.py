"""Proof for ticket ba777080011b — help lists the shortcuts in the bin beside a device's code.

Measured 2026-11-10 before the build: `bin/cairn help` showed [cairn] as `cairn` alone, though
`cairn start`, `cairn stop` and `cairn restart` run from cairn/devices/cairn/bin/ (tickets
30366e99655a, 3264ef726e35); bin_shortcuts read only the instance bin. Outline 5.4.3.3: "Any
device or machine may have a bin/ beside its code. That folder IS its list of shortcuts."

Teeth, one per falsifier clause:

  1. over a scratch class root (fxhb/bin/wave, Python, docstring about) and a scratch instance
     root (fxhb/0/bin/frob, comment about), bin_shortcuts lists [frob, wave] with those abouts;
  2. a name both bins hold is listed once, with the instance bin's about;
  3. a non-executable file in the class bin is absent; a device with neither bin returns [];
  4. with class_root omitted and CAIRN_CLASS_ROOT unset, the cairn device lists restart, start and
     stop from the repo's cairn/devices/cairn/bin/, abouts beginning `cairn <verb> —`;
  5. cold_list under CAIRN_CLASS_ROOT carries frob and wave in its data and its text;
  6. the standing help proofs pass unchanged.

Every world is a scratch folder from the scratch door; nothing reads or writes ~/.cairn. The
subject is bound at call time inside each tooth, so a hollow build reds the teeth by name.

    python3 cairn/tools/base/proofs/test_help_lists_the_bin_beside_the_code.py   # exit 0 = green
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "ba777080011b": {
        "1": "both_bins_are_listed_in_order",
        "2": "the_instance_bin_wins_a_shared_name",
        "3": "non_executables_and_empty_devices_list_nothing",
        "4": "the_default_class_root_is_the_repos_devices",
        "5": "cold_list_carries_the_class_bin",
        "6": "the_standing_help_proofs_pass",
    },
}

DEV = "fxhb"
STANDING = ["cairn/tools/base/proofs/test_help_answers_as_list_with_shortcuts.py",
            "cairn/tools/base/proofs/test_root_verbs.py"]
FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _exe(p: Path, text: str, mode: int = 0o755) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    os.chmod(p, mode)


def _world() -> tuple[Path, Path]:
    """(instance root, class root): fxhb/0/bin/frob and fxhb/0/bin/both in the instance bin;
    fxhb/bin/wave, fxhb/bin/both and a non-executable fxhb/bin/notes.txt in the class bin."""
    from cairn.tools.scratch.scratch import scratch_dir
    top = scratch_dir("ba77-")
    inst, cls = top / "instances", top / "classes"
    _exe(inst / DEV / "0" / "bin" / "frob", "#!/usr/bin/env bash\n# frob — turns the crank\necho frob\n")
    _exe(inst / DEV / "0" / "bin" / "both", "#!/usr/bin/env bash\n# both — the instance's copy\n")
    _exe(cls / DEV / "bin" / "wave", '#!/usr/bin/env python3\n"""wave — waves the fixture."""\nprint("wave")\n')
    _exe(cls / DEV / "bin" / "both", "#!/usr/bin/env bash\n# both — the class's copy\n")
    _exe(cls / DEV / "bin" / "notes.txt", "# not a shortcut\n", 0o644)
    (inst / "empty" / "0").mkdir(parents=True)
    return inst, cls


def _rows(dev: str, inst: Path, cls: Path) -> list[dict]:
    from cairn.tools.base import shim
    return shim.bin_shortcuts(dev, str(inst), 0, class_root=str(cls))


def main() -> int:
    inst, cls = _world()

    try:
        rows = _rows(DEV, inst, cls)
        names = [r["name"] for r in rows]
        about = {r["name"]: r["about"] for r in rows}
        ok1 = (names == ["both", "frob", "wave"] and about.get("frob") == "frob — turns the crank"
               and about.get("wave") == "wave — waves the fixture.")
        _check("both_bins_are_listed_in_order", ok1, f"rows={rows}")
        _check("the_instance_bin_wins_a_shared_name",
               names.count("both") == 1 and about.get("both") == "both — the instance's copy", f"rows={rows}")
        empty = _rows("empty", inst, cls)
        _check("non_executables_and_empty_devices_list_nothing",
               "notes.txt" not in names and empty == [], f"names={names} empty={empty}")
    except Exception as exc:  # a hollow build has no class_root: every tooth that needs it reds by name
        for name in ("both_bins_are_listed_in_order", "the_instance_bin_wins_a_shared_name",
                     "non_executables_and_empty_devices_list_nothing"):
            _check(name, False, f"{type(exc).__name__}: {exc}")

    code = ("import json, sys; from cairn.tools.base.shim import bin_shortcuts; "
            "print(json.dumps(bin_shortcuts('cairn', sys.argv[1], 0)))")
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_CLASS_ROOT"}
    env["PYTHONPATH"] = str(REPO)
    r = subprocess.run([sys.executable, "-c", code, str(inst)], capture_output=True, text=True, env=env, timeout=60)
    try:
        got = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = None
    ok4 = (isinstance(got, list) and [g["name"] for g in got] == ["restart", "start", "stop"]
           and all(g["about"].startswith(f"cairn {g['name']} —") for g in got))
    _check("the_default_class_root_is_the_repos_devices", ok4, f"rc={r.returncode} out={r.stdout[-600:]!r} err={r.stderr[-600:]!r}")

    code5 = ("import json, sys; from cairn.tools.base.shim import cold_list; "
             "print(json.dumps(cold_list(sys.argv[1], sys.argv[2])))")
    env5 = dict(env, CAIRN_CLASS_ROOT=str(cls))
    r5 = subprocess.run([sys.executable, "-c", code5, DEV, str(inst)], capture_output=True, text=True, env=env5, timeout=60)
    try:
        cl = json.loads(r5.stdout.strip().splitlines()[-1])
        sc = [s["name"] for s in cl["data"]["shortcuts"]]
        ok5 = {"frob", "wave"} <= set(sc) and "frob" in cl["text"] and "wave — waves the fixture." in cl["text"]
    except (ValueError, IndexError, KeyError, TypeError) as exc:
        sc, ok5 = f"{type(exc).__name__}: {exc}", False
    _check("cold_list_carries_the_class_bin", ok5, f"rc={r5.returncode} shortcuts={sc} err={r5.stderr[-600:]!r}")

    bad = []
    for p in STANDING:
        rp = subprocess.run([sys.executable, str(REPO / p)], capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, PYTHONPATH=str(REPO)))
        if rp.returncode != 0:
            bad.append(f"{p}: rc={rp.returncode} {rp.stdout[-400:]!r}")
    _check("the_standing_help_proofs_pass", not bad, "; ".join(bad))

    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

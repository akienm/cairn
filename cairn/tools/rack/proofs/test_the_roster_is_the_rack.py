"""THE DEVICE ROSTER IS THE RACK — ticket a808e21d646f (2026-09-30, amended 2026-10-02).

A device is a folder directly under ``cairn/devices/``, fronted by its shim; a ``probes/``
folder no longer makes anything a device. Measured 2026-09-30: the probes/ rule yielded 42
"devices", tools such as base, question and artifact among them, against 13 rack folders.
This proof holds six of the eight clauses of the ticket's falsifier; clauses 5 and 6 are
proved at their own components' addresses (RULE 1: a proof measures only its component), and
the ticket's crossing names all three proofs:

  (1) ``rack()`` returns no name that is not a folder directly under ``cairn/devices/``;
  (2) it omits no such folder (a scratch root: three device folders, one without shim.py, a
      nested machine with its own probes/, a ``cairn/tools/x/probes/`` folder, and the
      ``__pycache__`` / ``_private`` / ``.hidden`` noise);
  (3) the shimless folder is listed with shim None, never dropped;
  (4) ``device_folders`` has no call outside discovery.py and the ground loop's proofs;
  (5) [proved in cairn/devices/cairn/machines/sleep_cycle/proofs/test_token_rotation.py]
      ``token.roster(bus, root)`` is the rack devices whose LATEST announced menu carries
      ``sleep`` — a scratch bus with three menus: one carrying sleep, one whose newer menu
      dropped it, one device silent, plus a newer verb-less record on the sleeper's channel;
  (6) [proved in cairn/devices/cairn/machines/ground_loop/proofs/test_heartbeat.py]
      the ground loop's beat record carries ``devices`` equal to ``rack()`` of its root;
  (7) the encapsulation sieve shows no breach from ``cairn/tools/rack``, and none from the
      code (not the proofs) of bus_client, tools/base or bin/probes onto
      ``ground_loop.discovery`` (the roster walk);
  (8) mail to a nested machine still resolves its own shim: ``rack.shim_of('harbor_master')``
      is ``cairn/devices/cairn/machines/harbor_master/shim.py`` (83 probes post to it,
      measured 2026-10-03) — the roster narrowing must not cut a delivery address.

Every face is called inside a tooth, never at import, so a build taken away reds teeth
instead of crashing the runner. The grep's needle is assembled from pieces, so this file is
not its own hit.

Run:  python3 cairn/tools/rack/proofs/test_the_roster_is_the_rack.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"a808e21d646f": {
    "1": "rack names only folders directly under cairn/devices",
    "2": "rack omits no device folder",
    "3": "a shimless device folder is listed with shim None",
    "4": "nothing outside discovery asks device_folders",
    "7": "no roster import crosses into a device",
    "8": "mail to a nested machine still finds its own shim",
}}
NEEDLE = "device_" + "folders("
FAILURES: list[str] = []


def ok(name: str, passed: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if passed else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not passed:
        FAILURES.append(f"{name}: {detail}")


def _scratch_rack(root: Path) -> None:
    devs = root / "cairn" / "devices"
    for name, shim in (("alpha", True), ("beta", True), ("gamma", False)):
        (devs / name).mkdir(parents=True)
        if shim:
            (devs / name / "shim.py").write_text("# scratch shim\n")
    (devs / "alpha" / "machines" / "inner" / "probes").mkdir(parents=True)
    (devs / "alpha" / "machines" / "inner" / "shim.py").write_text("# nested machine shim\n")
    for noise in ("__pycache__", "_private", ".hidden"):
        (devs / noise).mkdir()
    (devs / "__init__.py").write_text("")
    (root / "cairn" / "tools" / "x" / "probes").mkdir(parents=True)


def _rack(root: Path):
    from cairn.tools.rack.rack import rack

    return rack(root)


def tooth_1_2_3(T) -> None:
    with tempfile.TemporaryDirectory(prefix="a808-the-roster-is-the-rack-") as td:
        root = Path(td)
        _scratch_rack(root)
        try:
            got = _rack(root)
        except Exception as exc:  # noqa: BLE001
            for k in ("1", "2", "3"):
                ok(T[k], False, f"rack() raised {type(exc).__name__}: {exc}")
            return
        devs = root / "cairn" / "devices"
        names = [g[0] for g in got]
        stray = [n for n in names if not (devs / n).is_dir() or n not in ("alpha", "beta", "gamma")]
        ok(T["1"], not stray, f"names={names} stray={stray}")
        ok(T["2"], names == ["alpha", "beta", "gamma"], f"names={names}")
        by = {g[0]: g for g in got}
        g = by.get("gamma")
        a = by.get("alpha")
        ok(T["3"], g is not None and g[2] is None and a is not None
           and Path(a[2]) == devs / "alpha" / "shim.py" and Path(g[1]) == devs / "gamma",
           f"gamma={g} alpha={a}")


def tooth_4(T) -> None:
    out = subprocess.run(["git", "-C", str(_REPO), "grep", "-n", "-F", NEEDLE, "--",
                          "cairn", "bin", "skills", ":!*.json"],
                         capture_output=True, text=True)
    allowed = ("cairn/devices/cairn/machines/ground_loop/discovery.py:",
               "cairn/devices/cairn/machines/ground_loop/proofs/")
    hits = [ln for ln in out.stdout.splitlines() if not ln.startswith(allowed)]
    ok(T["4"], out.returncode in (0, 1) and not hits, f"rc={out.returncode} hits={hits}")


def tooth_7(T) -> None:
    try:
        from cairn.machines.build_inspector.inspector import encapsulation_breaches
        rows = encapsulation_breaches(str(_REPO))
    except Exception as exc:  # noqa: BLE001
        ok(T["7"], False, f"sieve raised {type(exc).__name__}: {exc}")
        return
    walk = "cairn.devices.cairn.machines.ground_loop.discovery"
    # The roster's code, not other tickets' proofs: a proof under tools/base that imports
    # discover() to test probe arming is a RULE 1 row of its own, not a roster walk.
    bad = [f"{r['file']}:{r['line']} {r['module']} {r['reason']}" for r in rows
           if r["source"] == "cairn/tools/rack"
           or (r["module"] == walk and "/proofs/" not in r["file"]
               and (r["source"] in ("cairn/tools/bus_client", "cairn/tools/base")
                    or r["file"].startswith("bin/probes/")))]
    has_charter = (_REPO / "cairn" / "tools" / "rack" / "intention+why.json").is_file()
    ok(T["7"], has_charter and not bad, f"charter={has_charter} breaches={bad}")


def tooth_8(T) -> None:
    try:
        from cairn.tools.rack.rack import shim_of
        got = shim_of("harbor_master")
        top = shim_of("trouble")
        none = shim_of("no_such_device_a808")
    except Exception as exc:  # noqa: BLE001
        ok(T["8"], False, f"shim_of raised {type(exc).__name__}: {exc}")
        return
    devs = _REPO / "cairn" / "devices"
    ok(T["8"], got == devs / "cairn" / "machines" / "harbor_master" / "shim.py"
       and top == devs / "trouble" / "shim.py" and none is None,
       f"harbor_master={got} trouble={top} unknown={none}")


def main() -> int:
    print("the device roster is the rack")
    T = PROVES["a808e21d646f"]
    tooth_1_2_3(T)
    tooth_4(T)
    tooth_7(T)
    tooth_8(T)
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — the roster is the rack, the sleep roster is announced, nothing walks probes/ for it.")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())

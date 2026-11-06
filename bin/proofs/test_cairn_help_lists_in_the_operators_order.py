"""Proof for ticket 2e6c93cf74c7 — `cairn help` lists [all], [operator], [cairn], then every other
device alphabetically; `cairn <device> help` lists that one device; help is answered before the
floor is laid.

Akien 2026-11-05 (Q#27, outline 8.4): "cairn help lists [all] then [operator] then [cairn] then
the rest in alpha order"; and (open-ae78c6e4700d) [all] is the verbs "defined in the basemost
shim. they're part of everything". Teeth, one per falsifier clause:

  1. over a scratch CAIRN_INSTANCE_ROOT holding zeta, operator, alpha and cairn, `cairn help`
     prints section headers in the order [all], [operator], [cairn], [alpha], [zeta];
  2. each device section lists every executable in that device's bin with its first comment
     line, and a non-executable file is absent;
  3. `cairn alpha help` prints only alpha's section (no bus answers in the scratch HOME, so it is
     the cold answer, saying views need the bus);
  4. help exits 0 with a scratch root whose postgres socket is absent and whose venv is absent,
     and neither is laid (no floor ran);
  5. [all] lists help and every key of cairn.tools.base.shim.ROOT_VERB_SEMANTICS with its
     meaning, and a key added to that table in a fixture (a sitecustomize on PYTHONPATH) appears
     under [all] with no change to bin/cairn.

Every run is bin/cairn as a subprocess under a scratch HOME from the scratch door; the live
instance, bus, venv and db are never touched.

    python3 bin/proofs/test_cairn_help_lists_in_the_operators_order.py   # exit 0 = green
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CAIRN = REPO / "bin" / "cairn"

PROVES = {
    "2e6c93cf74c7": {
        "1": "clause_1_sections_in_the_operators_order",
        "2": "clause_2_each_section_lists_its_bin",
        "3": "clause_3_device_help_is_that_device_alone",
        "4": "clause_4_help_lays_no_floor",
        "5": "clause_5_all_is_the_root_verb_table",
    },
}

FAILURES: list[str] = []

BINS = {
    "zeta": {"zap": "# zap — zeta's only verb"},
    "operator": {"inbox": "# inbox: what waits for the operator", "review": "# review an artifact"},
    "alpha": {"frob": "# frob turns alpha's crank", "notes.txt": None},
    "cairn": {"cairn": "# the cairn device's own launcher"},
}


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _world() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("2e6c-home-")
    for dev, files in BINS.items():
        b = home / "devices" / dev / "0" / "bin"
        b.mkdir(parents=True)
        for name, comment in files.items():
            p = b / name
            if comment is None:
                p.write_text("# not executable, never a shortcut\n")
                p.chmod(0o644)
            else:
                p.write_text(f"#!/bin/sh\n{comment}\nexit 0\n")
                p.chmod(0o755)
    (home / "nosock").mkdir()
    fx = home / "fixture_site"
    fx.mkdir()
    (fx / "sitecustomize.py").write_text(
        "from cairn.tools.base import shim\n"
        "shim.ROOT_VERB_SEMANTICS['pid'] = 'lists the pids a device owns (fixture key, 2e6c)'\n")
    return home


def _env(home: Path, fixture: bool = False) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(HOME=str(home), CAIRN_INSTANCE_ROOT=str(home / "devices"),
               CAIRN_VENV=str(home / "venv"), CAIRN_PG_SOCKET_DIR=str(home / "nosock"))
    if fixture:
        env["PYTHONPATH"] = str(home / "fixture_site")
    return env


def _run(home: Path, *args: str, fixture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([str(CAIRN), *args], env=_env(home, fixture), capture_output=True,
                          text=True, timeout=180, cwd="/")


def _sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
            out[cur] = []
        elif cur is not None and s:
            out[cur].append(s)
    return out


def _headers(text: str) -> list[str]:
    return [ln.strip()[1:-1] for ln in text.splitlines() if ln.strip().startswith("[") and ln.strip().endswith("]")]


def clause_1_sections_in_the_operators_order(home: Path) -> None:
    r = _run(home, "help")
    got = _headers(r.stdout)
    want = ["all", "operator", "cairn", "alpha", "zeta"]
    _check("clause_1_sections_in_the_operators_order", r.returncode == 0 and got == want,
           f"rc={r.returncode} headers={got} want={want} stderr={r.stderr[-600:]}")


def clause_2_each_section_lists_its_bin(home: Path) -> None:
    r = _run(home, "help")
    sec = _sections(r.stdout)
    lacks = []
    for dev, files in BINS.items():
        lines = sec.get(dev)
        if lines is None:
            lacks.append(f"no [{dev}] section")
            continue
        for name, comment in files.items():
            hit = [ln for ln in lines if ln.split()[0] == name] if lines else []
            if comment is None:
                if hit:
                    lacks.append(f"[{dev}] lists the non-executable {name}")
            elif not hit:
                lacks.append(f"[{dev}] does not list {name}")
            elif comment.lstrip("#").strip() not in hit[0]:
                lacks.append(f"[{dev}] {name} line {hit[0]!r} lacks its first comment line")
    _check("clause_2_each_section_lists_its_bin", r.returncode == 0 and not lacks,
           f"rc={r.returncode} " + "; ".join(lacks) + f" stdout={r.stdout[-900:]}")


def clause_3_device_help_is_that_device_alone(home: Path) -> None:
    r = _run(home, "alpha", "help")
    heads = _headers(r.stdout)
    lacks = []
    if r.returncode != 0:
        lacks.append(f"rc={r.returncode} stderr={r.stderr[-500:]}")
    if heads != ["alpha"]:
        lacks.append(f"headers {heads}, want ['alpha']")
    body = r.stdout
    if "frob" not in body or "turns alpha's crank" not in body:
        lacks.append("alpha's frob and its comment are absent")
    for other in ("zap", "inbox", "review"):
        if other in body.split():
            lacks.append(f"another device's {other} appears")
    if "bus" not in body.lower():
        lacks.append("the cold answer does not say views need the bus")
    r2 = _run(home, "nosuchdevice", "help")
    if r2.returncode == 0:
        lacks.append(f"`cairn nosuchdevice help` exits 0: {r2.stdout[-300:]}")
    _check("clause_3_device_help_is_that_device_alone", not lacks, "; ".join(lacks) + f" stdout={body[-700:]}")


def clause_4_help_lays_no_floor(home: Path) -> None:
    lacks = []
    for args in (("help",), ("alpha", "help")):
        r = _run(home, *args)
        if r.returncode != 0:
            lacks.append(f"cairn {' '.join(args)} rc={r.returncode} stderr={r.stderr[-500:]}")
        if "floor" in r.stderr:
            lacks.append(f"cairn {' '.join(args)} reached the floor: {r.stderr[-400:]}")
    if (home / "venv").exists():
        lacks.append("a venv was laid under the scratch CAIRN_VENV")
    if any((home / "nosock").iterdir()):
        lacks.append("something appeared in the scratch postgres socket dir")
    _check("clause_4_help_lays_no_floor", not lacks, "; ".join(lacks))


def clause_5_all_is_the_root_verb_table(home: Path) -> None:
    from cairn.tools.base import shim
    lacks = []
    r = _run(home, "help")
    al = _sections(r.stdout).get("all") or []
    if "help" not in shim.ROOT_VERB_SEMANTICS:
        lacks.append("ROOT_VERB_SEMANTICS carries no help (child 2d6c1c36f3bd)")
    for verb, meaning in shim.ROOT_VERB_SEMANTICS.items():
        if not any(ln.split()[0] == verb and meaning in ln for ln in al):
            lacks.append(f"[all] lacks {verb} with its meaning")
    r = _run(home, "help", fixture=True)
    al = _sections(r.stdout).get("all") or []
    if not any(ln.split()[0] == "pid" and "fixture key, 2e6c" in ln for ln in al):
        lacks.append(f"a fixture key added to the table does not appear under [all]: rc={r.returncode} "
                     f"{r.stdout[-500:]} {r.stderr[-300:]}")
    _check("clause_5_all_is_the_root_verb_table", not lacks, "; ".join(lacks))


def main() -> int:
    print("2e6c93cf74c7 — cairn help lists [all], [operator], [cairn], then every device alphabetically")
    home = _world()
    try:
        for tooth in (clause_1_sections_in_the_operators_order, clause_2_each_section_lists_its_bin,
                      clause_3_device_help_is_that_device_alone, clause_4_help_lays_no_floor,
                      clause_5_all_is_the_root_verb_table):
            try:
                tooth(home)
            except Exception as exc:  # noqa: BLE001 — each tooth reports even when one raises
                _check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(home, ignore_errors=True)
    print(f"{'GREEN' if not FAILURES else 'RED'}: {len(FAILURES)} failing: {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for ticket c7dc2ccdd9ad — the commons root has one resolver (cairn.tools.base.address),
and the installer survives an absent commons.

Red-first: written before the build. On Windows the commons is the sibling clone
(C:/automation/local/CairnCommons), never ~/dev/src/CairnCommons.

Every tooth binds what the build ADDED at call time, never at import.

    python <this file>
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "c7dc2ccdd9ad": {
        "1": "no_production_source_spells_the_home_commons",
        "2": "the_sites_default_to_the_one_resolver_and_keep_their_overrides",
        "3": "install_over_an_absent_commons_is_a_named_failed_result",
    },
}

HOME_FORM = re.compile(r"dev/src/CairnCommons|\"dev\"\s*/\s*\"src\"\s*/\s*\"CairnCommons\"")
_FLAGS = 0x08000000 if os.name == "nt" else 0


def no_production_source_spells_the_home_commons():
    bad = []
    for p in (REPO / "cairn").rglob("*.py"):
        parts = set(p.relative_to(REPO).parts)
        if parts & {"proofs", "probes", "__pycache__", "validations"} or p.name.startswith("test_"):
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if HOME_FORM.search(line) and ('"' in line or "'" in line):  # a path literal, not prose
                bad.append(f"{p.relative_to(REPO).as_posix()}:{n}: {line.strip()}")
    assert not bad, "home-relative commons default:\n" + "\n".join(bad)


_PROBE = r"""
import json
from cairn.tools.base.address import ROOTS
from cairn.machines.installer import installer
from cairn.tools.ticket_inspector import inspector
from cairn.tools.operator_inbox import inbox
from cairn.machines.skill_block import skill_block
from cairn.devices.tester import hollow
c = ROOTS["commons"]
print(json.dumps({
  "commons": str(c),
  "installer": str(installer.DEFAULT_INTENTIONS_DIR.parent),
  "inspector": str(inspector.COMMONS_ROOT),
  "inspector_tickets": str(inspector.TICKETS_DIR.parent),
  "inbox": str(inbox.COMMONS_ROOT),
  "skill_block": str(skill_block._commons_root()),
  "hollow": str(hollow.COMMONS),
}))
"""


def _probe(env_extra: dict) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("CAIRN_COMMONS_ROOT", "CAIRN_ARTIFACT_ROOTS", "CAIRN_TICKETS_DIR")}
    env.update(env_extra)
    env["PYTHONPATH"] = str(REPO)
    r = subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True,
                       env=env, cwd=str(REPO), creationflags=_FLAGS)
    assert r.returncode == 0, f"probe import failed: {r.stderr[-600:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def the_sites_default_to_the_one_resolver_and_keep_their_overrides():
    d = _probe({})
    want = d["commons"]
    wrong = {k: v for k, v in d.items() if k != "commons" and Path(v) != Path(want)}
    assert not wrong, f"sites that do not default to address.ROOTS['commons'] ({want}): {wrong}"
    # the env override seams survive: CAIRN_COMMONS_ROOT still moves the sites that honoured it
    with tempfile.TemporaryDirectory() as t:
        o = _probe({"CAIRN_COMMONS_ROOT": t})
        for k in ("inbox", "skill_block"):
            assert Path(o[k]) == Path(t), f"{k} stopped honouring CAIRN_COMMONS_ROOT: {o[k]}"


def install_over_an_absent_commons_is_a_named_failed_result():
    from cairn.machines.installer import installer
    with tempfile.TemporaryDirectory() as t:
        absent = Path(t) / "no-such-commons" / "intentions-not-beside-code"
        try:
            res = installer.install(intentions_dir=absent, dry_run=True)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"install raised {type(e).__name__}: {e}") from e
        failed = [r for r in res if r.get("status") == "failed"]
        assert failed, f"no failed result for an absent directory: {res}"
        assert any(str(absent) in r.get("detail", "") for r in failed), f"no result names {absent}: {failed}"


TEETH = [no_production_source_spells_the_home_commons,
         the_sites_default_to_the_one_resolver_and_keep_their_overrides,
         install_over_an_absent_commons_is_a_named_failed_result]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:900]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

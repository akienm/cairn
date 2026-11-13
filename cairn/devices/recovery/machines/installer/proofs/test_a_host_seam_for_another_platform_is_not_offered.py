"""Proof: a host seam that cannot apply on this box's platform is not offered (ticket 45a6331971fd).

Measured 2026-11-12 on akiendell: the installer's only host seam, usage-widget-hook (a KDE plasmoid), read
OFFERED because its verify needs jq and ~/.claude/usage-cache.json, and the install gate refuses while any
red stands, so a Windows box could never read installed. A host seam may now declare `platforms`; a seam
declaring other platforms than this box's is reported without running its verify, and reads green.

Teeth 1-2 run install() over a scratch intentions directory, so nothing live is read or written. Tooth 3
reads the real corpus's usage-widget-hook, which must declare linux only. The new behaviour is reached
inside each tooth, so a hollow build reds per tooth.

    python3 cairn/devices/recovery/machines/installer/proofs/test_a_host_seam_for_another_platform_is_not_offered.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
assert (REPO / "bin" / "cairn").exists(), f"REPO {REPO} does not hold bin/cairn"
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"45a6331971fd": {
    "1": "test_a_seam_for_another_platform_is_skipped_by_name_and_never_verified",
    "2": "test_a_seam_without_a_declaration_or_for_this_platform_is_judged_as_before",
    "3": "test_the_usage_widget_seam_declares_linux_and_this_box_does_not_offer_it",
    "4": "test_the_gate_passes_a_not_applicable_seam_and_still_refuses_a_red_one",
}}

NEVER = "not-a-platform-anyone-runs"


def _seam(name: str, verify: str, **extra) -> dict:
    return {"id": name, "node_class": "host-seam", "intention": f"seam {name}",
            "apply": {"1": "nothing"}, "verify": {"command": verify}, **extra}


def _corpus(*seams: dict) -> Path:
    d = scratch_dir("host-seam-platform-")
    for s in seams:
        (d / f"{s['id']}.json").write_text(json.dumps(s), encoding="utf-8")
    return d


def test_a_seam_for_another_platform_is_skipped_by_name_and_never_verified() -> None:
    from cairn.devices.recovery.machines.install_inspector.inspector import red_of
    from cairn.devices.recovery.machines.installer.installer import install
    marker = scratch_dir("host-seam-marker-") / "verify-ran"
    other = _seam("other-platform", f"touch '{marker.as_posix()}'; exit 1", platforms=[NEVER])
    results = install(intentions_dir=_corpus(other), dry_run=True)
    (r,) = results
    assert r["id"] == "other-platform", r
    assert r["status"] == "not_applicable", r
    assert r["status"] != "already_applied", f"a seam never applied here must not read applied: {r}"
    assert r.get("skipped") == "platform", r
    assert NEVER in r["detail"] and sys.platform in r["detail"], r
    assert not marker.exists(), "the verify of a seam for another platform ran"
    assert red_of(results) == [], f"a skipped seam must not stand as a red: {results}"


def test_the_gate_passes_a_not_applicable_seam_and_still_refuses_a_red_one() -> None:
    import functools

    from cairn.devices.recovery.machines.install_inspector.inspector import installed
    from cairn.devices.recovery.machines.installer.installer import install
    only_other = _corpus(_seam("other-platform", "exit 1", platforms=[NEVER]))
    ok, reds = installed([functools.partial(install, intentions_dir=only_other)])
    assert ok and reds == [], (ok, reds)
    with_red = _corpus(_seam("other-platform", "exit 1", platforms=[NEVER]), _seam("here-red", "exit 1"))
    ok, reds = installed([functools.partial(install, intentions_dir=with_red)])
    assert not ok and [r["id"] for r in reds] == ["here-red"], (ok, reds)


def test_a_seam_without_a_declaration_or_for_this_platform_is_judged_as_before() -> None:
    from cairn.devices.recovery.machines.installer.installer import install
    seams = [_seam("undeclared-red", "exit 1"),
             _seam("here-red", "exit 1", platforms=[sys.platform]),
             _seam("undeclared-green", "echo ok")]
    by_id = {r["id"]: r for r in install(intentions_dir=_corpus(*seams), dry_run=True)}
    assert by_id["undeclared-red"]["status"] == "offered", by_id
    assert by_id["here-red"]["status"] == "offered", by_id
    assert by_id["undeclared-green"]["status"] == "already_applied", by_id
    assert not any(r.get("skipped") for r in by_id.values()), by_id


def test_the_usage_widget_seam_declares_linux_and_this_box_does_not_offer_it() -> None:
    from cairn.devices.recovery.machines.installer.installer import DEFAULT_INTENTIONS_DIR, gather_host_seams, install
    seam = next((s for s in gather_host_seams(DEFAULT_INTENTIONS_DIR) if s.get("id") == "usage-widget-hook"), None)
    assert seam is not None, "usage-widget-hook is not in the corpus"
    assert seam.get("platforms") == ["linux"], seam.get("platforms")
    if sys.platform != "linux":
        r = next(x for x in install(dry_run=True) if x["id"] == "usage-widget-hook")
        assert r["status"] == "not_applicable" and r.get("skipped") == "platform", r


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 -- every tooth reports, none aborts the run
            failed.append(name)
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

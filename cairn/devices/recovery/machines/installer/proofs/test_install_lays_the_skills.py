"""Proof: cairn install links every Cairn skill into the Claude skills root (ticket 53e7979f76e7).

Measured 2026-11-12: akienasus had none of the 15 Cairn skills and akiendell none of the 16,
both linked by hand. A box without them cannot fire /idea, /intent, /sorted or /sail.

Every tooth runs over a fixture skills tree and a scratch skills root, so the live
~/.claude/skills is never read or written. The link-maker is injected (a counting wrapper
around os.symlink), so a tooth can tell "changed nothing" from "relinked the same thing".
The installer's step is imported inside each tooth, so a hollow build reds per tooth.

    python3 cairn/devices/recovery/machines/installer/proofs/test_install_lays_the_skills.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
assert (REPO / "bin" / "cairn").exists(), f"REPO {REPO} does not hold bin/cairn"
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"53e7979f76e7": {
    "1": "test_an_empty_root_gets_one_link_per_skill_and_none_for_the_rest",
    "2": "test_a_second_run_reads_already_applied_and_changes_nothing",
    "3": "test_a_real_dir_is_red_a_stray_link_is_repointed_a_dangling_one_removed",
    "4": "test_dry_run_offers_and_writes_nothing",
}}

SKILLS = ("idea", "intent", "sorted")


def _fixture(tag: str) -> tuple[Path, Path, list]:
    """A checkout's skills/ (three skills, a __pycache__, a dir without SKILL.md, a loose
    file) and an empty scratch skills root. Returns (src, root, calls)."""
    base = scratch_dir(f"skill-links-{tag}-")
    src = base / "checkout" / "skills"
    for s in SKILLS:
        (src / s).mkdir(parents=True)
        (src / s / "SKILL.md").write_text(f"# /{s}\n")
    (src / "__pycache__").mkdir()
    (src / "half").mkdir()
    (src / "half" / "notes.md").write_text("no SKILL.md here\n")
    (src / "__init__.py").write_text("")
    root = base / "claude" / "skills"
    calls: list = []
    return src, root, calls


def _counting(calls: list):
    def link(target: Path, at: Path) -> None:
        calls.append((target, at))
        os.symlink(target, at, target_is_directory=True)
    return link


def test_an_empty_root_gets_one_link_per_skill_and_none_for_the_rest() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_skill_links
    src, root, calls = _fixture("empty")
    r = ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls))
    assert r["id"] == "skill-links" and r["status"] == "applied", r
    assert sorted(p.name for p in root.iterdir()) == sorted(SKILLS), sorted(root.iterdir())
    for s in SKILLS:
        assert os.path.islink(root / s), f"{s} is not a link"
        assert (root / s).resolve() == (src / s).resolve(), f"{s} -> {(root / s).resolve()}"
    assert not (root / "__pycache__").exists() and not (root / "half").exists()
    assert len(calls) == len(SKILLS), calls


def test_a_second_run_reads_already_applied_and_changes_nothing() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_skill_links
    src, root, calls = _fixture("again")
    ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls))
    before = {p.name: (os.readlink(p), p.lstat().st_ino) for p in root.iterdir()}
    calls.clear()
    again = ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls))
    assert again["status"] == "already_applied", again
    assert calls == [], f"a second run linked again: {calls}"
    after = {p.name: (os.readlink(p), p.lstat().st_ino) for p in root.iterdir()}
    assert after == before, (before, after)


def test_a_real_dir_is_red_a_stray_link_is_repointed_a_dangling_one_removed() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_skill_links
    src, root, calls = _fixture("mixed")
    root.mkdir(parents=True)
    (root / "idea").mkdir()                                   # someone's real directory
    (root / "idea" / "mine.md").write_text("hand work\n")
    other = src.parent.parent / "other-checkout" / "skills" / "intent"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("# old\n")
    os.symlink(other, root / "intent", target_is_directory=True)  # another checkout
    gone = src.parent.parent / "removed-checkout" / "skills" / "retired"
    os.symlink(gone, root / "retired", target_is_directory=True)  # dangling into skills/
    keep = src.parent.parent / "elsewhere" / "mytool"
    os.symlink(keep, root / "mytool", target_is_directory=True)   # dangling, not into skills/

    r = ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls))
    assert r["status"] == "failed", r
    assert "RED" in r["detail"] and str(root / "idea") in r["detail"], r
    assert not os.path.islink(root / "idea"), "the real directory was replaced"
    assert (root / "idea" / "mine.md").read_text() == "hand work\n", "the real directory was touched"
    assert (root / "intent").resolve() == (src / "intent").resolve(), "the stray link was not re-pointed"
    assert (other / "SKILL.md").exists(), "re-pointing reached into the other checkout"
    assert not os.path.lexists(root / "retired"), "the dangling skills/ link was not removed"
    assert os.path.lexists(root / "mytool"), "a dangling link outside skills/ was removed"
    assert (root / "sorted").resolve() == (src / "sorted").resolve(), "sorted was not linked"


def test_dry_run_offers_and_writes_nothing() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_skill_links
    src, root, calls = _fixture("dry")
    r = ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls), dry_run=True)
    assert r["status"] == "offered", r
    for s in SKILLS:
        assert s in r["detail"], r
    assert calls == [] and not root.exists(), "dry run wrote"
    root.mkdir(parents=True)
    gone = src.parent.parent / "removed-checkout" / "skills" / "retired"
    os.symlink(gone, root / "retired", target_is_directory=True)
    r = ensure_skill_links(skills_src=src, skills_root=root, link=_counting(calls), dry_run=True)
    assert r["status"] == "offered" and "retired" in r["detail"], r
    assert calls == [] and sorted(p.name for p in root.iterdir()) == ["retired"], "dry run wrote"


if __name__ == "__main__":
    fails = 0
    for name in [n for n in PROVES["53e7979f76e7"].values()]:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fails else 0)

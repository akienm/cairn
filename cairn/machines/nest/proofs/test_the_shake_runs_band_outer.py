"""Proof for ticket 71cd4a62e8c5 — the nest is its own machine, and its shake runs band-outer.

Outline 16.2.3.1: "Bands are phases: preprocess, measure, postprocess." Outline 11.4.6 and
Akien 2026-09-29 (open-8ecde12362d6, option c): the shake ranks instead of cuts — a postprocess
sieve gets the stamps of every subject and stamps each survivor with a rank, and the survivors
come back in rank order. Outline 16.2 / Q#46: the nest is its own machine, not a file in base.

Teeth, one per falsifier clause:

  1. cairn.machines.nest.nest.BAND_NAMES is {0: preprocess, 1: measure, 2: postprocess};
  2. over a fixture nest with one sieve per band and three subjects, every measure sieve fires
     over every subject before any postprocess sieve fires;
  3. a postprocess sieve is called fire(name, subject, stamps) once per subject rolling up 1.0,
     stamps holding all three subjects' measure scores; its return lands in ranks[subject][name]
     and changes neither gradation nor roll_up;
  4. a preprocess sieve is called once with the whole subject set; a subject it does not return
     carries no later score and rolls up 1.0;
  5. with only measure sieves, findings, gradation and roll_up equal the old subject-outer
     shake's (a frozen copy held inline below), and order is the survivors in name order;
  6. cairn/tools/base/nest.py is absent, and no .py under cairn/ or bin/ imports
     cairn.tools.base.nest;
  7. order is exactly the survivors, sorted by the tuple of their band-2 ranks in assembled
     order, ties by subject name.

The subject is imported inside each tooth, so a hollow build reds each tooth by name.

    python3 cairn/machines/nest/proofs/test_the_shake_runs_band_outer.py   # exit 0 = green
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "71cd4a62e8c5": {
        "1": "band_one_is_measure",
        "2": "measure_fires_over_every_subject_first",
        "3": "postprocess_receives_every_stamp",
        "4": "preprocess_picks_the_subjects",
        "5": "a_measure_only_shake_is_unchanged",
        "6": "the_base_copy_is_gone",
        "7": "order_follows_the_ranks",
    },
}

FAILURES: list[str] = []
SUBJECTS = {"a": "apple", "b": "kiwi", "c": "banana"}


def _check(name: str, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}", flush=True)
    except Exception as exc:  # noqa: BLE001 — a tooth reds by name, whatever broke it
        print(f"  FAIL  {name}\n        {type(exc).__name__}: {str(exc)[:1200]}", flush=True)
        FAILURES.append(name)


def _m():
    from cairn.machines.nest import nest as m
    return m


def _three_band_world(log: list):
    """One sieve per band. pick (band 0) keeps every subject; short (band 1) cuts names over
    five letters; length (band 2) ranks by length."""
    def fire(name, subject, stamps=None):
        log.append((name, subject if name != "pick" else tuple(sorted(subject)), stamps))
        if name == "pick":
            return list(subject)
        if name == "short":
            return [f"{subject} long"] if len(SUBJECTS[subject] if subject in SUBJECTS else subject) > 5 else []
        if name == "length":
            return len(SUBJECTS[subject])
        raise KeyError(name)
    return {"pick": 0, "short": 1, "length": 2}, fire


def band_one_is_measure():
    assert _m().BAND_NAMES == {0: "preprocess", 1: "measure", 2: "postprocess"}, _m().BAND_NAMES


def _shake_keyed(log):
    """Shake with subjects keyed by name, the sieves reading the key."""
    m = _m()
    reaches, fire = _three_band_world(log)
    return m.shake(m.nest(reaches), {k: k for k in SUBJECTS}, fire)


def measure_fires_over_every_subject_first():
    log: list = []
    _shake_keyed(log)
    names = [e[0] for e in log]
    assert "length" in names, names
    last_measure = max(i for i, n in enumerate(names) if n == "short")
    first_post = min(i for i, n in enumerate(names) if n == "length")
    assert names.count("short") == 3, names
    assert last_measure < first_post, names


def postprocess_receives_every_stamp():
    log: list = []
    out = _shake_keyed(log)
    post = [e for e in log if e[0] == "length"]
    survivors = [s for s, v in out["roll_up"].items() if v == 1.0]
    assert sorted(e[1] for e in post) == sorted(survivors) == ["a", "b"], (post, out["roll_up"])
    for _n, _s, stamps in post:
        assert set(stamps) == set(SUBJECTS), stamps
        assert all(stamps[s].get("short") in (0.0, 1.0) for s in SUBJECTS), stamps
    assert out["ranks"] == {"a": {"length": 5}, "b": {"length": 4}}, out["ranks"]
    for scores in out["gradation"].values():
        assert "length" not in scores, out["gradation"]
    assert out["roll_up"] == {"a": 1.0, "b": 1.0, "c": 0.0}, out["roll_up"]


def preprocess_picks_the_subjects():
    m = _m()
    calls: list = []

    def fire(name, subject, stamps=None):
        calls.append((name, subject))
        if name == "pick":
            return [k for k in subject if k != "b"]
        return []
    out = m.shake(m.nest({"pick": 0, "short": 1}), dict(SUBJECTS), fire)
    picks = [c for c in calls if c[0] == "pick"]
    assert len(picks) == 1 and set(picks[0][1]) == set(SUBJECTS), calls
    assert ("short", "kiwi") not in calls, calls
    assert "short" not in out["gradation"]["b"], out["gradation"]
    assert out["roll_up"]["b"] == 1.0, out["roll_up"]


def _old_shake(assembled, subjects, fire):
    """The subject-outer shake as it stood at cairn/tools/base/nest.py before 71cd4a62e8c5."""
    findings: list = []
    gradation: dict = {}
    for subject_name, subject in subjects.items():
        scores: dict = {}
        for _band, names in assembled:
            for name in names:
                caught = fire(name, subject)
                findings.extend(caught)
                scores[name] = 0.0 if caught else 1.0
        gradation[subject_name] = scores
    return {"findings": findings, "gradation": gradation,
            "roll_up": {s: (min(v.values()) if v else 1.0) for s, v in gradation.items()}}


def a_measure_only_shake_is_unchanged():
    m = _m()

    def fire(name, subject):
        if name == "vowel":
            return [f"vowel in {subject}"] if "a" in subject else []
        return [f"{subject} long"] if len(subject) > 5 else []
    subj = {"z": "kiwi", "y": "apple", "x": "banana"}
    asm = m.nest({"vowel": 1, "len": 1})
    new, old = m.shake(asm, subj, fire), _old_shake(asm, subj, fire)
    for k in ("findings", "gradation", "roll_up"):
        assert new[k] == old[k], (k, new[k], old[k])
    assert new["order"] == ["z"], new["order"]
    subj2 = {"q": "kiwi", "p": "fig"}
    assert m.shake(asm, subj2, fire)["order"] == ["p", "q"]


def the_base_copy_is_gone():
    assert not (REPO / "cairn/tools/base/nest.py").exists(), "cairn/tools/base/nest.py still stands"
    hits = []
    for top in ("cairn", "bin"):
        for p in (REPO / top).rglob("*.py"):
            try:
                tree = ast.parse(p.read_text())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and (
                        n.module == "cairn.tools.base.nest"
                        or (n.module == "cairn.tools.base" and any(a.name == "nest" for a in n.names))):
                    hits.append(f"{p.relative_to(REPO)}:{n.lineno}")
                if isinstance(n, ast.Import) and any(a.name == "cairn.tools.base.nest" for a in n.names):
                    hits.append(f"{p.relative_to(REPO)}:{n.lineno}")
    assert not hits, hits


def order_follows_the_ranks():
    m = _m()

    def fire(name, subject, stamps=None):
        if name == "cost":
            return {"a": 2, "b": 1, "c": 1, "d": 1}[subject]
        if name == "speed":
            return {"a": 0, "b": 3, "c": 3, "d": 1}[subject]
        return [] if subject != "e" else ["cut"]
    subj = {k: k for k in "abcde"}
    out = m.shake(m.nest({"ok": 1, "cost": 2, "speed": 2}), subj, fire)
    # assembled band-2 order is sorted: cost, speed -> keys (1,1)d, (1,3)b, (1,3)c, (2,0)a
    assert out["order"] == ["d", "b", "c", "a"], out["order"]
    assert set(out["ranks"]) == set("abcd"), out["ranks"]


def main() -> int:
    for name, fn in [("band_one_is_measure", band_one_is_measure),
                     ("measure_fires_over_every_subject_first", measure_fires_over_every_subject_first),
                     ("postprocess_receives_every_stamp", postprocess_receives_every_stamp),
                     ("preprocess_picks_the_subjects", preprocess_picks_the_subjects),
                     ("a_measure_only_shake_is_unchanged", a_measure_only_shake_is_unchanged),
                     ("the_base_copy_is_gone", the_base_copy_is_gone),
                     ("order_follows_the_ranks", order_follows_the_ranks)]:
        _check(name, fn)
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

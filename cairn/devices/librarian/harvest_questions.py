"""librarian/harvest_questions.py — propose cross-domain questions in Akien's own words; take new ones.

Ticket c7cb0de74f71, outline 4.3.1.11.5: a deterministic pass proposes, he confirms; a librarian
command adds new ones as he says them. Akien, 2026-11-05: "i expect i have a couple of hundred in
my own head."

- ``harvest [--root PATH ...]`` — no inference. Reads his DATED notes
  (``~/TheIgorsProject/Akien/DATED/*.txt``) and the USER turns of Claude Code transcripts
  (``~/.claude/projects/*/*.jsonl``, ``type == "user"`` with string content — never an assistant
  turn). A candidate is a sentence ending in ``?`` of 3..15 words. One seen, normalized, on at
  least 3 distinct days and not already in the corpus is proposed. Writes the proposals file in
  instance space (``~/.cairn/devices/librarian/0/harvest/proposals.json``), overwritten each run.
- ``proposals`` — prints them, ``n  days  text``.
- ``confirm <n> [--function F]`` — appends proposal n to the corpus as verbatim, said_by Akien.
- ``add "<question?>" [--function F]`` — appends a question he just said, dated today.

Both corpus writes go through the artifact door (the corpus is a record of truth in its
jurisdiction), and the new corpus must pass ``cross_domain_questions.load()`` before a byte lands.
A question whose normalized text the corpus already holds is refused, naming the id.

    cairn librarian question harvest | proposals | confirm <n> | add "<q?>"
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from cairn.devices.librarian import cross_domain_questions as cdq

MIN_DAYS = 3
MIN_WORDS, MAX_WORDS = 3, 15
MAX_SOURCES = 5
ID_PREFIX = "Q-xd-"

_DATED_NAME = re.compile(r"^(\d{4})(\d{2})(\d{2})")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_QUOTES = "\"'`“”‘’"


class HarvestRefused(ValueError):
    """A confirm or add the corpus will not take; the message says why."""


def default_roots() -> list[Path]:
    home = Path.home()
    return [home / "TheIgorsProject" / "Akien" / "DATED", home / ".claude" / "projects"]


def proposals_path() -> Path:
    from cairn.tools.base.address import instance_path
    return instance_path("librarian", 0) / "harvest" / "proposals.json"


def normalize(text: str) -> str:
    t = " ".join(text.lower().split())
    t = t.strip(_QUOTES + " ")
    t = t.rstrip("?.!,;: " + _QUOTES)
    return t.strip(_QUOTES + " ")


def _candidates(text: str):
    """(line number, sentence) for each question-shaped sentence in ``text``."""
    for ln, line in enumerate(text.splitlines(), 1):
        for s in _SENTENCE.split(line):
            s = s.strip().strip(_QUOTES).strip()
            if not s.endswith("?"):
                continue
            if MIN_WORDS <= len(s.split()) <= MAX_WORDS:
                yield ln, s


def _dated_texts(path: Path):
    m = _DATED_NAME.match(path.name)
    if not m:
        return
    day = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    text = path.read_text(encoding="utf-8", errors="replace")
    for ln, s in _candidates(text):
        yield day, f"{path}:{ln}", s


def _jsonl_texts(path: Path):
    with path.open(encoding="utf-8", errors="replace") as fh:
        for ln, raw in enumerate(fh, 1):
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(rec, dict) or rec.get("type") != "user":
                continue
            content = (rec.get("message") or {}).get("content")
            ts = rec.get("timestamp")
            if not isinstance(content, str) or not isinstance(ts, str) or len(ts) < 10:
                continue
            for _, s in _candidates(content):
                yield ts[:10], f"{path}:{ln}", s


def _files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(set(root.glob("*.txt")) | set(root.glob("*.jsonl")) | set(root.glob("*/*.jsonl")))


def harvest(roots: list[Path] | None = None, *, corpus: Path | None = None) -> list[dict]:
    """The proposals, sorted by days desc then count desc, numbered from 1. Deterministic."""
    held = {normalize(q["question"]) for q in cdq.load(corpus)["questions"]}
    days: dict[str, set] = defaultdict(set)
    count: dict[str, int] = defaultdict(int)
    spell: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sources: dict[str, list] = defaultdict(list)
    for root in [Path(r) for r in (roots or default_roots())]:
        if not root.exists():
            continue
        for f in _files(root):
            texts = _jsonl_texts(f) if f.suffix == ".jsonl" else _dated_texts(f)
            for day, where, s in texts:
                key = normalize(s)
                if not key or key in held:
                    continue
                days[key].add(day)
                count[key] += 1
                spell[key][s] += 1
                if len(sources[key]) < MAX_SOURCES:
                    sources[key].append(where)
    keep = [k for k in days if len(days[k]) >= MIN_DAYS]
    keep.sort(key=lambda k: (-len(days[k]), -count[k], k))
    out = []
    for n, k in enumerate(keep, 1):
        text = sorted(spell[k].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        out.append({"n": n, "text": text, "days": len(days[k]), "count": count[k],
                    "first_day": min(days[k]), "sources": sources[k]})
    return out


def write_proposals(props: list[dict], path: Path | None = None) -> Path:
    p = Path(path) if path else proposals_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(props, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def read_proposals(path: Path | None = None) -> list[dict]:
    p = Path(path) if path else proposals_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def _next_id(doc: dict) -> str:
    nums = [int(q["id"][len(ID_PREFIX):]) for q in doc["questions"]
            if q["id"].startswith(ID_PREFIX) and q["id"][len(ID_PREFIX):].isdigit()]
    return f"{ID_PREFIX}{max(nums, default=0) + 1:03d}"


def _append(entry: dict, *, corpus: Path | None, why: str) -> dict:
    """Append one verbatim entry to the corpus through the artifact door, after load() passes."""
    from cairn.tools.artifact.artifact import write_json

    path = Path(corpus) if corpus else cdq.CORPUS
    doc = cdq.load(path)
    key = normalize(entry["question"])
    for q in doc["questions"]:
        if normalize(q["question"]) == key:
            raise HarvestRefused(f"{entry['question']!r} is already in the corpus as {q['id']}; nothing written")
    entry = {"id": _next_id(doc), **entry}
    doc["questions"].append(entry)
    with tempfile.TemporaryDirectory() as d:
        trial = Path(d) / "corpus.json"
        trial.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        cdq.load(trial)  # raises CorpusRefused before a byte lands
    write_json(path, doc, verb="write", why=why)
    return entry


def confirm(n: int, *, function: str = "", corpus: Path | None = None,
            proposals: Path | None = None) -> dict:
    props = {p["n"]: p for p in read_proposals(proposals)}
    if n not in props:
        raise HarvestRefused(f"no proposal {n} (there are {len(props)}); run harvest first")
    p = props[n]
    return _append({"question": p["text"], "function": function, "origin": "verbatim",
                    "said_by": "Akien", "date": p["first_day"], "source": p["sources"][0]},
                   corpus=corpus, why=f"c7cb0de74f71: Akien confirmed harvested proposal {n}")


def add(question: str, *, function: str = "", corpus: Path | None = None,
        today: str | None = None) -> dict:
    day = today or _dt.date.today().isoformat()
    return _append({"question": question, "function": function, "origin": "verbatim",
                    "said_by": "Akien", "date": day, "source": f"said to CC {day}"},
                   corpus=corpus, why="c7cb0de74f71: a question Akien just said")


def _opt(argv: list[str], name: str) -> str | None:
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return None


def main(argv: list[str]) -> int:
    argv = list(argv)
    function = _opt(argv, "--function") or ""
    pfile = _opt(argv, "--proposals")
    corpus = _opt(argv, "--corpus")
    roots = []
    while "--root" in argv:
        roots.append(Path(_opt(argv, "--root")))
    verb, rest = (argv[0], argv[1:]) if argv else ("proposals", [])
    try:
        if verb == "harvest":
            props = harvest(roots or None, corpus=corpus)
            p = write_proposals(props, pfile)
            print(f"{len(props)} proposal(s) -> {p}")
        elif verb == "proposals":
            for p in read_proposals(pfile):
                print(f"{p['n']}  {p['days']}  {p['text']}")
        elif verb == "confirm" and rest:
            print(json.dumps(confirm(int(rest[0]), function=function, corpus=corpus, proposals=pfile)))
        elif verb == "add" and rest:
            print(json.dumps(add(rest[0], function=function, corpus=corpus)))
        else:
            print('usage: question harvest [--root P ...] | proposals | confirm <n> | add "<q?>"',
                  file=sys.stderr)
            return 2
    except (HarvestRefused, cdq.CorpusRefused) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

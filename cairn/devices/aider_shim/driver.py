"""The caller the shim never had: one piece of a cast ticket, brief -> applied edit -> test.

WHAT WAS MISSING, IN THE DEVICE'S OWN WORDS. ``translate.py`` closes on the sentence *"A
brief is data; running it is someone else's."* Until this module there was no someone
else: the shim could translate a chart chain into a brief, install its surfaces and fence
aider's model calls, and nothing anywhere constructed an aider ``Coder``. The device was
complete and INERT — which meant the offload thesis (Law 1: spend the resolver on the
novel) could not be tried, and therefore could not be measured (Law 3).

EVERY BOUND IS A CONSTRUCTOR ARGUMENT, AND THAT IS THE DESIGN, NOT A STYLE. ``map_tokens=0``,
``auto_commits=False``, ``use_git=False``, the file set confined to the brief — a bound
enforced by inspecting the result afterwards is a bound the drive has already violated.
The only thing this module asserts after the fact is the *ask count*, and only because the
mechanism that holds it (``max_reflections``) is an attribute rather than a constructor
parameter in the held program.

WHAT IS DELIBERATELY NOT HERE. This driver cannot cross a workflow state, cannot write a
verdict artifact, and cannot commit: a driver that can certify its own work is not a
subordinate, it is an unsupervised second author. It returns data. Reading it, judging it
and crossing anything are the supervisor's acts.

THE MEASURED SURPRISE OF THIS BUILD (2026-08-17), and the reason :func:`_seed_model_info`
exists. Constructing aider's ``Model`` reaches ``raw.githubusercontent.com`` **outside the
fence** — ``ModelInfoManager.get_model_from_cached_json_db`` falls through to
``_update_cache``, which is a bare ``requests.get``. It is invisible most days because
``~/.aider/caches/model_prices_and_context_window.json`` has a 24h TTL and this box had a
19-hour-old copy; the first measurement therefore came back clean and only went red when
the cache was pointed at an empty directory. A check that is green because of a cache's
age is a coin-toss red. Seeding ``local_model_metadata`` from the interceptor's own
``_model_info`` short-circuits the lookup at its first line, so the reach never happens —
and it composes the surface's answer rather than inventing a second one.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.aider_shim import translate
from cairn.devices.aider_shim.fence import DEFAULT_RECORD, Fence
from cairn.devices.aider_shim.venv import VenvRunFailed, run_in_venv

#: Instance-space, beside the ask log the fence already writes (Law 6: the tool's state
#: berths under the holder that assembled it). One line per driven piece.
DEFAULT_DRIVES = Path.home() / ".cairn" / "devices" / "aider_shim" / "0" / "drives.jsonl"

#: WHERE AN UNDIRECTED DRIVE'S ASKS LAND — the fence's own constant, imported rather than
#: re-spelled, because two spellings of one path is how a store quietly becomes two.
#:
#: THIS IS A SCAR. Until the first live fire, ``log_path=None`` meant a ``SeenLog`` with
#: ``record_path=None`` — an in-memory log that dies with the venv process. Every ask was
#: stamped with its ticket, every tooth read the stamp back off disk and passed, and
#: nothing reached ``asks.jsonl``: the offload probe's population would have stayed empty
#: through any number of real drives, which is the very defect this device's ticket exists
#: to close. The teeth could not have caught it — each one PASSES a log path, so the
#: default was the one arrangement no fixture exercised. A fixture that supplies the
#: argument can never falsify the default that supplies none.
DEFAULT_ASKS = DEFAULT_RECORD

#: The repository the pieces are driven against. Same root translate.py reads berths for.
REPO = Path(__file__).resolve().parents[3]

#: aider's ``edit_format``, PINNED rather than inherited. aider derives the format from its
#: own MODEL_SETTINGS table, and this model is not in it, so the default is ``whole`` — the
#: format where the model returns entire rewritten files. For a build device that is both
#: the expensive shape and the destructive one (a truncated reply silently truncates the
#: file). ``diff`` is search/replace: a hunk that does not match is REFUSED by aider rather
#: than applied, which is the failure mode we want. Measured 2026-08-17: with the format
#: unpinned, a reply carrying a SEARCH/REPLACE block was written into the file verbatim.
EDIT_FORMAT = "diff"


class DriveRefused(RuntimeError):
    """The drive could not be set up. Distinct from a drive that ran and failed."""


@dataclass
class DriveResult:
    """What one driven piece did. Serializable by construction — the record IS this."""

    ticket: str
    piece_index: int
    model: str
    at: str
    files: list[str] = field(default_factory=list)
    read_only: list[str] = field(default_factory=list)
    prompt_chars: int = 0
    edit_format: str = EDIT_FORMAT
    max_reflections: int = 0

    #: The before/after images: {relpath: {"exists": bool, "sha256": str, "bytes": int}}.
    #: THIS PAIR IS WHAT MAKES EDIT SURVIVAL ANSWERABLE LATER, by a probe with no access to
    #: this process. Before alone cannot tell 'reverted' from 'never touched'.
    before: dict = field(default_factory=dict)
    after: dict = field(default_factory=dict)

    #: What aider says it edited, kept SEPARATE from the hashes on purpose: when the two
    #: disagree, one of them is wrong and a single merged field could not say which.
    aider_reported_edited: list[str] = field(default_factory=list)

    asks: list[dict] = field(default_factory=list)
    response_tail: str = ""
    num_reflections: int = 0
    test: dict = field(default_factory=dict)
    error: str = ""
    traceback: str = ""

    @property
    def hashes_moved(self) -> list[str]:
        return sorted(p for p in self.before
                      if self.after.get(p) != self.before.get(p))

    @property
    def allowed_asks(self) -> list[dict]:
        return [a for a in self.asks if a.get("verdict") == "allowed"]


# --------------------------------------------------------------------- the images

def _image(root: Path, rel: str) -> dict:
    p = Path(rel)
    if not p.is_absolute():
        p = Path(root) / rel
    if not p.exists():
        return {"exists": False}
    data = p.read_bytes()
    return {"exists": True, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def image_of(files, root=REPO) -> dict:
    """Keyed by repo-relative path — the record must still mean something on another box."""
    return {_rel(f, Path(root)): _image(Path(root), f) for f in files}


def survival(record: dict, root=REPO) -> dict:
    """Answer 'did this edit survive?' from the RECORD ALONE plus the world as it is now.

    Four answers, and the third is why the before-image is kept: ``untouched`` (the drive
    changed nothing here), ``survived`` (still what the drive left), ``reverted`` (back to
    what it was before the drive), ``changed_again`` (somebody moved it since, neither
    image matches). Collapsing untouched into reverted would report a piece that did
    nothing as a piece whose work was thrown away.
    """
    before, after = record.get("before") or {}, record.get("after") or {}
    out = {}
    for rel, was in before.items():
        became = after.get(rel)
        now = _image(Path(root), rel)
        if became == was:
            out[rel] = "untouched"
        elif now == became:
            out[rel] = "survived"
        elif now == was:
            out[rel] = "reverted"
        else:
            out[rel] = "changed_again"
    return out


# ------------------------------------------------------------------ the test command

def run_test(test_cmd: str, *, cwd=REPO, timeout: int = 900) -> dict:
    """Run the piece's test command and carry its result AS ITSELF.

    An empty command records ``ran: False`` — NOT a pass. A vacuous green is worse here
    than a red: a red is distrusted by construction and a false green gets leaned on
    (Law 8). And the streams are carried whole rather than reduced to a boolean, because
    the caller is the one who has to fix whatever failed (Law 7).
    """
    if not (test_cmd or "").strip():
        return {"cmd": test_cmd or "", "ran": False,
                "why": "no test_cmd was supplied — NOT a pass, and not a failure either"}
    try:
        r = subprocess.run(test_cmd, shell=True, cwd=str(cwd), capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        return {"cmd": test_cmd, "ran": True, "returncode": None, "timed_out": timeout,
                "stdout": expired.stdout or "", "stderr": expired.stderr or ""}
    return {"cmd": test_cmd, "ran": True, "returncode": r.returncode,
            "stdout": r.stdout, "stderr": r.stderr, "passed": r.returncode == 0}


# ------------------------------------------------------------------- the in-venv half

_DRIVE = r'''
import os, traceback
from pathlib import Path


def _seam(spec):
    """Resolve "module.path:attr" or "/abs/file.py:attr" INSIDE the venv.

    A seam is a callable and a callable does not cross a process boundary as JSON. Naming
    it instead keeps the injection serializable, which is what lets a proof drive the whole
    surface with no host and no network — the same seams interceptor.build already takes.
    """
    if not spec:
        return None
    where, _, attr = spec.rpartition(":")
    if where.endswith(".py"):
        import importlib.util
        s = importlib.util.spec_from_file_location("_cairn_seam_%s" % abs(hash(where)), where)
        mod = importlib.util.module_from_spec(s)
        s.loader.exec_module(mod)
    else:
        import importlib
        mod = importlib.import_module(where)
    return getattr(mod, attr)


from cairn.devices.aider_shim import holder
from cairn.devices.aider_shim.fence import SeenLog
from cairn.devices.aider_shim.interceptor import _model_info

log = SeenLog(record_path=Path(ARG["log_path"]) if ARG.get("log_path") else None)
holder.hold(ticket=ARG["ticket"], log=log,
            resolve=_seam(ARG.get("resolve")), resolver=_seam(ARG.get("resolver")))

import aider.models as M
from aider.coders import Coder
from aider.io import InputOutput

# THE UNFENCED REACH, CLOSED AT ITS FIRST LINE — see this module's docstring.
M.model_info_manager.local_model_metadata[ARG["model"]] = _model_info(ARG["model"], None)

os.chdir(ARG["repo"])
result = {"asks": log.entries, "aider_reported_edited": [], "response_tail": "",
          "num_reflections": 0, "edit_format": ARG["edit_format"],
          "error": "", "traceback": ""}
try:
    coder = Coder.create(
        main_model=M.Model(ARG["model"]),
        io=InputOutput(pretty=False, yes=True, fancy_input=False),
        fnames=ARG["files"],
        read_only_fnames=ARG["read_only"],
        edit_format=ARG["edit_format"],
        map_tokens=ARG["map_tokens"],     # 0 — the repo map traces to no berthed field
        auto_commits=False,               # the apprentice never commits on our behalf
        dirty_commits=False,
        auto_lint=False,
        auto_test=False,                  # WE run the test, so its result is ours to carry
        use_git=False,
        stream=False,
        suggest_shell_commands=False,
        detect_urls=False,
        analytics=None,
        verbose=False,
    )
    # The cap. aider's run_one loops while self.reflected_message and returns as soon as
    # `self.num_reflections >= self.max_reflections`; at 0 that is true at the first
    # reflection, so one run() is one allowed ask. An attribute, not a ctor argument —
    # which is exactly why the ask log has to be able to falsify it from outside.
    coder.max_reflections = ARG["max_reflections"]
    out = coder.run(with_message=ARG["prompt"])
    result["response_tail"] = (out or "")[-4000:]
    result["aider_reported_edited"] = sorted(coder.aider_edited_files or [])
    result["num_reflections"] = getattr(coder, "num_reflections", 0)
    result["edit_format"] = coder.edit_format
except BaseException as bad:
    # The ask log is the evidence, and a raise that took it with it would leave the
    # refusal unprovable. Emit the failure AND the log; the caller decides.
    result["error"] = "%s: %s" % (type(bad).__name__, bad)
    result["traceback"] = traceback.format_exc()[-4000:]
result["asks"] = log.entries
emit(result)
'''


# ------------------------------------------------------------------------ the drive

def drive(ticket: str, piece_index: int, *, test_cmd: str = "", repo=REPO,
          berths_root=None, model: str | None = None, log_path=None,
          drives_path=DEFAULT_DRIVES, seams: dict | None = None,
          max_reflections: int = 0, timeout: int = 900) -> DriveResult:
    """Carry ONE piece of a cast ticket from its berthed brief to an applied edit + test.

    ``seams`` names the injected ``resolve``/``resolver`` as ``"module:attr"`` or
    ``"/abs/file.py:attr"`` — the same two seams ``interceptor.build`` takes, passed by name
    because the venv is a different process. Absent, the real metered door is used.
    """
    b = translate.brief(ticket, piece_index, test_cmd=test_cmd, berths_root=berths_root)
    return drive_brief(b, repo=repo, model=model, log_path=log_path,
                       drives_path=drives_path, seams=seams,
                       max_reflections=max_reflections, timeout=timeout)


def drive_brief(b, *, repo=REPO, model: str | None = None, log_path=None,
                drives_path=DEFAULT_DRIVES, seams: dict | None = None,
                max_reflections: int = 0, timeout: int = 900) -> DriveResult:
    """Drive a Brief that is already in hand. THE SEAM THE PROOFS USE, and it is the real
    one: :func:`drive` is this plus ``translate.brief``. Splitting it means a tooth can
    exercise the whole arrangement — venv, surfaces, real Coder, fence, record — against a
    hand-built Brief, without a chart chain and without instance-space berths."""
    ticket, piece_index = b.ticket, b.piece_index
    model = model or Fence().models[0]
    log_path = DEFAULT_ASKS if log_path is None else log_path
    if not b.files:
        raise DriveRefused(
            f"the brief for {ticket!r} piece {piece_index} names no editable file — there "
            "is nothing for the apprentice to edit, and driving anyway would spend a model "
            "call to produce a chat message. Fix the chain's holdings, not this call."
        )
    repo = Path(repo)
    before = image_of(b.files, repo)
    payload = {
        "repo": str(repo), "ticket": ticket, "model": model, "prompt": b.prompt,
        "files": list(b.files),           # translate hands these back ABSOLUTE, already
        "read_only": list(b.read_only),   # split by constrain's bound, not by convenience
        "map_tokens": b.map_tokens, "edit_format": EDIT_FORMAT,
        "max_reflections": max_reflections,
        "log_path": None if log_path is None else str(log_path),
        "resolve": (seams or {}).get("resolve"),
        "resolver": (seams or {}).get("resolver"),
    }
    out = run_in_venv(_DRIVE, payload, timeout=timeout, cwd=str(repo))
    after = image_of(b.files, repo)
    result = DriveResult(
        ticket=ticket, piece_index=piece_index, model=model,
        at=datetime.now(timezone.utc).isoformat(),
        files=[_rel(f, repo) for f in b.files],
        read_only=[_rel(f, repo) for f in b.read_only], prompt_chars=len(b.prompt),
        edit_format=out.get("edit_format", EDIT_FORMAT), max_reflections=max_reflections,
        before=before, after=after,
        aider_reported_edited=[_rel(p, repo) for p in out.get("aider_reported_edited", [])],
        asks=out.get("asks", []), response_tail=out.get("response_tail", ""),
        num_reflections=out.get("num_reflections", 0),
        error=out.get("error", ""), traceback=out.get("traceback", ""),
    )
    result.test = run_test(b.test_cmd, cwd=repo)
    record(result, path=drives_path)
    return result


def _rel(p: str, repo: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(Path(repo).resolve()))
    except Exception:
        return str(p)


def record(result: DriveResult, *, path=DEFAULT_DRIVES) -> dict:
    """Append one drive to the record. THE ONLY WRITER — a probe reads, it never mints."""
    row = asdict(result)
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def drives(path=DEFAULT_DRIVES) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


if __name__ == "__main__":  # pragma: no cover — a hand's entrance, not a proved surface
    args = sys.argv[1:]
    if len(args) < 2:
        print("usage: python -m cairn.devices.aider_shim.driver <ticket> <piece_index> "
              "[test_cmd]", file=sys.stderr)
        raise SystemExit(2)
    try:
        r = drive(args[0], int(args[1]), test_cmd=args[2] if len(args) > 2 else "")
    except VenvRunFailed as failed:
        print(str(failed), file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(asdict(r), indent=2, ensure_ascii=False))

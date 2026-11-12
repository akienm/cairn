"""Proof for ticket 386ea8131006 — the WATCHME gate is CodeMother's.

Outline 3.3.4, 3.3.4.1 and 9.4.1.5 (Akien 2026-11-10): the gates are CodeMother's; the harbor's
bus face answers status queries and the crossing notice only, and its ``watch`` verb leaves. A
WATCHME probe's red finding over a ticket at a rest makes that ticket's own instance fail the gate:
it goes to FIXME carrying the finding, tells the harbor, and waits in the trouble lane CC and
Akien read, posting to no design verb (outline 3.3.4, Q#85, ticket 794835a34ec9).

Clauses 2-4 run in a scratch world: a tickets store (the live store charter copied in, one fixture
plan and state), a component with a charter and a probe, ``ticket_file._TICKETS`` pointed at the
store, and a spy participant that bounces every request. The crossing is the REAL emit chokepoint.
Clause 5 reads the live tree and the live commons beside the main tree.

What a hollow build cannot pass (Law 8): without gate.py every fixture tooth fails importing it;
with the old probes every probe still posts to harbor_master and clause 5 reds by file.

    python3 cairn/devices/codemother/machines/watchme/proofs/test_a_watchme_finding_fails_its_ticket.py
"""

from __future__ import annotations

import ast
import importlib
import json
import re
import shutil
import subprocess
import sys
from cairn.tools.scratch.scratch import scratch_dir
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "386ea8131006": {
        "1": "test_codemother_holds_the_watch_and_the_harbor_does_not",
        "2": "test_a_red_finding_fails_the_ticket_into_the_trouble_lane",
        "3": "test_a_green_finding_or_a_ticket_not_at_rest_moves_nothing",
        "4": "test_a_malformed_watch_is_refused_by_name",
        "5": "test_no_standing_probe_still_posts_to_the_harbor",
    },
    "794835a34ec9": {
        "4": "test_a_red_finding_fails_the_ticket_into_the_trouble_lane",
    },
    "3ee0d23164e6": {
        "all": "test_a_red_finding_fails_a_host_seam_back_to_fixme_before_pocme",
    },
}

_TID = "fe12dc34ba56"
_VERB = "machines/watchme/watch"


def _main_tree() -> Path:
    """The hollow runs this proof in a /tmp worktree with no CairnCommons beside it; the commons
    is read beside the main tree (the test_watch_receives_a_finding.py precedent)."""
    common = subprocess.run(["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute",
                             "--git-common-dir"], capture_output=True, text=True)
    return Path(common.stdout.strip()).parent if common.returncode == 0 else _REPO_ROOT


_COMMONS = _main_tree().parent / "CairnCommons"


def _root_the_class_defs_if_this_is_a_worktree() -> None:
    """emit's load_class_def reads node classes from the commons; in a hollow worktree there is
    none beside it, so read the main tree's (the harbor proof's precedent)."""
    if _REPO_ROOT.resolve() == _main_tree().resolve():
        return
    from cairn.tools.base import transitions as _t
    classes, real_load = _COMMONS / "node_classes", _t.load_class_def

    def _rooted_load(node_class, *, root=None):
        if root is None or not Path(root).is_dir():
            root = classes
        return real_load(node_class, root=root)

    _t.load_class_def = _rooted_load


_root_the_class_defs_if_this_is_a_worktree()


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


class _Spy:
    """A bus participant: records every request and post; bounces every request."""

    def __init__(self):
        self.requests: list[dict] = []
        self.posts: list[dict] = []

    def request(self, *, to, channel="personal", why, verb="", body=None, timeout=30.0):
        self.requests.append({"to": to, "verb": verb, "body": body})
        return {"body": {"is_bounce": True, "reason": "fixture: no handler"}}

    def post(self, *, to, channel="personal", why, verb="", body=None, reply_to=None):
        self.posts.append({"to": to, "verb": verb, "body": body})
        return {"id": f"post-{len(self.posts)}"}


_HOST_SEAM_AT_WATCHME = ("host-seam@v1: THINKME -> TICKETME -> RESEARCHME -> POCME -> PROVEME -> "
                         "[WATCHME(the host still holds)] -> PROVED")


@contextmanager
def _world(cursor: str = "PROVED", *, watchme=None, workflow=None):
    import cairn.tools.base.ticket_file as tf
    tmp = scratch_dir("watchme-gate-")
    roots = {"repo": tmp / "repo", "commons": tmp / "commons", "instance": tmp / "instance"}
    store = roots["commons"] / "tickets"
    store.mkdir(parents=True)
    roots["instance"].mkdir()
    shutil.copy(_COMMONS / "tickets" / "_charter+why.json", store / "_charter+why.json")
    comp = roots["repo"] / "comp"
    (comp / "probes").mkdir(parents=True)
    (comp / "intention+why.json").write_text("{}", "utf-8")
    (comp / "probes" / "p.py").write_text("", "utf-8")
    (roots["repo"] / "loose").mkdir()
    (roots["repo"] / "loose" / "p.py").write_text("", "utf-8")
    plan = store / f"{_TID}-a-watched-fixture.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a watched fixture",
                                "owning_intention": "comp/intention+why.json"}, indent=2) + "\n")
    spec = {"probe": "comp/probes/p.py"} if watchme is None else watchme
    wf = workflow or _wf(cursor)
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": wf,
                                               "node_class": wf.split("@")[0], "watchme": spec},
                                              indent=2) + "\n")
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "roots": roots, "plan": plan, "comp": comp, "store": store}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _bytes(w) -> bytes:
    import cairn.tools.base.ticket_file as tf
    return w["plan"].read_bytes() + tf.state_path(w["plan"]).read_bytes()


def _watch(w, body: dict, sender="fixture_prober"):
    from cairn.devices.codemother.machines.watchme.gate import WatchmeGate
    spy = _Spy()
    env = {"id": "fixture-watch", "to": "codemother", "verb": _VERB,
           "why": "fixture WATCHME finding", "body": body}
    if sender is not None:
        env["sender"] = sender
    reply = WatchmeGate(participant=spy, roots=w["roots"]).declared_verbs()["watch"](env)
    return reply, spy


# --- teeth ------------------------------------------------------------------

def test_codemother_holds_the_watch_and_the_harbor_does_not():
    from cairn.devices.codemother.shim import CodeMotherDevice
    verbs = CodeMotherDevice().declared_verbs()
    assert _VERB in verbs, f"codemother declares no {_VERB}: {sorted(verbs)}"
    # read the harbor's verb table as text, never by import (RULE 1)
    src = (_REPO_ROOT / "cairn/devices/cairn/machines/harbor_master/device.py").read_text("utf-8")
    keys: list[str] = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == "declared_verbs":
            for d in ast.walk(node):
                if isinstance(d, ast.Dict):
                    keys += [k.value for k in d.keys if isinstance(k, ast.Constant)]
    assert "crossing" in keys, f"the harbor's verb table did not read: {keys}"
    assert "watch" not in keys, f"harbor_master still declares watch: {keys}"


def test_a_red_finding_fails_the_ticket_into_the_trouble_lane():
    import cairn.tools.base.ticket_file as tf
    with _world("PROVED") as w:
        reply, spy = _watch(w, {"ticket": _TID, "holds": False, "finding": "fixture finding"})
        assert reply.get("accepted") is True and reply.get("acted") == "fixme", reply
        assert reply.get("device") == "codemother" and reply.get("verb") == "watch", reply
        st = json.loads(tf.state_path(w["plan"]).read_text("utf-8"))
        assert "[FIXME" in st["workflow_and_state"], st["workflow_and_state"]
        assert st.get("fixme") == [{"n": 1, "kind": "watchme", "missing": "fixture finding"}], st
        hist = w["comp"] / "history.json"
        assert hist.is_file(), "no crossing journaled beside the probe's charter"
        raw = json.loads(hist.read_text("utf-8"))
        last = (raw.get("entries", raw) if isinstance(raw, dict) else raw)[-1]
        assert last.get("to") == "FIXME" and "WATCHME finding" in json.dumps(last), last
        back = [p for p in spy.posts if p["to"] == "harbor_master" and p["verb"] == "crossing"]
        assert len(back) == 1 and back[0]["body"]["direction"] == "back", spy.posts
        assert spy.requests == [], f"a refused ticket asked something: {spy.requests}"
        ident = f"ticket-refused-{_TID}-at-watchme"
        assert reply.get("queued") is False and reply.get("trouble") == ident, reply
        found = "\n".join(p.read_text("utf-8", errors="replace") for p in w["tmp"].rglob("*")
                          if p.is_file() and p.suffix in (".json", ".jsonl"))
        assert ident in found, f"no trouble {ident} in the fixture roots"


def test_a_red_finding_fails_a_host_seam_back_to_fixme_before_pocme():
    """Ticket 3ee0d23164e6: host-seam v1 has no BUILDME, and Akien's answer to open-8bc1eaf1f568
    puts its FIXME before POCME. A red finding over a host-seam@v1 ticket at WATCHME answers
    acted='fixme' and stands the cursor at [FIXME] directly before POCME."""
    import cairn.tools.base.ticket_file as tf
    from cairn.tools.base.transitions import parse_workflow
    with _world(workflow=_HOST_SEAM_AT_WATCHME) as w:
        reply, _spy = _watch(w, {"ticket": _TID, "holds": False, "finding": "fixture finding"})
        assert reply.get("accepted") is True and reply.get("acted") == "fixme", reply
        st = json.loads(tf.state_path(w["plan"]).read_text("utf-8"))
        got = parse_workflow(st["workflow_and_state"])
        assert got.here == "FIXME", st["workflow_and_state"]
        assert got.path[got.cursor + 1] == "POCME", st["workflow_and_state"]


def test_a_green_finding_or_a_ticket_not_at_rest_moves_nothing():
    with _world("PROVED") as w:
        before = _bytes(w)
        reply, spy = _watch(w, {"ticket": _TID, "holds": True, "finding": ""})
        assert reply.get("accepted") is True and reply.get("acted") == "none", reply
        assert _bytes(w) == before and not (w["comp"] / "history.json").exists()
        assert spy.posts == [] and spy.requests == [], (spy.posts, spy.requests)
    with _world("BUILDME") as w:
        before = _bytes(w)
        reply, spy = _watch(w, {"ticket": _TID, "holds": False, "finding": "fixture finding"})
        assert reply.get("accepted") is True and reply.get("acted") == "none", reply
        assert "BUILDME" in reply.get("said", ""), reply
        assert _bytes(w) == before and spy.posts == [] and spy.requests == []


def test_a_malformed_watch_is_refused_by_name():
    red = {"ticket": _TID, "holds": False, "finding": "x"}
    cases = [
        (red, None, None, "sender"),
        ({"holds": False, "finding": "x"}, "p", None, "ticket"),
        ({**red, "ticket": "ffffffffffff"}, "p", None, "ticket"),
        ({**red, "holds": "yes"}, "p", None, "holds"),
        ({**red, "finding": ""}, "p", None, "finding"),
        (red, "p", {}, "probe"),
        (red, "p", {"probe": "loose/p.py"}, "charter"),
    ]
    for body, sender, watchme, field in cases:
        with _world("PROVED", watchme=watchme) as w:
            before = _bytes(w)
            try:
                reply, spy = _watch(w, body, sender)
            except Exception as exc:  # noqa: BLE001
                raise AssertionError(f"{body!r} raised instead of refusing: {exc!r}") from exc
            assert reply.get("accepted") is False, f"{body!r}/{watchme!r} not refused: {reply}"
            assert field in reply.get("reason", ""), \
                f"{body!r}/{watchme!r}: the refusal does not name {field!r}: {reply.get('reason')!r}"
            assert _bytes(w) == before and spy.posts == [], f"{body!r} changed something"


_TO_HARBOR = re.compile(r"""to\s*=\s*["']harbor_master["']""")
_VERB_WATCH = re.compile(r"""verb\s*=\s*["']watch["']""")


def test_no_standing_probe_still_posts_to_the_harbor():
    stale = []
    for top in ("cairn", "bin", "skills", "press_office"):
        for p in sorted((_REPO_ROOT / top).rglob("probes/*.py")):
            text = p.read_text("utf-8", errors="replace")
            if _TO_HARBOR.search(text) and _VERB_WATCH.search(text):
                stale.append(str(p.relative_to(_REPO_ROOT)))
    assert not stale, f"{len(stale)} probe(s) still post watch to harbor_master: {stale[:8]}"

    from cairn.tools.base.ticket_file import plans, read_ticket
    from cairn.tools.base.transitions import parse_workflow
    named, wrong, checked = [], [], 0
    for path in plans(_COMMONS / "tickets"):
        try:
            doc = read_ticket(path)
            here = parse_workflow(doc["workflow_and_state"]).here
        except Exception:  # noqa: BLE001 — not a standing ticket this tooth can read
            continue
        specs = doc.get("watchme")
        for spec in (specs if isinstance(specs, list) else [specs]):
            if not isinstance(spec, dict):
                continue
            if "harbor_master watch verb" in json.dumps(spec.get("receiver")):
                named.append(doc.get("id"))
            probe = str(spec.get("probe") or "")
            if here not in ("PROVED", "WATCHME") or not probe.endswith(".py") \
                    or not (_REPO_ROOT / probe).is_file():
                continue
            mod = importlib.import_module(probe[:-3].replace("/", "."))
            pr = getattr(mod, "PROBE", None)
            if pr is None or pr.verb not in ("watch", _VERB):
                continue
            checked += 1
            if (pr.to, pr.verb) != ("codemother", _VERB):
                wrong.append(f"{doc.get('id')}: {probe} posts {pr.verb!r} to {pr.to!r}")
    assert not named, f"{len(named)} ticket record(s) still name the harbor watch receiver: {named[:8]}"
    assert not wrong, f"{len(wrong)} standing probe(s) post elsewhere: {wrong[:8]}"
    assert checked >= 50, f"only {checked} standing watch probes read — the population vanished"


if __name__ == "__main__":
    checks = [
        test_codemother_holds_the_watch_and_the_harbor_does_not,
        test_a_red_finding_fails_the_ticket_into_the_trouble_lane,
        test_a_red_finding_fails_a_host_seam_back_to_fixme_before_pocme,
        test_a_green_finding_or_a_ticket_not_at_rest_moves_nothing,
        test_a_malformed_watch_is_refused_by_name,
        test_no_standing_probe_still_posts_to_the_harbor,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}", flush=True)
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}", flush=True)
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — a WATCHME finding fails its ticket at CodeMother's gate, and no probe posts to the harbor")

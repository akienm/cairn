"""PROOF — a ticket has ONE status, and the three reports are venn diagrams of one reader.

Ticket 3feb201c84ea (Akien, 2026-09-06): "for a given ticket that appers in all the
places, i should see the same status. it has one status." / "they're kinda venn
diagrams. so whatever's in the way of that's a bug."

The three reports `akienupdate` prints — the operator inbox, the codemother
dashboard, the harbor map — must wear, for every ticket id on more than one of them,
the byte-identical status label. The label is derived once, in
operator_inbox.read_tickets; nothing here re-derives it — the teeth compare the
printed rows, which is what Akien reads. Over the fixture this proof renders the
inbox only; the dashboard and the map render it at their owners (0c6f774d9ad8,
cbbb651f4552), and over the live world this proof reads the other two as the commands
Akien types, `cairn codemother show dashboard` and `cairn harbor_master show map open`
(ticket 96afb3586d2e, RULE 1: a tool's proofs reach a device only through its public face).

What a hollow build cannot pass (Law 8):
  - An inbox that parses the cursor its own way fails
    test_fixture_one_label_per_id_across_all_three the moment a WATCHME(x):waiting or
    a prose cursor is in the fixture — those are the forms the readers disagreed on.
  - A header that buckets 'other' fails test_fixture_headers_sum_with_no_other.
  - A dashboard or map that wears another label, live, fails the live teeth.

    python3 cairn/tools/operator_inbox/proofs/test_one_status_everywhere.py   # exit 0 = green
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The subject — the one reader and the three reports over it — is bound at CALL time
# (``_world()``), never at import: this build added the reader's names, so a hollow
# reading takes them away, and a proof that binds them at import cannot reach its first
# tooth (proof_binds_its_subject_at_call_time). Nothing below names the subject at
# module level.

PROVES = {"3feb201c84ea": {
    "1": "test_fixture_one_label_per_id_across_all_three",
    "2": "test_fixture_headers_sum_with_no_other",
    "3": "test_source_one_label_deriving_function_no_private_cursor_regex",
    "4": "test_live_map_rows_carry_date_and_id_and_groups_are_stage_vocabulary",
    "5": "test_live_every_open_ticket_carries_owning_intention",
}}
# Clauses (6) and (7) — the map's prose-standing finding and its crossing patch — are the
# harbor master's to prove and berth there (ticket cbbb651f4552); (6) live is still read here,
# off the printed map, in test_live_map_rows_carry_date_and_id_and_groups_are_stage_vocabulary.

_ROW = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([0-9a-f]{12})\s+(.*)$")
_GROUP = re.compile(r"^\s*(\S+) \((\d+)\):$")

# The four readers clause (3) greps — one label-deriving function among them, in the inbox.
_READERS = (
    "cairn/tools/operator_inbox/inbox.py",
    "cairn/devices/codemother/dashboard.py",
    "cairn/devices/cairn/machines/harbor_master/register.py",
    "cairn/devices/cairn/machines/harbor_master/device.py",
)
# Which components' history standing is prose is MEASURED each run from the map's own
# FINDING lines, never listed here: the list of five frozen at 3feb201c84ea went stale when cc
# and charter returned to stage-token standing (measured 2026-10-04, e4138780377a build).
_FINDING = re.compile(r"^FINDING: (\S+) history standing is prose")


def _prose_standing(hmap: str) -> list[str]:
    return sorted({m.group(1).rsplit("/", 1)[-1]
                   for m in map(_FINDING.match, hmap.splitlines()) if m})


def _command(*argv: str) -> str:
    """A device's report as Akien types it — its command, never its module (RULE 1)."""
    import subprocess
    r = subprocess.run([str(_REPO_ROOT / "bin" / "cairn"), *argv], capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, f"cairn {' '.join(argv)} exited {r.returncode}: {r.stderr[-400:]}"
    return r.stdout


class _world:
    """The subject, bound when a tooth asks for it."""

    def __init__(self):
        from cairn.tools.base.transitions import TERMINAL_STATES
        from cairn.tools.operator_inbox import inbox
        self.TERMINAL_STATES = TERMINAL_STATES
        self.is_stage_token = inbox.is_stage_token
        self.UNPARSED = inbox.UNPARSED
        self.format_inbox = inbox.format_inbox
        self.format_summary = inbox.format_summary
        self.read_tickets = inbox.read_tickets
        # the commons the reader reads — not a path beside this file, which in a
        # worktree (hollow, scratch) is beside nothing
        self.COMMONS_ROOT = inbox.COMMONS_ROOT


# --- the fixture -------------------------------------------------------------

_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> WATCHME(fx) -> PROVED"


def _wf(cursor: str) -> str:
    """Render the class path with the bracketed cursor at its own seat."""
    seat = cursor.split("(")[0].split(":")[0]
    stages = _WF.split(": ", 1)[1].split(" -> ")
    out = []
    for s in stages:
        out.append(f"[{cursor}]" if s.split("(")[0] == seat else s)
    return "code-seam@v2: " + " -> ".join(out)


FIXTURE_TICKETS = [
    # id, title, date, workflow_and_state, owning_intention
    ("aa0000000001", "think-about-it", "2026-09-01", _wf("THINKME"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000002", "cast-it", "2026-09-02", _wf("TICKETME:waiting"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000003", "prove-it", "2026-09-03", _wf("PROVEME:waiting"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000004", "watch-it-waiting", "2026-09-04", _wf("WATCHME(fx):waiting"),
     "cairn/tools/other_thing/intention+why.json"),
    ("aa0000000005", "watch-it-armed", "2026-09-05", _wf("WATCHME(fx)"),
     "cairn/tools/other_thing/intention+why.json"),
    ("aa0000000006", "done-and-dusted", "2026-09-06", _wf("PROVED"),
     "cairn/tools/fx_widget/intention+why.json"),
    ("aa0000000007", "prose-state", "2026-09-06", "waiting on akien",
     None),
]
_NON_TERMINAL = {t[0] for t in FIXTURE_TICKETS if t[3] != _wf("PROVED")}


def _build_fixture(root: Path) -> tuple[Path, Path]:
    tickets = root / "tickets"
    tickets.mkdir()
    for tid, title, date, wf, owning in FIXTURE_TICKETS:
        doc = {"id": tid, "title": title, "date": date, "workflow_and_state": wf,
               "node_class": "code-seam"}
        if owning:
            doc["owning_intention"] = owning
        (tickets / f"{tid}-{title}.json").write_text(json.dumps(doc, indent=2))
    (tickets / "_charter+why.json").write_text(json.dumps({"role": "store-charter"}))
    cairn_root = root / "cairn"
    comp = cairn_root / "tools" / "fx_widget"
    comp.mkdir(parents=True)
    (comp / "widget.py").write_text("# fixture component\n")
    (comp / "history.json").write_text(json.dumps([
        {"at": "2026-08-28", "seq": 0,
         "standing": "Built and proved — three teeth green, probe armed"}]))
    return tickets, cairn_root


def _stub_data(w: _world, tickets_dir: Path) -> dict:
    """The inbox's data dict with every lane but tickets stubbed empty — the tickets
    lane is the real reader over the fixture."""
    return {
        "troubles": {"live": [], "live_count": 0, "total_count": 0},
        "email": {"count": 0},
        "adjudications": {"findings": [], "count": 0},
        "lap": {"items": [], "count": 0, "error": None},
        "questions": {"open": [], "count": 0},
        "design": {},
        "tickets": w.read_tickets(tickets_dir=tickets_dir),
        "intentions": {"count": 0, "items": []},
        "ideas": {"count": 0, "items": []},
    }


def _render_inbox(w: _world, tickets_dir: Path) -> str:
    return w.format_inbox(_stub_data(w, tickets_dir))


# --- readers over the PRINTED text (what Akien sees) -------------------------

def _rows(text: str) -> dict[str, str]:
    """{id: label} for every ticket atom printed. A single id printed with two labels
    on one report is itself a divergence, and raises here."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        _, label, tid, _ = m.groups()
        assert out.get(tid, label) == label, (
            f"{tid} printed twice with two labels on one report: {out[tid]} / {label}")
        out[tid] = label
    return out


def _groups(text: str, start: str | None = None, stop: str | None = None) -> dict[str, int]:
    """{label: n} from the 'LABEL (n):' group headers between two markers."""
    lines = text.splitlines()
    if start is not None:
        lines = lines[next(i for i, l in enumerate(lines) if start in l) + 1:]
    if stop is not None:
        lines = lines[:next(i for i, l in enumerate(lines) if stop in l)]
    out: dict[str, int] = {}
    for line in lines:
        m = _GROUP.match(line)
        if m and not m.group(1).startswith("DONE"):
            out[m.group(1)] = int(m.group(2))
    return out


def _header_counts(summary: str) -> dict[str, int]:
    """{label: n} from the inbox header's '(LABEL n, LABEL n)'."""
    m = re.search(r"tickets \(([^)]*)\)", summary)
    assert m, f"no ticket breakdown in the summary: {summary!r}"
    out = {}
    for part in m.group(1).split(", "):
        label, n = part.rsplit(" ", 1)
        out[label] = int(n)
    return out


# --- fixture teeth ------------------------------------------------------------

def test_fixture_one_label_per_id_across_all_three():
    """Over the fixture the inbox prints the reader's label on every row it shows; the
    dashboard and the map are held to the same reader at their owners."""
    w = _world()
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, _ = _build_fixture(Path(td))
        rows = _rows(_render_inbox(w, tickets_dir))
        labels = {r["id"]: r["label"] for r in w.read_tickets(tickets_dir=tickets_dir)["records"]}
        assert set(labels) == _NON_TERMINAL, f"reader open set {sorted(labels)}"
        assert rows and set(rows) <= set(labels), f"inbox rows {sorted(rows)}"
        divergent = {tid: (rows[tid], labels[tid]) for tid in rows if rows[tid] != labels[tid]}
        assert not divergent, f"one ticket, two statuses (inbox, reader): {divergent}"
        # the labels are the ones the fixture carries — the forms that used to diverge
        assert labels["aa0000000004"] == "WATCHME:waiting"
        assert labels["aa0000000005"] == "WATCHME"
        assert labels["aa0000000002"] == "TICKETME:waiting"
        assert labels["aa0000000007"] == w.UNPARSED, "a prose cursor is loud (Law 7), never hidden"
        assert "aa0000000006" not in labels, "a PROVED ticket is not an open one"


def test_fixture_headers_sum_with_no_other():
    w = _world()
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, _ = _build_fixture(Path(td))
        data = _stub_data(w, tickets_dir)
        summary = w.format_summary(data)
        header = _header_counts(summary)
        assert "other" not in summary.lower(), summary
        assert sum(header.values()) == len(_NON_TERMINAL) == data["tickets"]["total_not_done"]
        counted: dict[str, int] = {}
        for r in data["tickets"]["records"]:
            counted[r["label"]] = counted.get(r["label"], 0) + 1
        assert header == counted, f"the header {header} is not the reader's labels {counted}"
        assert list(header)[0] == "THINKME" and list(header)[-1] == w.UNPARSED


# --- live teeth: the real world, the real three reports ----------------------

def _live_map() -> str:
    return _command("harbor_master", "show", "map", "open")


def test_live_one_label_per_id_across_the_three_reports():
    w = _world()
    live = {r["id"]: r["label"] for r in w.read_tickets()["records"]}
    assert live, "no live tickets — a green here would be hollow"
    dash = _command("codemother", "show", "dashboard")
    hmap = _live_map()
    d_rows, m_rows = _rows(dash), _rows(hmap)
    assert set(d_rows) == set(m_rows) == set(live), (
        f"the dashboard, the map and the reader list different tickets: "
        f"dash-only {sorted(set(d_rows) - set(m_rows))[:5]}, map-only {sorted(set(m_rows) - set(d_rows))[:5]}, "
        f"reader-only {sorted(set(live) - set(d_rows) - set(m_rows))[:5]}")
    divergent = [(tid, live[tid], d_rows[tid], m_rows[tid]) for tid in live
                 if not (live[tid] == d_rows[tid] == m_rows[tid])]
    assert not divergent, f"one ticket, two statuses, live: {divergent[:10]}"
    assert all(lbl.split(":")[0] not in w.TERMINAL_STATES for lbl in live.values())
    print(f"    (live: {len(live)} open tickets, one label each across dashboard + map)")


def test_live_akienupdate_reports_agree():
    """The three files `akienupdate` writes — the exact text Akien reads. Every id on
    more than one of them wears one label."""
    w = _world()
    files = [w.COMMONS_ROOT / n for n in ("AkienInbox.txt", "AkienDashboard.txt", "AkienHMMap.txt")]
    missing = [str(f) for f in files if not f.is_file()]
    assert not missing, f"akienupdate has not written: {missing}"
    per_file = [_rows(f.read_text(encoding="utf-8")) for f in files]
    seen: dict[str, set[str]] = {}
    for rows in per_file:
        for tid, label in rows.items():
            seen.setdefault(tid, set()).add(label)
    shared = [tid for tid in seen if sum(tid in r for r in per_file) >= 2]
    assert shared, "no ticket appears on two of the three reports — nothing to compare (hollow)"
    divergent = {tid: sorted(labels) for tid, labels in seen.items() if len(labels) != 1}
    assert not divergent, f"one ticket, two statuses in Akien's reports: {divergent}"
    print(f"    (akienupdate: {len(shared)} ids on 2+ reports, all agree)")


# --- clauses (3), (4), (5): the source, the live map, the live corpus -----------

def test_source_one_label_deriving_function_no_private_cursor_regex():
    """(3) over the four readers: exactly one function derives a label from a cursor, and it
    is the inbox's; the cursor is parsed only through transitions.parse_workflow; no private
    cursor regex (a pattern that knows the bracket, the -ME suffix or the :phase) anywhere
    among them."""
    import ast
    derivers: list[str] = []
    parsers: list[str] = []
    private_regex: list[str] = []
    cursor_shape = re.compile(r"\\\[|ME\b|:\(|\[A-Z\]\[A-Z_\]|waiting|PROVED|BUILDME")
    for rel in _READERS:
        src = (_REPO_ROOT / rel).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ("status_label", "cursor_of"):
                derivers.append(f"{rel}::{node.name}")
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if name == "parse_workflow":
                    parsers.append(f"{rel}:{node.lineno}")
                if isinstance(fn, ast.Attribute) and getattr(fn.value, "id", "") == "re" \
                        and fn.attr in ("compile", "match", "search", "findall", "fullmatch"):
                    pat = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else ""
                    if isinstance(pat, str) and cursor_shape.search(pat):
                        private_regex.append(f"{rel}:{node.lineno} {pat!r}")
    assert derivers == ["cairn/tools/operator_inbox/inbox.py::cursor_of",
                        "cairn/tools/operator_inbox/inbox.py::status_label"], (
        f"the label is derived in ONE place, the inbox: {derivers}")
    assert parsers and all(p.startswith("cairn/tools/operator_inbox/inbox.py:") for p in parsers), (
        f"the cursor is parsed only by the inbox's reader (through transitions.parse_workflow): {parsers}")
    assert not private_regex, f"a private cursor regex outside transitions.parse_workflow: {private_regex}"
    # the other three readers reach the label only by importing it from the inbox
    for rel in _READERS[1:]:
        assert "operator_inbox" in (_REPO_ROOT / rel).read_text(encoding="utf-8"), \
            f"{rel} does not read through the inbox"


def test_live_map_rows_carry_date_and_id_and_groups_are_stage_vocabulary():
    """(4) + (6) live: on the open map every row under a status group carries a date and a
    12-hex id; every status group name is a stage token of transitions' vocabulary (or the
    one loud UNPARSED); and every prose-standing component (measured from the map's FINDING lines) appears only as a FINDING line
    naming the prose, never as a berth or a status group."""
    w = _world()
    hmap = _live_map()
    head, _, rest = hmap.partition("OPEN — by status:")
    by_status, _, in_port = rest.partition("IN PORT — by component:")
    assert head.strip().startswith("Fleet:") and by_status.strip() and in_port.strip(), hmap[:400]
    bad_rows = [l for l in by_status.splitlines()
                if l.strip() and not _GROUP.match(l) and not _ROW.match(l)]
    assert not bad_rows, f"map rows without a date + ticket id: {bad_rows[:5]}"
    groups = _groups(by_status)
    assert groups, "the open map has no status groups — a green here would be hollow"
    stray = [g for g in groups if not (w.is_stage_token(g) or g == w.UNPARSED)]
    assert not stray, f"a status group outside transitions' stage vocabulary: {stray}"
    port_rows = [l for l in in_port.splitlines() if _ROW.match(l)]
    assert len(port_rows) == sum(groups.values()), (
        f"the in-port rows ({len(port_rows)}) are the open rows ({sum(groups.values())}) regrouped")
    # (6): the prose-standing components berth no group and no row on the map — the only
    # line naming them as a component is the finding that names the prose
    port_groups = _groups(in_port)
    for comp in _prose_standing(hmap):
        berthed = [g for g in port_groups if re.search(rf"(^|/){comp}$", g)]
        assert not berthed, f"{comp} berths a lane on the map instead of a finding line: {berthed}"
        named = [l for l in hmap.splitlines()
                 if re.search(rf"(devices|machines|tools)/{comp}\b", l)]
        for l in named:
            assert l.startswith("FINDING:") and "history standing is prose" in l, (
                f"{comp} appears on the map other than as a finding line: {l!r}")
    print(f"    (live map: {sum(groups.values())} rows, groups {list(groups)})")


def test_live_every_open_ticket_carries_owning_intention():
    """(5) live: every non-terminal ticket names its owning charter — the component lane
    berths nobody as 'unassigned'."""
    w = _world()
    records = w.read_tickets()["records"]
    assert records, "no live tickets — a green here would be hollow"
    unowned = [r["id"] for r in records if r["owning_component"] == "unassigned"]
    assert not unowned, f"open tickets naming no owning_intention: {unowned}"
    hmap = _live_map()
    in_port = hmap.partition("IN PORT — by component:")[2]
    assert "unassigned (" not in in_port, "the map still berths an unassigned lane"
    print(f"    (live: {len(records)} open tickets, every one owned)")


if __name__ == "__main__":
    checks = [
        test_fixture_one_label_per_id_across_all_three,
        test_fixture_headers_sum_with_no_other,
        test_source_one_label_deriving_function_no_private_cursor_regex,
        test_live_map_rows_carry_date_and_id_and_groups_are_stage_vocabulary,
        test_live_every_open_ticket_carries_owning_intention,
        test_live_one_label_per_id_across_the_three_reports,
        test_live_akienupdate_reports_agree,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — one reader, one label per ticket, on the inbox, the dashboard and the map")

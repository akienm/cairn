"""Proof that the codemother dashboard wears the one status label and the one idea/intention counts (ticket 0c6f774d9ad8).

Ruled 2026-09-06 (ticket 3feb201c84ea): a ticket has ONE status, and the inbox, the codemother
dashboard and the harbor map are venn diagrams of one reader, operator_inbox.read_tickets.
Ruled with 3ed960cc402e clause (5): the inbox and the dashboard print the same open-idea and
open-intention counts. Until this ticket the dashboard's half of both was measured from
operator_inbox's proofs, which imported codemother (RULE 1: a ticket's proofs measure only that
component), so the dashboard's teeth berth here with their owner.

    python3 cairn/devices/codemother/proofs/test_the_dashboard_wears_the_one_label.py   # exit 0 = green
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

PROVES = {"0c6f774d9ad8": {
    "1": "test_fixture_dashboard_rows_wear_the_reader_label",
    "2": "test_fixture_dashboard_groups_are_the_inbox_header",
    "3": "test_live_dashboard_rows_wear_the_reader_label",
    "4": "test_the_dashboard_prints_the_inbox_idea_and_intention_counts",
}}

_ROW = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([0-9a-f]{12})\s+(.*)$")
_GROUP = re.compile(r"^\s*(\S+) \((\d+)\):$")

_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> WATCHME(fx) -> PROVED"


def _wf(cursor: str) -> str:
    seat = cursor.split("(")[0].split(":")[0]
    stages = _WF.split(": ", 1)[1].split(" -> ")
    return "code-seam@v2: " + " -> ".join(
        f"[{cursor}]" if s.split("(")[0] == seat else s for s in stages)


FIXTURE_TICKETS = [
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
    ("aa0000000007", "prose-state", "2026-09-06", "waiting on akien", None),
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


def _stub_data(tickets_dir: Path) -> dict:
    """The inbox's data dict with every lane but tickets stubbed empty."""
    from cairn.tools.operator_inbox.inbox import read_tickets
    return {
        "troubles": {"live": [], "live_count": 0, "total_count": 0},
        "email": {"count": 0},
        "adjudications": {"findings": [], "count": 0},
        "lap": {"items": [], "count": 0, "error": None},
        "questions": {"open": [], "count": 0},
        "design": {},
        "tickets": read_tickets(tickets_dir=tickets_dir),
        "intentions": {"count": 0, "items": []},
        "ideas": {"count": 0, "items": []},
    }


def _dash(tickets_dir: Path) -> str:
    from cairn.devices.codemother.dashboard import format_dashboard
    return format_dashboard(_stub_data(tickets_dir), tickets_dir=tickets_dir)


def _rows(text: str) -> dict[str, str]:
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


def _labels(tickets_dir: Path | None = None) -> dict[str, str]:
    from cairn.tools.operator_inbox.inbox import read_tickets
    kw = {"tickets_dir": tickets_dir} if tickets_dir is not None else {}
    return {r["id"]: r["label"] for r in read_tickets(**kw)["records"]}


def _header(tickets_dir: Path) -> dict[str, int]:
    """The inbox header's '(LABEL n, LABEL n)' — the reader's own count and order."""
    from cairn.tools.operator_inbox.inbox import format_summary
    summary = format_summary(_stub_data(tickets_dir))
    assert "other" not in summary.lower(), summary
    m = re.search(r"tickets \(([^)]*)\)", summary)
    assert m, f"no ticket breakdown in the inbox summary: {summary!r}"
    return {p.rsplit(" ", 1)[0]: int(p.rsplit(" ", 1)[1]) for p in m.group(1).split(", ")}


def test_fixture_dashboard_rows_wear_the_reader_label():
    from cairn.tools.operator_inbox.inbox import UNPARSED
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, _ = _build_fixture(Path(td))
        dash = _dash(tickets_dir)
        rows, labels = _rows(dash), _labels(tickets_dir)
        assert set(rows) == _NON_TERMINAL == set(labels), (
            f"dashboard rows {sorted(rows)}, reader {sorted(labels)}")
        divergent = {tid: (rows[tid], labels[tid]) for tid in rows if rows[tid] != labels[tid]}
        assert not divergent, f"one ticket, two statuses (dashboard, reader): {divergent}"
        assert rows["aa0000000004"] == "WATCHME:waiting"
        assert rows["aa0000000005"] == "WATCHME"
        assert rows["aa0000000002"] == "TICKETME:waiting"
        assert rows["aa0000000007"] == UNPARSED, "a prose cursor is loud (Law 7), never hidden"
        assert "aa0000000006" not in rows, "a PROVED ticket is not an open one on the dashboard"
        assert "PROVED (1)" in dash, "the dashboard counts the done ticket under DONE"


def test_fixture_dashboard_groups_are_the_inbox_header():
    from cairn.tools.operator_inbox.inbox import UNPARSED
    with tempfile.TemporaryDirectory() as td:
        tickets_dir, _ = _build_fixture(Path(td))
        groups, header = _groups(_dash(tickets_dir)), _header(tickets_dir)
        assert groups == header, f"dashboard groups {groups} vs the inbox header {header}"
        assert list(groups) == list(header), "the dashboard's group order is not the reader's order"
        assert list(groups)[0] == "THINKME" and list(groups)[-1] == UNPARSED, list(groups)


def test_live_dashboard_rows_wear_the_reader_label():
    from cairn.devices.codemother.dashboard import format_dashboard
    labels = _labels()
    assert labels, "no live tickets — a green here would be hollow"
    rows = _rows(format_dashboard())
    assert set(rows) == set(labels), (
        f"dash-only {sorted(set(rows) - set(labels))[:5]}, reader-only {sorted(set(labels) - set(rows))[:5]}")
    divergent = {tid: (rows[tid], labels[tid]) for tid in rows if rows[tid] != labels[tid]}
    assert not divergent, f"one ticket, two statuses, live (dashboard, reader): {dict(list(divergent.items())[:10])}"
    print(f"    (live: {len(rows)} open tickets, the dashboard wears the reader's label on each)")


def test_the_dashboard_prints_the_inbox_idea_and_intention_counts():
    """3ed960cc402e clause (5), the dashboard's half: over the live commons the dashboard prints
    the open-idea and open-intention counts the inbox's reader gathers — agreement, never a
    snapshot of the number."""
    from cairn.devices.codemother.dashboard import format_dashboard
    from cairn.tools.operator_inbox.inbox import gather_all
    data = gather_all()
    dash = format_dashboard(data)

    def one(pattern):
        hits = re.findall(pattern, dash, re.M)
        assert len(hits) == 1, f"dashboard: expected one match for {pattern!r}, got {hits}"
        return int(hits[0])

    assert one(r"^  IDEAS: (\d+) open \(not yet at intent; \d+ moved on\)") == data["ideas"]["count"]
    assert one(r"^  INTENTIONS: (\d+) open \(no ticket yet; \d+ moved on\)") == data["intentions"]["count"]


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""render — the web presentation surface's HTML, from DATA. Pure, no I/O, no sockets.

The web server is a PRESENTATION surface (Law 7): it may render an error into a coherent
shape, but it holds no record of truth and produces no DATA of its own. Everything here is a
pure function ``data -> html`` — the DATA comes from the shims (``active_page``, web-server
child a) and the heartbeat (``roster``, child c); this module only renders it. That split is
what keeps the intelligence in the devices and the web server trivial (one owner, no state).

TWO Law-7 disciplines live here, as physics:
  - EVERYTHING A DEVICE SAYS IS ESCAPED. A device's reported state could contain ``<script>``
    (a bug, or a hostile string in some future feed); the surface renders it as TEXT, never as
    live markup. ``html.escape`` on every device-derived value — a presentation surface that let
    a device's data become markup would be lying about what the device said.
  - AN ABSENT PANE RENDERS ITS REASON, loudly (the ``absent`` field child a produced). The
    surface collapses nothing into silence; a pane that could not be built says so.

v0 renders each pane's DATA as pretty JSON in a ``<pre>`` — honest and complete for
introspection. Interaction panes bringing their own rich view is a filed edge (child a's
declared-panes shape already carries what such a view would need).

No framework, no JS, no external asset (Law: self-contained). One small inline stylesheet.
"""

from __future__ import annotations

import html
import json


def _esc(value) -> str:
    """Escape any device-derived value to TEXT. A dict/list is shown as pretty JSON (itself
    escaped); a scalar is stringified and escaped. Nothing a device said becomes live markup."""
    if isinstance(value, (dict, list)):
        return html.escape(json.dumps(value, indent=2, sort_keys=False, default=str))
    return html.escape(str(value))


def render_nav(roster: dict, selected: str | None = None, *, harbor: bool = False) -> str:
    """The nav across the top — one entry per device the heartbeat beats to (child c's roster),
    in order, each a link to its ACTIVE page, marked awake/asleep, the selected one flagged. An
    empty roster is an honest empty nav, not a broken page. With ``harbor`` set, a leading link to
    the harbour master's TRAFFIC IMAGE (``/harbor``, web-server child d) rides on every page — the
    fleet-wide view is reachable from anywhere, distinct from the per-device pages. (There is no
    special chat entry: the librarian rides the roster like any device — ONE web server, and every
    device's surfaces live on its own page.)"""
    beats = _esc(roster.get("beats", 0))
    items = []
    if harbor:
        hcls = "dev harbor" + (" selected" if selected == "harbor" else "")
        items.append(f'<a class="{hcls}" href="/harbor" title="the traffic image">⚓ Harbor</a>')
    for entry in roster.get("devices", []):
        device = entry.get("device", "?")
        awake = entry.get("awake", False)
        cls = "dev" + (" selected" if device == selected else "")
        dot = "●" if awake else "○"  # awake ● / asleep ○ — live wakefulness in the nav
        state = "awake" if awake else "asleep"
        items.append(
            f'<a class="{cls}" href="/device/{html.escape(str(device))}" '
            f'title="{state}"><span class="dot">{dot}</span> {_esc(device)}</a>'
        )
    nav = "".join(items) or '<span class="empty">no devices on the heartbeat yet</span>'
    return f'<nav><span class="beats" title="heartbeats">♥ {beats}</span>{nav}</nav>'


def render_traffic_image(img: dict) -> str:
    """The harbour master's TRAFFIC IMAGE as HTML (web-server child d) — the whole-fleet view,
    state-right-now, from the DATA harbor_master.voyage produces. Pure ``data -> html``; the web
    server owns nothing (Law 7), it renders the harbor's projection.

    Calm when healthy (held-traffic-image): each EMERGENT GATE shows its ``underway`` as a COUNT
    (the calm number) and its ``flagged`` boats as LINES you can read — a marker + the boat's id.
    Every boat-derived string is escaped (Law 7: a ticket id on disk is untrusted here too). An
    empty fleet renders an honest empty image, not a broken page."""
    c = img.get("counts", {})
    header = (f'<p class="tallies">{_esc(c.get("at_sea", 0))} at sea across '
              f'{_esc(c.get("gates", 0))} gates · <strong>{_esc(c.get("flagged", 0))} flagged</strong> · '
              f'{_esc(c.get("berthed", 0))} berthed</p>')

    rows = []
    for g in img.get("gates", []):
        gate = _esc(g.get("gate", "?"))
        underway = _esc(g.get("underway", 0))
        flagged = g.get("flagged", [])
        flags = "".join(
            f'<li><span class="marker">{_esc(o.get("marker", ""))}</span> {_esc(o.get("id", "?"))}'
            f' <span class="cond">{_esc(o.get("condition", ""))}</span></li>'
            for o in flagged
        )
        flags_html = f'<ul class="flagged">{flags}</ul>' if flagged else ""
        cls = "gate" + (" has-flags" if flagged else "")
        rows.append(
            f'<div class="{cls}"><div class="gate-head"><span class="gate-name">{gate}</span>'
            f'<span class="underway">{underway} underway</span>'
            f'<span class="flag-count">{_esc(len(flagged))} flagged</span></div>{flags_html}</div>'
        )
    gates_html = "".join(rows) or '<p class="empty">no boats at sea</p>'

    berthed = img.get("berthed", [])
    berthed_names = ", ".join(_esc(b.get("id", "?")) for b in berthed) or "none"
    berthed_html = (f'<section class="berthed"><h2>Berthed '
                   f'<span class="count">({_esc(len(berthed))})</span></h2>'
                   f'<p class="quiet">{berthed_names}</p></section>')

    return (f'<div class="active harbor-view"><h1>⚓ Traffic Image</h1>{header}'
            f'<section class="gates">{gates_html}</section>{berthed_html}</div>')


def _render_chat_reply(kind: str, reply: dict) -> str:
    """One chat turn's reply as HTML, by kind — the device's DATA rendered, never touched.
    A resolve reply is PROSE first (the walk articulated — the librarian CHATS), its
    code-built citations legible, and the loop's verdict COLLAPSED to one secondary
    line (Law 7: the surface may collapse; the turn record upstream keeps the verdict
    whole); a summarize reply is the cited prose with its code-built citations and its
    depth; a refusal renders LOUDLY as the reply it honestly is. Everything the device
    said is escaped, like any device."""
    if kind == "refused":
        return f'<p class="refused">refused — {_esc(reply.get("refusal"))}</p>'
    if kind == "summarize":
        cites = "".join(
            f'<li>[{_esc(c.get("n"))}] {_esc(c.get("node_id"))} '
            f'<span class="cond">{_esc(c.get("source"))} · '
            f'sim {_esc(round(c.get("similarity", 0), 4))}</span></li>'
            for c in reply.get("citations", []))
        d = reply.get("depth", {})
        return (f'<p class="prose">{_esc(reply.get("summary"))}</p>'
                f'<ul class="citations">{cites}</ul>'
                f'<p class="depth">reached {_esc(d.get("region"))} of '
                f'{_esc(d.get("tree_nodes"))} nodes · region {_esc(d.get("region_digest"))}'
                f'{" · already landed" if reply.get("duplicate") else ""}</p>')
    cites = "".join(
        f'<li>[{_esc(c.get("n"))}] {_esc(c.get("node_id"))} '
        f'<span class="cond">{_esc(c.get("source"))} · '
        f'sim {_esc(round(c.get("similarity", 0), 4))}</span></li>'
        for c in reply.get("citations", []))
    loop = reply.get("loop") or {}
    verdict = loop.get("verdict", "?")
    cond = (f'<p class="cond">{_esc(verdict)}'
            f'{" (" + _esc(loop.get("reason")) + ")" if loop.get("reason") else ""} · '
            f'best {_esc(round(loop["best"], 4) if loop.get("best") is not None else None)} · '
            f'floor {_esc(loop.get("floor"))} · {_esc(loop.get("backfills", 0))} backfills · '
            f'{_esc(len(loop.get("deposited", [])))} nodes folded in</p>')
    return (f'<p class="prose">{_esc(reply.get("prose"))}</p>'
            + (f'<ul class="citations">{cites}</ul>' if cites else "")
            + cond)


def _render_chat_pane(pane: dict) -> str:
    """The CHAT pane — the first interaction pane with its own rich view (the generic
    renderer shows DATA as pretty JSON; a conversation earns a transcript + form). The
    pane's DATA is the session's page (``{"tree", "turns"}``); the form POSTs back to
    the device's own page (``action=""`` — the current URL) with a hidden ``channel``
    field naming the device's mail channel, and the ``summarize:`` affordance is SAID
    on the surface, not memorized. Pure data -> html; the surface owns nothing."""
    data = pane.get("data") or {}
    turns = []
    for t in data.get("turns", []):
        kind = str(t.get("kind", "?"))
        turns.append(
            f'<section class="turn"><p class="utterance">{_esc(t.get("utterance"))}</p>'
            f'{_render_chat_reply(kind, t.get("reply") or {})}</section>')
    transcript = "".join(turns) or \
        '<p class="empty">nothing said yet — the graph is listening.</p>'
    form = (
        '<form class="ask" method="post" action="">'
        '<input type="hidden" name="channel" value="chat">'
        '<input type="text" name="utterance" autofocus autocomplete="off" '
        'placeholder="ask — or start with &quot;summarize:&quot; for cited prose">'
        '<button type="submit">send</button></form>')
    label = _esc(pane.get("label", "Chat"))
    tree = _esc(data.get("tree", "?"))
    return (f'<section class="pane chat" data-kind="chat"><h2>{label} '
            f'<span class="count">tree: {tree}</span></h2>'
            f'<div class="transcript">{transcript}</div>{form}</section>')


def _render_record(data) -> str:
    """A record — key-value pairs as a definition list. The data is a dict."""
    if not isinstance(data, dict):
        return f'<pre>{_esc(data)}</pre>'
    items = "".join(f'<dt>{_esc(k)}</dt><dd>{_esc(v)}</dd>' for k, v in data.items())
    return f'<dl class="record">{items}</dl>'


def _render_table(data) -> str:
    """A table — a list of dicts as an HTML table. Columns from the union of all keys."""
    if not isinstance(data, list) or not data:
        return f'<pre>{_esc(data)}</pre>'
    cols = []
    seen = set()
    for row in data:
        if isinstance(row, dict):
            for k in row:
                if k not in seen:
                    cols.append(k)
                    seen.add(k)
    if not cols:
        return f'<pre>{_esc(data)}</pre>'
    header = "".join(f'<th>{_esc(c)}</th>' for c in cols)
    rows = []
    for row in data:
        if isinstance(row, dict):
            cells = "".join(f'<td>{_esc(row.get(c, ""))}</td>' for c in cols)
        else:
            cells = f'<td colspan="{len(cols)}">{_esc(row)}</td>'
        rows.append(f'<tr>{cells}</tr>')
    return f'<table><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _render_sequence(data) -> str:
    """A sequence — a list rendered as an ordered list."""
    if not isinstance(data, list):
        return f'<pre>{_esc(data)}</pre>'
    items = "".join(f'<li>{_esc(item)}</li>' for item in data)
    return f'<ol class="sequence">{items}</ol>'


def _render_tree(data, *, _depth: int = 0) -> str:
    """A tree — nested dicts/lists as collapsible details/summary elements."""
    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            inner = _render_tree(v, _depth=_depth + 1)
            if isinstance(v, (dict, list)) and v:
                parts.append(
                    f'<details{"" if _depth > 0 else " open"}>'
                    f'<summary>{_esc(k)}</summary>{inner}</details>')
            else:
                parts.append(f'<div class="leaf"><span class="key">{_esc(k)}</span>: '
                             f'<span class="val">{_esc(v)}</span></div>')
        return "".join(parts)
    if isinstance(data, list):
        items = "".join(f'<li>{_render_tree(item, _depth=_depth + 1)}</li>' for item in data)
        return f'<ol class="tree-list">{items}</ol>'
    return f'<span class="val">{_esc(data)}</span>'


def _render_scalar(data) -> str:
    """A scalar — a single value rendered inline."""
    return f'<span class="scalar">{_esc(data)}</span>'


_VIEW_DISPATCH: dict[str, object] = {
    "record": _render_record,
    "table": _render_table,
    "sequence": _render_sequence,
    "tree": _render_tree,
    "scalar": _render_scalar,
    "chat": None,
}


def _render_pager(pane: dict, base_path: str) -> str:
    """Prev/next anchors when a pane is bounded (count > len(window))."""
    count = pane.get("count")
    window = pane.get("window")
    cursor = pane.get("cursor")
    if count is None or window is None:
        return ""
    window_len = len(window) if isinstance(window, list) else 0
    if count <= window_len:
        return ""
    links = []
    if cursor is not None and cursor > 0:
        prev_cursor = max(0, cursor - window_len)
        links.append(f'<a class="pager-prev" href="{_esc(base_path)}?cursor={prev_cursor}">&larr; prev</a>')
    if cursor is not None and cursor + window_len < count:
        next_cursor = cursor + window_len
        links.append(f'<a class="pager-next" href="{_esc(base_path)}?cursor={next_cursor}">next &rarr;</a>')
    elif cursor is None and window_len < count:
        links.append(f'<a class="pager-next" href="{_esc(base_path)}?cursor={window_len}">next &rarr;</a>')
    if not links:
        return ""
    return f'<nav class="pager">{" ".join(links)}</nav>'


def _render_window_meta(pane: dict) -> str:
    """'showing N of M' annotation when a pane carries bounded-read metadata."""
    count = pane.get("count")
    window = pane.get("window")
    if count is None or window is None:
        return ""
    window_len = len(window) if isinstance(window, list) else 0
    if count <= window_len:
        return ""
    return f'<p class="window-meta">showing {_esc(window_len)} of {_esc(count)}</p>'


def render_pane(pane: dict, *, base_path: str = "") -> str:
    """One pane of a device's ACTIVE page: its label, then its DATA — or, if it could not be
    built, its ABSENT reason (loud, never silent; child a produced the reason). Dispatches on
    the declared kind: record, table, sequence, tree, scalar each have a dedicated renderer;
    chat has its own rich view; an unknown kind falls back to <pre> with pretty JSON."""
    label = _esc(pane.get("label", pane.get("kind", "pane")))
    kind = _esc(pane.get("kind", ""))
    if pane.get("absent"):
        return (f'<section class="pane absent" data-kind="{kind}">'
                f'<h2>{label}</h2><p class="reason">absent — {_esc(pane["absent"])}</p></section>')
    if pane.get("kind") == "chat":
        return _render_chat_pane(pane)
    renderer = _VIEW_DISPATCH.get(pane.get("kind", ""))
    data = pane.get("data")
    window_meta = _render_window_meta(pane)
    pager = _render_pager(pane, base_path)
    if renderer is not None:
        body = renderer(pane.get("window", data) if pane.get("window") is not None else data)
    else:
        body = f'<pre>{_esc(data)}</pre>'
    return (f'<section class="pane" data-kind="{kind}">'
            f'<h2>{label}</h2>{window_meta}{body}{pager}</section>')


def render_active_page(page: dict, *, trouble: str | None = None,
                       base_path: str = "") -> str:
    """A device's ACTIVE page — the pane stack (child a's assembled DATA), in order. A
    ``trouble`` (a POSTed delivery that died) renders loudly ABOVE the still-intact page
    (Law 7: the surface collapses the error into a legible shape, never into silence)."""
    device = _esc(page.get("device", "?"))
    trouble_html = f'<p class="refused">{_esc(trouble)}</p>' if trouble else ""
    panes = "".join(render_pane(p, base_path=base_path) for p in page.get("panes", []))
    return f'<div class="active"><h1>{device}</h1>{trouble_html}{panes}</div>'


def render_message(title: str, body: str) -> str:
    """A coherent shape for a non-page response (a 404, a landing) — the surface never shows a
    raw stack; it collapses the condition into a legible message (Law 7)."""
    return f'<div class="active"><h1>{html.escape(title)}</h1><p>{html.escape(body)}</p></div>'


_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.5 system-ui, sans-serif; }
nav { display: flex; gap: .25rem; align-items: center; flex-wrap: wrap;
      padding: .5rem .75rem; border-bottom: 1px solid #8884; position: sticky; top: 0;
      background: Canvas; }
nav .beats { margin-right: .5rem; opacity: .7; }
nav a.dev { text-decoration: none; padding: .2rem .55rem; border-radius: .4rem;
            border: 1px solid #8884; color: inherit; }
nav a.dev.selected { border-color: #6a9; font-weight: 600; }
nav a.dev .dot { opacity: .8; }
nav .empty { opacity: .6; }
main { padding: 1rem 1.25rem; max-width: 60rem; }
.active h1 { margin: .2rem 0 1rem; }
.pane { border: 1px solid #8884; border-radius: .5rem; margin: 0 0 1rem; padding: .5rem .9rem; }
.pane h2 { font-size: .95rem; margin: .3rem 0; text-transform: capitalize; }
.pane pre { margin: 0; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
.pane.absent .reason { opacity: .7; font-style: italic; }
nav a.dev.harbor { border-color: #a86; }
.harbor-view .tallies { opacity: .8; margin: .2rem 0 1rem; }
.harbor-view .gates { display: flex; flex-direction: column; gap: .5rem; }
.gate { border: 1px solid #8884; border-radius: .5rem; padding: .4rem .8rem; }
.gate.has-flags { border-color: #a86; }
.gate-head { display: flex; gap: .75rem; align-items: baseline; }
.gate-head .gate-name { font-weight: 600; min-width: 7rem; }
.gate-head .underway { opacity: .7; }
.gate-head .flag-count { margin-left: auto; opacity: .7; font-size: .9rem; }
.gate .flagged { list-style: none; margin: .35rem 0 0; padding: 0; }
.gate .flagged li { padding: .1rem 0; }
.gate .flagged .marker { font-family: ui-monospace, monospace; opacity: .9; }
.gate .flagged .cond { opacity: .6; font-size: .85rem; }
.berthed { margin-top: 1rem; }
.berthed h2 { font-size: .95rem; margin: .3rem 0; }
.berthed .count { opacity: .6; font-weight: 400; }
.berthed .quiet { opacity: .6; margin: .2rem 0; }
.pane.chat .count { opacity: .6; font-weight: 400; font-size: .9rem; }
.pane.chat .transcript { display: flex; flex-direction: column; gap: .6rem; }
.pane.chat .turn { border: 1px solid #8884; border-radius: .5rem; padding: .4rem .8rem; }
.pane.chat .utterance { font-weight: 600; margin: .3rem 0; }
.pane.chat .verdict { opacity: .8; margin: .2rem 0; }
.pane.chat .walk { margin: .3rem 0; padding-left: 1.4rem; }
.pane.chat .walk .sim { font-family: ui-monospace, monospace; opacity: .8; }
.pane.chat .cond { opacity: .6; font-size: .85rem; }
.pane.chat .prose { margin: .3rem 0; }
.pane.chat .citations { list-style: none; margin: .3rem 0; padding: 0;
                        font-family: ui-monospace, monospace; font-size: .85rem; }
.pane.chat .depth { opacity: .6; font-size: .85rem; margin: .2rem 0; }
.refused { color: #b55; margin: .3rem 0; }
.pane dl.record { margin: .3rem 0; display: grid; grid-template-columns: auto 1fr; gap: .1rem .8rem; }
.pane dl.record dt { font-weight: 600; opacity: .8; }
.pane dl.record dd { margin: 0; }
.pane table { width: 100%; border-collapse: collapse; margin: .3rem 0; font-size: .9rem; }
.pane table th, .pane table td { text-align: left; padding: .25rem .5rem; border: 1px solid #8884; }
.pane table th { font-weight: 600; opacity: .8; }
.pane ol.sequence { margin: .3rem 0; padding-left: 1.5rem; }
.pane details { margin: .2rem 0; }
.pane details summary { cursor: pointer; font-weight: 600; opacity: .9; }
.pane .leaf { margin: .1rem 0 .1rem .8rem; }
.pane .leaf .key { font-weight: 600; opacity: .8; }
.pane .scalar { font-size: 1.1rem; }
.window-meta { opacity: .7; font-size: .85rem; margin: .2rem 0; }
.pager { display: flex; gap: 1rem; margin: .5rem 0 .2rem; }
.pager a { text-decoration: none; padding: .2rem .6rem; border: 1px solid #8884;
           border-radius: .4rem; color: inherit; }
.pane.chat .ask { display: flex; gap: .5rem; margin-top: 1rem; }
.pane.chat .ask input { flex: 1; padding: .45rem .7rem; border: 1px solid #8884;
                        border-radius: .4rem; font: inherit; background: Canvas; color: inherit; }
.pane.chat .ask button { padding: .45rem .9rem; border: 1px solid #8884;
                         border-radius: .4rem; font: inherit; background: Canvas;
                         color: inherit; cursor: pointer; }
"""


def render_document(*, title: str, nav_html: str, body_html: str) -> str:
    """The whole page — self-contained (Law: no external asset), no JS, one inline stylesheet.
    The nav (roster) across the top, the selected device's ACTIVE page below."""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body>{nav_html}<main>{body_html}</main></body></html>"
    )

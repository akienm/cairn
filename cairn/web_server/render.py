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


def render_nav(roster: dict, selected: str | None = None) -> str:
    """The nav across the top — one entry per device the heartbeat beats to (child c's roster),
    in order, each a link to its ACTIVE page, marked awake/asleep, the selected one flagged. An
    empty roster is an honest empty nav, not a broken page."""
    beats = _esc(roster.get("beats", 0))
    items = []
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


def render_pane(pane: dict) -> str:
    """One pane of a device's ACTIVE page: its label, then its DATA — or, if it could not be
    built, its ABSENT reason (loud, never silent; child a produced the reason)."""
    label = _esc(pane.get("label", pane.get("kind", "pane")))
    kind = _esc(pane.get("kind", ""))
    if pane.get("absent"):
        return (f'<section class="pane absent" data-kind="{kind}">'
                f'<h2>{label}</h2><p class="reason">absent — {_esc(pane["absent"])}</p></section>')
    return (f'<section class="pane" data-kind="{kind}">'
            f'<h2>{label}</h2><pre>{_esc(pane.get("data"))}</pre></section>')


def render_active_page(page: dict) -> str:
    """A device's ACTIVE page — the pane stack (child a's assembled DATA), in order."""
    device = _esc(page.get("device", "?"))
    panes = "".join(render_pane(p) for p in page.get("panes", []))
    return f'<div class="active"><h1>{device}</h1>{panes}</div>'


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

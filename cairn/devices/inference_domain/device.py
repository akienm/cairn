"""inference_domain/device.py — the inference domain as a device.

The inference domain's machinery (domain.py, host.py, route.py) predates its device
class. This wraps the module behind a BaseDevice face so the domain can be addressed
on the bus — the SOLE path for inter-device inference (ticket 87a7f1c7ae21).

The ``resolve`` verb is the bus-addressable face of ``domain.resolve``: a caller posts
a request (kind, prompt/messages, model), the handler builds the resolver, runs the
domain workflow, and returns the result. The shim posts the reply — the device never
touches the bus.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


def _with_kind(envelope: dict, kind: str) -> dict:
    """The same envelope with the request's ``kind`` fixed — the verb decides the kind, a
    caller's own ``kind`` key is overridden rather than argued with (``embed`` means embed)."""
    body = dict(envelope.get("body") or {})
    body["kind"] = kind
    return {**envelope, "body": body}


def _json_safe(value):
    """A row as something json.dumps takes: datetimes to ISO strings, Decimal to float."""
    from datetime import date, datetime
    from decimal import Decimal
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


class InferenceDomainDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "inference_domain"
        from cairn.devices.inference_domain.domain import _trail
        self.debug_sink = _trail

    @property
    def device_id(self) -> str:
        return self._device_id

    def declared_verbs(self) -> dict:
        # ``embed`` and ``infer`` are the two named asks (ticket 87a7f1c7ae21, chart
        # decompose-20260906T111035): each is ``resolve`` with the kind fixed, so a device
        # that wants a vector or a completion asks for THAT over the bus and never needs the
        # domain's request vocabulary — or its module — to ask.
        return {**super().declared_verbs(), "resolve": self._handle_resolve,
                "embed": self._handle_embed, "infer": self._handle_infer,
                "calls": self._handle_calls}

    def _handle_calls(self, envelope: dict, *, table: str | None = None) -> dict:
        """Who asks for the domain's calls gets them (ticket b905340f8162): stored
        inference_calls rows, most recent first, bounded by ``limit`` (default 100, capped
        at 1000) and ``since`` (ISO; rows created at or before it are dropped). A verb, not a
        view, because a view takes no arguments. The domain does not know who asks or why.
        ``table`` is a proof seam for a scratch table; the bus never passes it."""
        from cairn.devices.inference_domain import domain

        body = envelope.get("body") or {}
        limit = max(1, min(int(body.get("limit") or 100), 1000))
        kw = {"table": table} if table else {}
        rows = domain.read_ticket(limit=limit, since=body.get("since"), **kw)
        return {"calls": [_json_safe(r) for r in rows]}

    def _handle_embed(self, envelope: dict) -> dict:
        return self._handle_resolve(_with_kind(envelope, "embed"))

    def _handle_infer(self, envelope: dict) -> dict:
        return self._handle_resolve(_with_kind(envelope, "generate"))

    def declared_views(self) -> dict:
        return {"yield": self._yield_view, "models": self._models_view,
                "calls": self._calls_view}

    def _calls_view(self, limit=None, since=None) -> dict:
        """The calls as a view (ticket f09c594cf6d8): ``cairn inference_domain show calls
        --limit 20`` for a human, ``get calls`` for JSON. Delegates to the ``calls`` verb's own
        handler, so the bound (default 100, capped at 1000) and ``since`` are the verb's; the
        verb stays, because the librarian asks for the calls over the bus."""
        return self._handle_calls({"body": {"limit": limit, "since": since}})

    def _render_view(self, name: str, data: dict) -> str:
        """``calls`` is one line per call, newest first: created to the second, verdict, cost,
        and the canonical request cut to 80 characters; then ``N calls``. Every other view
        renders as the base renders it."""
        if name != "calls":
            return super()._render_view(name, data)
        rows = data.get("calls") or []
        lines = []
        for r in rows:
            created = str(r.get("created") or "")[:19].replace("T", " ")
            lines.append(f"{created}  {str(r.get('verdict') or ''):<7} "
                         f"{str(r.get('cost') if r.get('cost') is not None else ''):>8}  "
                         f"{str(r.get('canonical') or '')[:80]}")
        lines.append(f"{len(rows)} calls")
        return "\n".join(lines)

    def _handle_resolve(self, envelope: dict) -> dict:
        from cairn.devices.inference_domain import domain, host

        body = envelope.get("body", {})
        model = body.get("model")
        if not model:
            # THE DEFAULT IS DATA, PER KIND (ticket 959bb65192a1): until 2026-10-14 every kind
            # defaulted to the embed model here, so a model-less generate was refused as if
            # the route had failed. A kind with no declared default is refused by name BEFORE
            # any resolver is built; the request itself is left as asked (it is the cache key).
            from cairn.devices.inference_domain.machines.route.route import kind_default
            kind = body.get("kind", "generate")      # the domain's own reading of a kindless ask
            try:
                model = kind_default(kind)
            except Exception as refusal:
                return {"outcome": "refused", "refused": type(refusal).__name__,
                        "detail": str(refusal)[:2000], "ticket": None, "model": None,
                        "hit": False, "answer": None}
        temperature = body.get("temperature", 0.0)
        resolver = host.ollama_resolver(model=model, temperature=temperature)

        # THE WHITELIST IS THE REQUEST, so a key missing from it is a question silently
        # rewritten. `tools` was missing until 2026-09-11 (ticket 548dd13fb4db): host.py sent
        # the toolset on /api/chat, canonicalize() digested it and the cache forked on it —
        # and none of that was reachable from the bus, because the key never entered the
        # request here. A caller posting a tool-using conversation over the one door got a
        # coherent toolless answer and no error anywhere, which is exactly the collapse Law 7
        # forbids a door to make. Held as a whitelist rather than opened to the whole body on
        # purpose: the request IS the cache key, so an unfiltered copy lets any stray body key
        # fork the store for every caller.
        request = {k: v for k, v in body.items()
                   if k in ("kind", "prompt", "messages", "model", "domain", "options",
                            "tools")}
        # THE CALLER RIDES THE ENVELOPE (ticket ea4a6151300f): the bus stamps ``sender`` on
        # every envelope, so over this door the asker's identity is measured off the message,
        # not guessed off a call stack that ends in the shim. An envelope with no sender is
        # passed through as None and the domain records ``unknown`` — a measurement that
        # found nothing, never a blank.
        caller = envelope.get("sender") or None
        try:
            result = domain.resolve(request, resolver=resolver, sink=self.debug_sink,
                                    caller=caller)
        except Exception as refusal:
            # A REFUSAL COMES BACK AS A VALUE, NOT A CRASH. The domain already wrote the
            # task ticket and raised the trouble; what the bus caller needs is an
            # intelligible answer they can act on — which host said no, why, and where the
            # ticket is — rather than a traceback folded into the reply channel (Law 7:
            # loud, and permanent in the ticket; this face may shape it, never hide it).
            ticket = getattr(refusal, "task_ticket", None)
            self.debug_sink.emit("resolve",
                                 pointer=body.get("kind", ""),
                                 values={"hit": False, "model": model,
                                         "outcome": "refused",
                                         "refused": type(refusal).__name__})
            return {"outcome": "refused", "refused": type(refusal).__name__,
                    "detail": str(refusal)[:2000], "ticket": ticket, "model": model,
                    "hit": False, "answer": None}
        self.debug_sink.emit("resolve",
                             pointer=body.get("kind", ""),
                             values={"hit": result.get("hit", False),
                                     "model": model,
                                     "outcome": "answered",
                                     "ticket": result.get("ticket")})
        return result

    def _yield_view(self) -> dict:
        from cairn.devices.inference_domain import domain
        return domain.yield_report()

    def _models_view(self) -> dict:
        """The parsed models stack — the owner's declaration of what it will answer for.

        A consumer (aider_shim first, ticket 50ad391f4e95) sizes its model table off this
        instead of reading ``machines/route/stacks/models.json`` out of this device's tree.
        """
        from cairn.devices.inference_domain.machines.route.route import load_stacks
        return load_stacks()["models"]

    def intention(self) -> dict:
        return {
            "what": "The one path to the inference host, and the compile-once gate.",
            "why": "A resource with exactly one owner, reached only through the "
                    "owner's gate (Law 6 + Law 4). The cache is the point: an answered "
                    "question becomes structure (Law 1).",
        }

    def state(self) -> dict:
        from cairn.devices.inference_domain import domain
        try:
            report = domain.yield_report()
            return {
                "spent": report.get("spent", 0),
                "avoided": report.get("avoided", 0),
                "hit_rate": report.get("hit_rate"),
            }
        except Exception:
            return {}

    def settings(self) -> dict:
        return {}

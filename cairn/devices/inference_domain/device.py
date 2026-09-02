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


class InferenceDomainDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "inference_domain"

    @property
    def device_id(self) -> str:
        return self._device_id

    def declared_verbs(self) -> dict:
        return {**super().declared_verbs(), "resolve": self._handle_resolve}

    def declared_views(self) -> dict:
        return {"yield": self._yield_view}

    def _handle_resolve(self, envelope: dict) -> dict:
        from cairn.devices.inference_domain import domain, host

        body = envelope.get("body", {})
        model = body.get("model", "nomic-embed-text")
        temperature = body.get("temperature", 0.0)
        resolver = host.ollama_resolver(model=model, temperature=temperature)

        request = {k: v for k, v in body.items()
                   if k in ("kind", "prompt", "messages", "model", "domain", "options")}
        return domain.resolve(request, resolver=resolver)

    def _yield_view(self) -> dict:
        from cairn.devices.inference_domain import domain
        return domain.yield_report()

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

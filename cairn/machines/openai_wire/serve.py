"""The OpenAI-shaped HTTP face, with its answerers INJECTED. This module knows
two routes and nothing about who answers them: a holder hands make_handler a
`resolve` and a `models`, gets a handler class back, and owns the listener that
make_server builds around it. The handler never dials anything itself — a
netns-isolated proof of it is a proof of the whole file.

  resolve(request) -> answer     request = {"model", "messages", "tools"?,
                                            "temperature"?} as they arrived on
                                            the wire (OpenAI-shaped; the holder
                                            calls translate.to_provider if its
                                            provider needs it). The answer is
                                            provider-shaped: {"text", "role",
                                            "tool_calls", "usage"?: {"prompt_tokens",
                                            "completion_tokens"}, "extra"?: dict}
                                            — "extra" is spliced into the envelope
                                            as "x_cairn" so a holder can carry
                                            its own facts (hit, canonical) without
                                            this module knowing them.
  models() -> iterable of str    the ids /v1/models lists.

What the wire is told, never faked (Law 7): a raising resolve is a 502 whose
message carries the exception's type and text; stream=true is a 400 naming the
gap; any other path is a 404 naming the path. Lifted from the measured source
CairnCommons/measurements/2026-09-11-hermes-openai-door-spike.py (ticket
76639374d9f9).
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cairn.machines.openai_wire import translate

STREAM_GAP = "stream=true is not served: the answerer behind this door speaks one whole answer"


def make_handler(*, resolve, models):
    """Build a handler class closed over the two injected callables."""

    class OpenAIWireHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):  # stderr is for real errors only
            pass

        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/models"):
                try:
                    names = list(models())
                except Exception as exc:
                    self._send(502, {"error": {"message": f"{type(exc).__name__}: {exc}",
                                               "type": "cairn_models_error"}})
                    return
                self._send(200, {"object": "list", "data": [
                    {"id": name, "object": "model", "owned_by": "cairn"} for name in names]})
            else:
                self._send(404, {"error": {"message": f"no route {self.path}", "type": "cairn_no_route"}})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n)
            try:
                req = json.loads(raw or b"{}")
            except Exception:
                self._send(400, {"error": {"message": "unparseable body", "type": "cairn_bad_request"}})
                return
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._send(404, {"error": {"message": f"no route {self.path}", "type": "cairn_no_route"}})
                return
            if not isinstance(req, dict) or not isinstance(req.get("messages"), list):
                self._send(400, {"error": {"message": "body needs a 'messages' list",
                                           "type": "cairn_bad_request"}})
                return
            if req.get("stream"):
                self._send(400, {"error": {"message": STREAM_GAP, "type": "cairn_stream_gap"}})
                return

            request = {"model": req.get("model"), "messages": req["messages"]}
            for key in ("tools", "temperature"):
                if req.get(key) is not None:
                    request[key] = req[key]
            try:
                answer = resolve(request)
            except Exception as exc:
                self._send(502, {"error": {"message": f"{type(exc).__name__}: {exc}",
                                           "type": "cairn_resolve_error"}})
                return
            if not isinstance(answer, dict):
                self._send(502, {"error": {"message": f"resolve returned {type(answer).__name__}, not a dict",
                                           "type": "cairn_resolve_error"}})
                return
            out = translate.completion(answer, req.get("model"), answer.get("usage"))
            if isinstance(answer.get("extra"), dict):
                out["x_cairn"] = answer["extra"]
            self._send(200, out)

    return OpenAIWireHandler


def make_server(handler, host="127.0.0.1", port=8899):
    """The listener a holder owns. Separate from make_handler so a proof can drive
    the handler with fake files and never bind a socket."""
    return ThreadingHTTPServer((host, port), handler)

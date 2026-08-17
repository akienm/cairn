"""The money-fence: the ask is narrow by name, and widening it is refused loudly.

WHY THIS IS AN OBJECT IN THIS DEVICE AND NOT A ROW IN THE PROXY. Until 2026-08-16 the
fence WAS a row — a ``builder-aider`` vertical in ``inference_domain``'s domains stack,
carrying this consumer's model pin and its allow-list. Akien killed it: *"The inference
proxy knows about providers and models. it does not understand about consumers. the
consumer asks for what it wants. period, end of story."* The whole obligation moved
here, and with it the reason the fence and the injection point are ONE OBJECT: aider
reaches every model it will ever reach through a single call site, so the thing that
translates the ask and the thing that judges it cannot drift apart if they are the same
code.

THE REFUSAL IS DELIBERATELY NOT A ``litellm`` EXCEPTION, and that is load-bearing rather
than tidy. aider catches ``LiteLLMExceptions.exceptions_tuple()`` — the named litellm
error classes (23, measured at HEAD 5dc9490bb) — and retries the retryable ones with exponential backoff to
``RETRY_TIMEOUT`` (60s). A refusal that wore one of those names would be ABSORBED by that
loop: sixty seconds of retrying a decision that will never change, and then a generic
failure in the record. ``AskWidened`` is outside the tuple, so it propagates out of aider
untouched — loud at the diagnostic surface, permanent in the record (Law 7). The class
name also deliberately does not end in ``Error``: ``LiteLLMExceptions._load`` walks
``dir(litellm)`` and raises ``ValueError`` on any ``*Error`` attribute it does not know,
so an attribute named ``AskWidenedError`` on the surface module would break aider at
import. Measured 2026-08-16 at ``aider/exceptions.py:68``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Instance-space, per Law 6 and the three roots: the tool's state berths under the holder
# that assembled it, never in class-space. A proof passes its own path — a sealed proof
# may not read instance-space.
DEFAULT_RECORD = Path.home() / ".cairn" / "devices" / "aider_shim" / "0" / "asks.jsonl"


class AskWidened(Exception):
    """The ask left the fence. Raised at the seam, before any host is touched."""


@dataclass(frozen=True)
class Fence:
    """What this device is allowed to ask for, by name.

    ``models`` and ``providers`` are EXACT-MATCH tuples, never patterns. A pattern is how
    an allow-list widens without anyone deciding to widen it.
    """

    models: tuple[str, ...] = ("qwen3-coder:30b",)
    providers: tuple[str, ...] = ("hex",)

    def check_model(self, name: str) -> None:
        if name not in self.models:
            raise AskWidened(
                f"model {name!r} is not on this device's fence {list(self.models)} — "
                "refusing before any host is touched. A build device that widens under "
                "failure is how a local-only device starts spending money."
            )

    def check_provider(self, name: str) -> None:
        if name not in self.providers:
            raise AskWidened(
                f"provider {name!r} served this ask, and this device's fence is "
                f"{list(self.providers)}. The route chose a provider the fence does not "
                "allow — the ask widened downstream of the name check."
            )


@dataclass
class SeenLog:
    """Every ask this device made, and how the fence dispositioned it.

    THIS EXISTS SO A GREEN CANNOT BE EARNED BY NOTHING HAPPENING. A fence proof that
    asserts 'no widened ask was served' passes trivially when no ask was made at all;
    the proof must also assert this log is non-empty and CONTAINS the widened name, which
    is what proves the fence was reached and reddened rather than bypassed.
    """

    entries: list[dict] = field(default_factory=list)
    record_path: Path | None = None

    def record(self, *, model: str, verdict: str, detail: str = "", provider: str = "") -> dict:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "verdict": verdict,          # "allowed" | "refused"
            "provider": provider,
            "detail": detail,
        }
        self.entries.append(row)
        path = self.record_path
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def names(self) -> list[str]:
        return [e["model"] for e in self.entries]

    def refused(self) -> list[dict]:
        return [e for e in self.entries if e["verdict"] == "refused"]

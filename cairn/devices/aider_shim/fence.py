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
failure in the record. ``AskWidened`` is outside the tuple, so it escapes THAT loop.

IT DOES NOT ESCAPE AIDER, AND THIS FILE SAID IT DID UNTIL 2026-08-17. The claim here was
that the refusal "propagates out of aider untouched"; measured, it does not. ``aider``
catches bare ``Exception`` at ``base_coder.py:1506``, prints the traceback to its own io
and returns, so a refusal reaches our caller as a quiet result with no error and no edits.
The retry tuple was one absorber and the design found it; the broad handler two lines of
control flow later was never looked for. So the refusal cannot be made loud by choosing a
class name — it is made loud by :class:`SeenLog` writing the row BEFORE the raise, at the
seam, where nothing downstream can swallow it. Law 7 is satisfied by the record, not by
the exception's flight path.

The class name still deliberately does not end in ``Error``: ``LiteLLMExceptions._load`` walks
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


class AskTruncated(Exception):
    """The host processed less than we sent — the model answered a payload we did not make.

    THIS IS THE DEFECT THAT COST THIS DEVICE ITS FIRST REAL DRIVE, and it happened entirely
    outside our code. ollama's ``num_ctx`` defaults to 4096 REGARDLESS of what the model's
    own ``context_length`` declares, and an over-long ask is silently CLAMPED: the API
    returns HTTP 200 and a fluent, coherent answer, with no field saying anything was
    dropped. Measured 2026-08-17 — the first driven piece sent 289,601 chars (~72k tokens:
    aider's system prompt, 129,319 chars of read-only reference, 141,238 chars of editable
    files, and a 13,932-char instruction) and hex reported ``prompt_eval_count=4271``. The
    apprentice never saw one of the files it was asked to edit, said so plainly (*"since no
    files have been added to the chat yet, I'll create the new file"*), and invented one.
    Every layer above read that as the model being weak.

    A silent clamp is a Law 7 breach in somebody else's process, so the fix is not to make
    ours quieter — it is to make the shortfall LOUD at our seam and permanent in our record.

    NOT NAMED ``*Error``, and not a ``litellm`` class, for exactly the reasons ``AskWidened``
    is not (see the module docstring): ``LiteLLMExceptions._load`` walks ``dir(litellm)`` and
    raises on an unknown ``*Error`` attribute, and anything inside aider's exception tuple
    would be absorbed into its 60-second retry loop — sixty seconds of re-sending an ask that
    will be clamped identically every time.
    """


@dataclass(frozen=True)
class Fence:
    """What this device is allowed to ask for, by name.

    ``models`` and ``providers`` are EXACT-MATCH tuples, never patterns. A pattern is how
    an allow-list widens without anyone deciding to widen it.
    """

    models: tuple[str, ...] = ("qwen3-coder:30b",)
    providers: tuple[str, ...] = ("hex",)

    #: THE ONE NUMBER, AND IT HAS TO BE ONE. Three numbers have to agree for an ask to be
    #: honest — what we tell aider it may send, what we ask the host to allocate, and what
    #: the host actually processes — and until 2026-08-17 none of the three came from the
    #: same place. aider was told 32768 (a constant in ``interceptor._model_cost``), the
    #: host was told nothing (so 4096, its default), and 4271 came back. This field is the
    #: single source: it rides the request as ``options.num_ctx``, it is what
    #: ``get_model_info`` reports to aider minus the output headroom, and it is the
    #: ceiling :meth:`check_processed` measures the answer against.
    #:
    #: 81920 is MEASURED, not chosen — and measured on one box at n=1, which is what makes
    #: it a debt rather than a setting. hex is a 32 GB M1 Studio; re-asking the captured
    #: 289,601-char payload at 81920 loads at 26.9 GB and answers, and the same ask at
    #: 98304 returns an empty reply with no counters after 11s. The method is the whole
    #: value of the number: post the payload to ``/api/chat`` with a candidate ``num_ctx``
    #: and read ``prompt_eval_count`` back. A second provider on the fence would need its
    #: own reading, which is why this cannot stay a constant forever — how this device
    #: LEARNS this number is the open half, recorded in the charter's ``how_it_learns``.
    ask_ctx: int = 81920

    #: Reserved for the reply, subtracted from :attr:`ask_ctx` before aider is told what it
    #: may send. Without it aider sizes a payload that fits the window exactly and the
    #: answer has nowhere to go.
    reply_headroom: int = 8192

    def send_budget(self) -> int:
        """What aider may put in an ask, in tokens — the number reported as
        ``max_input_tokens``."""
        return max(1, self.ask_ctx - self.reply_headroom)

    def check_processed(self, processed: int, *, sent_chars: int) -> None:
        """Red when the host filled the window to the brim — that is a clamp, not a fit.

        THE PREDICATE HAS NO ESTIMATE IN IT, deliberately. The obvious check — compare the
        host's ``prompt_eval_count`` against our own count of what we sent — cannot be made
        exact from here: this device's ``token_counter`` is a ``chars // 4`` approximation
        (it says so at its own definition), so the comparison would need a tolerance, and a
        tolerance is a place for a real truncation to hide.

        What IS exact is the ceiling. ollama clamps by DISCARDING until the payload fits the
        window, so a clamped ask comes back having processed essentially the whole window,
        while an ask that genuinely fits leaves headroom below it. Measured at n=1 on the
        drive that bore this check: ``num_ctx`` 4096 (the default), ``prompt_eval_count``
        4271 — over the nominal window, because the clamp preserves the system prompt and
        the tail rather than cutting at exactly N. So the test is *reached the ceiling*,
        not *equals the window*, and it needs nothing from us but the number we asked for.

        The one false positive this admits is an ask that honestly fills the window to the
        last token. That is measure-zero, and it errs LOUD — which is the direction Law 7
        picks when a check has to be wrong in one of two ways.
        """
        if processed >= self.ask_ctx:
            raise AskTruncated(
                f"the host processed {processed} tokens against a requested window of "
                f"{self.ask_ctx} — the window was filled to the brim, which is what a "
                f"CLAMP looks like, not a fit. The ask carried {sent_chars} chars "
                f"(~{sent_chars // 4} tokens by this device's estimate). The answer this "
                "would have returned is a fluent reply to a payload nobody sent: the model "
                "cannot see the files that were discarded and does not know they existed. "
                "Refusing it here rather than letting it become an edit."
            )

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

    #: WHY A `ticket` RIDES EVERY ASK. The offload probe has to answer "which tickets were
    #: actually built through the shim", and this log is the only place that knows: a
    #: verdict artifact records that a ticket reached a verdict, never that aider was the
    #: one that moved the code. Without it the probe would have to infer shimmed-ness from
    #: timing, which is a proxy that goes wrong the first time two voyages overlap.
    #: Defaults to "" so an ask made outside a ticket (a live fire, a proof) records
    #: honestly as ticketless rather than being attributed to whatever ran last.
    #: WHY THE THREE SIZE FIELDS RIDE EVERY ROW. They are the three numbers whose
    #: disagreement WAS the defect, and before 2026-08-17 this record carried none of them,
    #: so the clamp left no trace anywhere in the system. `ask_chars` is the only place the
    #: real size of an ask is ever written down — the driver's `prompt_chars` records the
    #: INSTRUCTION aider was handed (13,932 on the drive that bore this) and not the payload
    #: aider then built from it (289,601), a 20x understatement in a record of truth.
    #: `num_ctx` is what we asked the host to allocate and `prompt_eval_count` is what it
    #: reports having read; a row where the second reaches the first is a clamped ask, and
    #: now it says so on its face instead of needing a live re-ask to reconstruct.
    def record(self, *, model: str, verdict: str, detail: str = "", provider: str = "",
               ticket: str = "", ask_chars: int = 0, num_ctx: int = 0,
               prompt_eval_count: int | None = None) -> dict:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            # "allowed" | "refused" | "truncated" | "failed". Only "allowed" means the
            # apprentice was heard from; the driver reads exactly that when it decides
            # whether an empty edit list is evidence about the model or about the setup.
            "verdict": verdict,
            "provider": provider,
            "ticket": ticket,
            "ask_chars": ask_chars,
            "num_ctx": num_ctx,
            # None on a cache hit — no call was made, so there is no count. Honest null
            # rather than a zero that would read as "processed nothing".
            "prompt_eval_count": prompt_eval_count,
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

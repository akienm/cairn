"""cairn cross — a ticket's cursor crosses through one command (ticket 3d9cedf76a7e).

    python3 -m cairn.tools.base.cross <ticket-id> <TARGET> --actor <who> --why <why>
                                      [--proven-by P ...] [--missing M ...]

One standing door for every NON-REST crossing, so no voyage crosses through an ad hoc script
again (F21: each voyage had been writing its own). It finds the ticket in the store
transitions already names, derives the component from the ticket's owning_intention (the
charter's directory, refusing one that carries no charter), calls ``transitions.emit`` with
that component's history and state and ``ticket=<id>``, and writes emit's returned cursor
onto the ticket through the artifact door (verb cast) in the same act — the write-back
pattern ``set_phase(ticket=)`` already uses. emit refuses before writing anything, so a
refused crossing leaves the ticket and the history as they were.

A CROSSING INTO A REST IS REFUSED BY NAME. Entering proven-space belongs to
``cairn.devices.cairn.machines.harbor_master.clearance.clear``, a device-held machine this
tool may not reach (RULE 1); emit's own clearance gate would refuse it too, but later and
less plainly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cairn.tools.artifact.artifact import write
from cairn.tools.base import transitions


def cross(ticket_id: str, target: str, *, actor: str, why: str,
          proven_by: list[str] | None = None, missing: list[str] | None = None,
          tickets_dir: Path | None = None, repo_root: Path | None = None,
          node_class_root: Path | None = None) -> str:
    """Cross ``ticket_id``'s cursor to ``target``; return the new workflow string."""
    tickets_dir = Path(tickets_dir if tickets_dir is not None else transitions._TICKETS)
    repo_root = Path(repo_root if repo_root is not None else transitions._REPO_ROOT)
    node_class_root = Path(node_class_root if node_class_root is not None
                           else transitions._NODE_CLASSES)
    hits = sorted(tickets_dir.glob(f"{ticket_id}-*.json"))
    if len(hits) != 1:
        raise ValueError(f"ticket {ticket_id} resolves to {len(hits)} files under {tickets_dir}, "
                         "not one")
    tp = hits[0]
    t = json.loads(tp.read_text(encoding="utf-8"))
    wf = transitions.parse_workflow(t["workflow_and_state"])
    class_def = transitions.load_class_def(wf.node_class, root=node_class_root)
    tgt = transitions.canon_target(wf, target, class_def)
    if (tgt in wf.path and not transitions.is_summons(tgt)
            and not transitions.is_disposition(tgt, class_def)):
        raise ValueError(f"{tgt} is a rest: the crossing into it is cleared by "
                         "cairn.devices.cairn.machines.harbor_master.clearance.clear, "
                         "not by this command")
    owning = str(t.get("owning_intention") or "")
    dev = repo_root / Path(owning).parent
    if not owning or not (dev / "intention+why.json").is_file():
        raise ValueError(f"owning_intention {owning!r} names no charter: "
                         f"{dev}/intention+why.json is not a file")
    extra: dict = {"ticket": ticket_id, "actor": actor, "why": why}
    if proven_by:
        extra["proven_by"] = list(proven_by)
    if missing:
        extra["missing"] = list(missing)
    new = transitions.emit(t["workflow_and_state"], target,
                           history_path=str(dev / "history.json"),
                           state_path=str(dev / "state.json"),
                           node_class_root=node_class_root, **extra)
    if new != t["workflow_and_state"]:
        t["workflow_and_state"] = new
        write(str(tp), json.dumps(t, indent=2, ensure_ascii=False) + "\n", verb="cast", why=why)
    return new


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cairn cross", description=__doc__.strip().splitlines()[0])
    ap.add_argument("ticket")
    ap.add_argument("target")
    ap.add_argument("--actor", required=True)
    ap.add_argument("--why", required=True)
    ap.add_argument("--proven-by", action="append", default=[])
    ap.add_argument("--missing", action="append", default=[])
    a = ap.parse_args(argv)
    try:
        new = cross(a.ticket, a.target, actor=a.actor, why=a.why,
                    proven_by=a.proven_by or None, missing=a.missing or None)
    except Exception as e:  # noqa: BLE001 — every refusal is printed, verbatim, and writes nothing
        print(f"refused: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(new)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""The counting block's host seam: its post-commit SUBSCRIBER, fired by the fan-out (ticket
5a4ec289bf15 D26, D27; e0f318650123 D5).

THE INSTALLED HOOK IS NOW THE FAN-OUT'S. Git runs one installed post-commit, and until
e0f318650123 it was this block's body, so no other component could hear a commit except by
polling HEAD on the beat. ``cairn/tools/post_commit`` owns the installed hook now and runs every
tracked ``<component>/hooks/post-commit`` once; this block's ``hooks/post-commit`` is one of
those subscribers, unchanged. The three functions below stay as thin delegations to the tool's
declared public interface (``cairn.tools.post_commit.fanout``) so this block's own CLI and its
proof keep their surface; REPO_ROOT, HOOK_SOURCE and _MARK still describe the subscriber body.
"""
from pathlib import Path

from cairn.tools.post_commit import fanout

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SOURCE = Path(__file__).parent / "hooks" / "post-commit"
_MARK = "cairn-counting-block-door"


def hook_path(root: Path | None = None) -> Path:
    """Where git looks for the one installed post-commit — the fan-out's."""
    return fanout.hook_path(root)


def install_hook(root: Path | None = None) -> dict:
    """Install the fan-out, which runs this block's subscriber body on every commit."""
    return fanout.install_hook(root)


def verify_hook(root: Path | None = None) -> dict:
    """Green only when this block's subscriber body is present AND the fan-out that runs it is
    installed — a live read of the host, never a record of having installed it once."""
    if not HOOK_SOURCE.is_file():
        return {"green": False, "path": str(HOOK_SOURCE),
                "why": f"the subscriber body is missing: {HOOK_SOURCE}"}
    return fanout.verify_hook(root)

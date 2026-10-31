"""The argv prefix that runs a bash script: the script itself on POSIX, ``bash <script>`` on Windows.

Windows cannot exec a shebang script (``OSError: [WinError 193] %1 is not a valid Win32
application``), so a caller that builds an argv for ``bin/cairn`` or a ``bin/cmd/*`` script
puts this in front instead of the bare path. On POSIX the result is ``[str(path)]`` -- the
argv every caller built before this existed.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def bash_script_argv(path: Path | str) -> list[str]:
    """``[str(path)]`` on POSIX; ``[bash, str(path)]`` where ``os.name == 'nt'``."""
    if os.name != "nt":
        return [str(path)]
    return [shutil.which("bash") or "bash", str(path)]

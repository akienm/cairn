"""aider_shim — the device that holds aider in-process and fences its model calls.

The charter is ``intention+why.json`` beside this file. Nothing here imports aider at
module load: the interceptor must be installed at ``sys.modules['litellm']`` BEFORE aider
is imported, so importing this package must never trigger that import itself.
"""

from cairn.devices.aider_shim.fence import AskWidened, Fence, SeenLog
from cairn.devices.aider_shim.interceptor import install, installed

__all__ = ["AskWidened", "Fence", "SeenLog", "install", "installed"]

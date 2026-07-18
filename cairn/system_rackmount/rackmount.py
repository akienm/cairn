"""system_rackmount — the rack-mount device that abstracts the host's SYSTEM SERVICES,
device-independently.

A rack holds rack-mount devices. THIS device is the one that stands in the rack for *the system
underneath* — the host's services (scheduling, and more to come). Its whole point is device-
independence: a device that needs a system service asks the rackmount for it BY NAME and uses
that service's interface, never reaching the OS directly. So the same fleet runs whether the
scheduling backing is a thread, cron, or a systemd timer; whether privilege comes via sudo or
something else. The OS-specific parts live *behind* the services this device surfaces — swapped
without touching any device that depends on them.

WHAT IT DOES (v0): holds a registry of named system services and hands them out via
``service(name)``. Its first service is the ``scheduler`` (services/scheduler.py) — the physics
of WHEN a driver fires, itself firing onto ``ground_loop``. More system services mount here as
they are built (privilege/sudo, filesystem, network are the same shape: a device-independent
face over an OS-specific backing). Asking for a service that is not mounted is a LOUD miss
(CP1 / Law 7), never a silent ``None`` a caller could mistake for an idle service.

WHY a device and not a bare module: it carries CP1-CP6 and reports the Form v0 #2 surface, so
the system-services layer is inspectable like everything else on the spine — a device can always
be asked what system services exist and what state they are in. It composes ``ground_loop``
(passing it to the scheduler) and introduces no authority of its own beyond the abstraction.

FILED EDGES (children of this stone):
  - Services are held IN-MEMORY and constructed eagerly at boot; a durable/declared service
    registry waits on a real multi-service need.
  - The scheduler's OS-specific wall-clock backing (the daemon that pulses ``tick`` on a real
    cadence) is a thin wrapper this device will own — filed on the scheduler, not built yet.
  - sudo_relay (privilege) is a system service in the same family, built standalone first; it
    migrates behind this abstraction when a second consumer makes the seam pay for itself.
"""

from __future__ import annotations

from cairn.base.device import BaseDevice
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.system_rackmount.services.scheduler import SchedulerService


class SystemRackmountDevice(BaseDevice):
    """The rack-mount device abstracting host system services device-independently (carries
    CP1-CP6; reports intention/state/settings). Its capability is ``service(name)`` — hand a
    named system service to a device that asks, so no device touches the OS directly."""

    def __init__(self, ground_loop: GroundLoopDevice, device_id: str = "system_rackmount") -> None:
        super().__init__()
        if not isinstance(ground_loop, GroundLoopDevice):
            raise ValueError("the system rackmount surfaces the scheduler onto a GroundLoopDevice")
        self._device_id = device_id
        # v0: the services this rackmount abstracts. The scheduler is the first; more mount here.
        self._services: dict[str, object] = {
            SchedulerService.name: SchedulerService(ground_loop),
        }

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- the one capability: hand out a named system service ----------------

    def service(self, name: str):
        """Return the named system service, or refuse loudly if it is not mounted (CP1 / Law 7 —
        a missing service is a diagnostic error, never a silent None a caller could misread)."""
        if name not in self._services:
            raise KeyError(f"no system service {name!r} on the rackmount; mounted: "
                           f"{sorted(self._services)}")
        return self._services[name]

    def services(self) -> list[str]:
        """The names of the system services this rackmount abstracts."""
        return sorted(self._services)

    @property
    def scheduler(self) -> SchedulerService:
        """Convenience for the first service — same object as ``service('scheduler')``."""
        return self._services[SchedulerService.name]

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The rack-mount device that abstracts the host's system services (scheduling, "
            "and more) device-independently: a device asks for a service by name and uses its "
            "interface, never touching the OS underneath.",
            "why": "So no device is coupled to the host: the OS-specific backing (a thread vs cron "
            "vs a systemd timer; one privilege path vs another) is swapped behind these services "
            "without changing any device that depends on them — the system, made a device.",
        }

    def state(self) -> dict:
        return {
            "services": self.services(),
            "scheduler": self.scheduler.state(),  # the first service's condition, folded in
        }

    def settings(self) -> dict:
        return {
            "abstraction": "device-independent — services are reached by name via service(name); "
            "the OS-specific backing of each lives behind its interface, swappable.",
            "services": {name: type(svc).__name__ for name, svc in self._services.items()},
            "scheduler": self.scheduler.settings(),
        }

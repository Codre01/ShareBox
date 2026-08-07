from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ServiceState(str, Enum):
    NOT_RUNNING = "not_running"
    INITIALIZING = "initializing"
    READY = "ready"
    SHARING = "sharing"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class RuntimeState:
    state: ServiceState = ServiceState.NOT_RUNNING
    sharing: bool = False
    error: str | None = None
    lan_addresses: list[str] = field(default_factory=list)
    port: int = 8765
    active_pairing: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "sharing": self.sharing,
            "error": self.error,
            "lan_addresses": self.lan_addresses,
            "port": self.port,
            "url_hints": [f"http://{a}:{self.port}" for a in self.lan_addresses]
            + ([f"http://sharebox.local:{self.port}"] if self.lan_addresses else []),
            "active_pairing": self.active_pairing,
        }

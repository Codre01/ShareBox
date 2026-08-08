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
    mdns_active: bool = False
    mdns_ip: str | None = None
    use_https: bool = False
    cert_fingerprint: str | None = None

    @property
    def scheme(self) -> str:
        return "https" if self.use_https else "http"

    def as_dict(self) -> dict[str, Any]:
        port = self.port
        scheme = self.scheme
        # V1 uses LAN IPs only — sharebox.local / mDNS confused mobile browsers
        # (Android often fails; iOS treats .local and IP as different sites).
        url_hints = [f"{scheme}://{a}:{port}" for a in self.lan_addresses]
        return {
            "state": self.state.value,
            "sharing": self.sharing,
            "error": self.error,
            "lan_addresses": self.lan_addresses,
            "port": port,
            "mdns_active": False,
            "mdns_ip": None,
            "scheme": scheme,
            "use_https": self.use_https,
            "cert_fingerprint": self.cert_fingerprint,
            "url_hints": url_hints,
            "primary_url": url_hints[0] if url_hints else f"{scheme}://127.0.0.1:{port}",
            "active_pairing": self.active_pairing,
        }

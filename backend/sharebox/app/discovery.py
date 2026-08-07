from __future__ import annotations

import logging
import socket
import threading
from typing import TYPE_CHECKING

logger = logging.getLogger("sharebox.discovery")

if TYPE_CHECKING:
    from zeroconf import ServiceInfo, Zeroconf


class MdnsAdvertiser:
    """Advertise sharebox.local → the primary LAN IP shown in Control Center."""

    def __init__(self, port: int, host_name: str) -> None:
        self.port = port
        self.host_name = host_name
        self._zc: Zeroconf | None = None
        self._info: ServiceInfo | None = None
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self.active = False
        self.advertised_ip: str | None = None

    def start(self, addresses: list[str]) -> None:
        """addresses: IPv4 strings; first entry is the Control Center primary address."""
        ips = [a for a in addresses if a]
        if not ips:
            return
        self.stop()
        self._thread = threading.Thread(
            target=self._register,
            args=(ips,),
            name="sharebox-mdns",
            daemon=True,
        )
        self._thread.start()

    def _register(self, ips: list[str]) -> None:
        try:
            from zeroconf import IPVersion, ServiceInfo, Zeroconf
        except ImportError:
            logger.warning("zeroconf not available; mDNS disabled")
            return

        primary = ips[0]
        packed: list[bytes] = []
        for ip in ips:
            try:
                packed.append(socket.inet_aton(ip))
            except OSError:
                continue
        if not packed:
            return

        zc = None
        try:
            # Bind mDNS to the same interface IP the UI advertises when possible.
            try:
                zc = Zeroconf(interfaces=[primary], ip_version=IPVersion.V4Only)
            except Exception:
                zc = Zeroconf(ip_version=IPVersion.V4Only)

            info = ServiceInfo(
                type_="_http._tcp.local.",
                name="ShareBox._http._tcp.local.",
                addresses=packed,
                port=self.port,
                properties={"path": "/", "app": "sharebox"},
                server="sharebox.local.",
            )
            zc.register_service(info, allow_name_change=True)
            with self._lock:
                self._zc = zc
                self._info = info
                self.active = True
                self.advertised_ip = primary
            logger.info("mDNS: sharebox.local → %s:%s", primary, self.port)
        except Exception:
            self.active = False
            self.advertised_ip = None
            logger.warning(
                "mDNS unavailable — use the IP address shown in Control Center",
                exc_info=True,
            )
            if zc is not None:
                try:
                    zc.close()
                except Exception:
                    pass

    def stop(self) -> None:
        with self._lock:
            zc, info = self._zc, self._info
            self._zc = None
            self._info = None
            self.active = False
            self.advertised_ip = None
        if zc and info:
            try:
                zc.unregister_service(info)
            except Exception:
                pass
        if zc:
            try:
                zc.close()
            except Exception:
                pass

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

logger = logging.getLogger("sharebox.discovery")

if TYPE_CHECKING:
    from zeroconf import ServiceInfo, Zeroconf


class MdnsAdvertiser:
    """Advertise ShareBox via mDNS (best-effort; never blocks app startup)."""

    def __init__(self, port: int, host_name: str) -> None:
        self.port = port
        self.host_name = host_name
        self._zc: Zeroconf | None = None
        self._info: ServiceInfo | None = None
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self, addresses: list[bytes]) -> None:
        """Kick off registration on a daemon thread so FastAPI lifespan is not blocked."""
        if not addresses:
            return
        self.stop()
        self._thread = threading.Thread(
            target=self._register,
            args=(list(addresses),),
            name="sharebox-mdns",
            daemon=True,
        )
        self._thread.start()

    def _register(self, addresses: list[bytes]) -> None:
        try:
            from zeroconf import ServiceInfo, Zeroconf
        except ImportError:
            logger.warning("zeroconf not available; mDNS disabled")
            return
        try:
            zc = Zeroconf()
            info = ServiceInfo(
                type_="_http._tcp.local.",
                name="ShareBox._http._tcp.local.",
                addresses=addresses,
                port=self.port,
                properties={"path": "/", "app": "sharebox"},
                server="sharebox.local.",
            )
            # allow_name_change avoids long conflicts on Windows home networks
            zc.register_service(info, allow_name_change=True)
            with self._lock:
                self._zc = zc
                self._info = info
            logger.info("mDNS registered sharebox.local:%s", self.port)
        except Exception:
            logger.warning(
                "mDNS unavailable (LAN discovery by hostname may not work; IP:port still works)",
                exc_info=True,
            )
            try:
                if "zc" in locals():
                    zc.close()
            except Exception:
                pass

    def stop(self) -> None:
        with self._lock:
            zc, info = self._zc, self._info
            self._zc = None
            self._info = None
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

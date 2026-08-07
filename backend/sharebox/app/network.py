from __future__ import annotations

import socket
from ipaddress import ip_address


def list_lan_addresses() -> list[str]:
    """Return likely LAN IPv4 addresses for this host."""
    addresses: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            addr = info[4][0]
            if _is_usable_lan(addr) and addr not in addresses:
                addresses.append(addr)
    except OSError:
        pass

    # Fallback: UDP connect trick to discover default-route interface.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            addr = s.getsockname()[0]
            if _is_usable_lan(addr) and addr not in addresses:
                addresses.insert(0, addr)
    except OSError:
        pass

    return addresses


def _is_usable_lan(addr: str) -> bool:
    try:
        ip = ip_address(addr)
    except ValueError:
        return False
    if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        return False
    return bool(ip.is_private)


def primary_lan_address() -> str | None:
    addrs = list_lan_addresses()
    return addrs[0] if addrs else None

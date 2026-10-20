from __future__ import annotations

import ipaddress


def mask_ip(raw: str) -> str:
    """Replace last IPv4 octet or last two IPv6 groups with ***."""
    if not raw or raw == "localhost":
        return raw

    raw = raw.split("%")[0]  # strip scope ID

    if raw.startswith("["):  # [ipv6]:port
        raw = raw[1:raw.rfind("]")]
    elif raw.count(":") == 1:  # ipv4:port
        raw = raw.rsplit(":", 1)[0]

    try:
        addr = ipaddress.ip_address(raw)
    except ValueError:
        return raw

    if addr.version == 4:
        prefix, _ = addr.exploded.rsplit(".", 1)
        return f"{prefix}.***"
    else:
        groups = addr.exploded.split(":")
        return ":".join(groups[:6]) + ":***:***"

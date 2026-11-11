"""
SSRF and remote network request boundary protection.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from opengen.domain.errors import SecurityViolationError

FORBIDDEN_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.169.254/32")  # Cloud metadata
]

def assert_safe_remote_url(url: str):
    """Ensures a remote URL does not resolve to internal networks or metadata endpoints."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecurityViolationError(f"Disallowed scheme: '{parsed.scheme}'. Must be HTTP/HTTPS.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityViolationError("Missing URL hostname.")

    try:
        ip_str = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip_str)
    except Exception as e:
        raise SecurityViolationError(f"DNS resolution failed for hostname '{hostname}': {e}")

    for net in FORBIDDEN_NETWORKS:
        if ip_addr in net:
            raise SecurityViolationError(f"SSRF blocked: Host resolves to protected network address ({ip_addr}).")

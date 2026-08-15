import ipaddress
from urllib.parse import urlsplit, urlunsplit

from app.common.exceptions import AppException


def normalize_research_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AppException(422, "INVALID_SOURCE_URL", "Only absolute HTTP(S) URLs are allowed.")
    if parsed.username or parsed.password:
        raise AppException(422, "INVALID_SOURCE_URL", "URLs containing user information are not allowed.")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host == "metadata.google.internal":
        raise AppException(422, "UNSAFE_SOURCE_URL", "Local and metadata destinations are not allowed.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise AppException(422, "UNSAFE_SOURCE_URL", "Private, loopback, and link-local destinations are not allowed.")
    port = parsed.port
    netloc = host if port is None else f"{host}:{port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def validate_supplier_domain(source_url: str, supplier_url: str, allow_subdomains: bool = False) -> None:
    source_host = urlsplit(source_url).hostname or ""
    supplier_host = (urlsplit(supplier_url).hostname or "").rstrip(".").lower()
    matches = source_host == supplier_host or (allow_subdomains and source_host.endswith(f".{supplier_host}"))
    if not matches:
        raise AppException(422, "SOURCE_DOMAIN_MISMATCH", "The source URL must use the supplier website domain.")

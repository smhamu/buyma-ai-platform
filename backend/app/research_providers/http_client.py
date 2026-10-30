import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from app.common.exceptions import AppException
from app.utils.research_url import normalize_research_url, validate_supplier_domain


class SafeResearchHttpClient:
    def __init__(self, *, max_bytes: int = 1_000_000, max_redirects: int = 3, timeout_seconds: float = 15.0, transport=None):
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    @staticmethod
    async def _resolve_public_address(url: str) -> str:
        host = urlsplit(url).hostname
        if not host:
            raise AppException(422, "INVALID_SOURCE_URL", "The source URL has no hostname.")
        try:
            addresses = await asyncio.to_thread(socket.getaddrinfo, host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise AppException(502, "SOURCE_DNS_ERROR", "The supplier hostname could not be resolved.") from exc
        if not addresses:
            raise AppException(502, "SOURCE_DNS_ERROR", "The supplier hostname returned no addresses.")
        public_addresses = []
        for entry in addresses:
            address = ipaddress.ip_address(entry[4][0])
            if not address.is_global:
                raise AppException(422, "UNSAFE_SOURCE_URL", "The supplier hostname resolves to a non-public address.")
            public_addresses.append(str(address))
        return public_addresses[0]

    @staticmethod
    def _pinned_url(url: str, address: str) -> tuple[str, str]:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        display_address = f"[{address}]" if ":" in address else address
        port = parsed.port
        netloc = display_address if port is None else f"{display_address}:{port}"
        host_header = host if port is None else f"{host}:{port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, "")), host_header

    async def get(self, url: str, supplier_url: str) -> tuple[str, str]:
        current = normalize_research_url(url)
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=self.timeout_seconds,
            trust_env=False,
            transport=self.transport,
            headers={"User-Agent": "BUYMA-AI-Research/1.0 (+manual-admin-fetch)"},
        ) as client:
            for redirect_count in range(self.max_redirects + 1):
                validate_supplier_domain(current, supplier_url)
                address = await self._resolve_public_address(current)
                pinned_url, host_header = self._pinned_url(current, address)
                async with client.stream(
                    "GET",
                    pinned_url,
                    headers={"Host": host_header},
                    extensions={"sni_hostname": urlsplit(current).hostname},
                ) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location or redirect_count == self.max_redirects:
                            raise AppException(502, "SOURCE_REDIRECT_REJECTED", "The supplier response used an invalid redirect.")
                        current = normalize_research_url(urljoin(current, location))
                        validate_supplier_domain(current, supplier_url)
                        continue
                    if response.status_code != 200:
                        raise AppException(502, "SOURCE_FETCH_FAILED", f"The supplier returned HTTP {response.status_code}.")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if content_type not in {"text/html", "application/json", "application/ld+json"}:
                        raise AppException(422, "UNSUPPORTED_SOURCE_CONTENT", "The supplier response is not HTML or JSON.")
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > self.max_bytes:
                            raise AppException(413, "SOURCE_RESPONSE_TOO_LARGE", "The supplier response exceeds the configured size limit.")
                        chunks.append(chunk)
                    encoding = response.encoding or "utf-8"
                    try:
                        return b"".join(chunks).decode(encoding), content_type
                    except (LookupError, UnicodeDecodeError) as exc:
                        raise AppException(422, "INVALID_SOURCE_ENCODING", "The supplier response could not be decoded.") from exc
        raise AppException(502, "SOURCE_FETCH_FAILED", "The supplier response could not be fetched.")

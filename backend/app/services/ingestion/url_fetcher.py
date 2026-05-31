from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings
from app.services.ingestion.extractors import IngestionError, SourceKind, validate_extracted_text

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_CONTENT_TYPES = {
    "text/html",
    "text/plain",
    "application/xhtml+xml",
}
_USER_AGENT = "JobFitAI-Ingestion/0.1 (+https://localhost)"


@dataclass(slots=True)
class FetchedJobDescription:
    """Text extracted from a public job description URL."""

    url: str
    text: str
    content_type: str | None
    title: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def char_count(self) -> int:
        return len(self.text)


async def fetch_job_description_from_url(
    url: str,
    *,
    settings: Settings,
) -> FetchedJobDescription:
    """Fetch and extract visible job-description text from a public URL."""

    normalized_url = _validate_public_url(url)
    timeout = httpx.Timeout(settings.url_fetch_timeout_seconds)
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1"}

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        max_redirects=3,
        headers=headers,
    ) as client:
        try:
            response = await client.get(normalized_url)
        except httpx.HTTPError as exc:
            raise IngestionError("Could not fetch the job description URL.") from exc

    final_url = _validate_public_url(str(response.url))
    # Defensive: normalization should not change valid response URLs.
    if final_url != str(response.url):
        raise IngestionError("Job URL redirected to an unsupported destination.")

    if response.status_code >= 400:
        raise IngestionError(f"Job URL returned HTTP {response.status_code}.")

    content = await response.aread()
    if len(content) > settings.max_url_response_bytes:
        raise IngestionError("Job URL response is too large to ingest safely.")

    content_type = response.headers.get("content-type", "").split(";", maxsplit=1)[0].lower()
    if content_type and content_type not in _ALLOWED_CONTENT_TYPES:
        raise IngestionError("Job URL must return a public HTML or plain text page.")

    raw_text = response.text
    if content_type == "text/plain":
        title = None
        extracted = raw_text
    else:
        title, extracted = _extract_visible_html_text(raw_text)

    normalized_text = validate_extracted_text(extracted, source_label=SourceKind.URL.value)
    warnings: list[str] = []
    if len(normalized_text) < 800:
        warnings.append("Extracted URL text is short; verify the JD content before matching.")

    return FetchedJobDescription(
        url=normalized_url,
        text=normalized_text,
        content_type=content_type or None,
        title=title,
        warnings=warnings,
    )


def _extract_visible_html_text(html: str) -> tuple[str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for selector in ("script", "style", "noscript", "svg", "header", "footer", "nav", "form"):
        for node in soup.select(selector):
            node.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else None
    main_node = soup.find("main") or soup.find("article") or soup.body or soup
    chunks = [chunk.strip() for chunk in main_node.get_text("\n", strip=True).splitlines()]
    return title, "\n".join(chunk for chunk in chunks if chunk)


def _validate_public_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise IngestionError("Only public http(s) job URLs are supported.")
    if not parsed.hostname:
        raise IngestionError("Job URL must include a hostname.")

    hostname = parsed.hostname.strip().lower()
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or _default_port(parsed.scheme))
    except socket.gaierror as exc:
        raise IngestionError("Could not resolve the job URL hostname.") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if _is_blocked_ip(ip):
            raise IngestionError("Private, local, or reserved job URLs are not allowed.")

    return parsed.geturl()


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )

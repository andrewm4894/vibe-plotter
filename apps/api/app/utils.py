from __future__ import annotations

import io
import ipaddress
from typing import Optional
from urllib.parse import urlparse

import httpx
import pandas as pd

from .config import settings
from .models import AppError


def _is_private_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def validate_csv_url(url: str, allowed_hosts: Optional[set[str]] = None) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise AppError("invalid_url", "Only http(s) URLs are allowed.")
    if not parsed.hostname:
        raise AppError("invalid_url", "URL must include a hostname.")

    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise AppError("invalid_url", "Localhost URLs are not allowed.")
    if _is_private_ip(host):
        raise AppError("invalid_url", "Private network URLs are not allowed.")
    if allowed_hosts is not None and host not in allowed_hosts:
        raise AppError("invalid_url", "URL host is not in the allowed list.")


def _enforce_max_bytes(content_length: int | None) -> None:
    if content_length is not None and content_length > settings.max_csv_bytes:
        raise AppError(
            "csv_too_large",
            f"CSV exceeds max size of {settings.max_csv_bytes} bytes.",
        )


async def read_csv_from_url(url: str) -> pd.DataFrame:
    validate_csv_url(url, settings.allowed_hosts_set)

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit():
                _enforce_max_bytes(int(content_length))

            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                total += len(chunk)
                if total > settings.max_csv_bytes:
                    raise AppError(
                        "csv_too_large",
                        f"CSV exceeds max size of {settings.max_csv_bytes} bytes.",
                    )
                chunks.append(chunk)

    data = b"".join(chunks)
    return pd.read_csv(io.BytesIO(data))

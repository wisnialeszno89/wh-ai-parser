"""Safely identify which authentication layer rejected NaviMind V2.

Makes one POST with a deliberately invalid empty JSON contract. A correctly
authenticated endpoint should return 400 INVALID_AGENT_TASK, never call a
reasoning model and never interact with the desktop.
Only logs allowlisted error categories, never server HTML, secrets or URLs.
"""
from __future__ import annotations
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from dotenv import load_dotenv


def classify_auth_response(status: int, content_type: str, body: bytes) -> str:
    if status in (401, 403):
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeError, ValueError):
            data = None
        if isinstance(data, dict) and data.get("error") == "UNAUTHORIZED":
            return "navimind_secret_rejected"
        if "html" in content_type.casefold() or (
            b"<html" in body[:512].lower()
        ):
            return "vercel_or_upstream_protection"
        return "unknown_auth_layer"
    if status == 400:
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeError, ValueError):
            return "unexpected_400_format"
        if isinstance(data, dict) and data.get("error") in {
            "INVALID_AGENT_TASK", "INVALID_AGENT_TASK_V2"
        }:
            return "navimind_auth_accepted_contract_validation_reached"
        return "unknown_400_reason"
    if status == 503:
        return "navimind_configuration_or_upstream_unavailable"
    if status >= 500:
        return "server_error"
    return "unexpected_http_status"


def probe(*, url: str, secret: str, opener=urlopen) -> tuple[int, str]:
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname
            or parts.username or parts.password or parts.query or parts.fragment
            or parts.path.rstrip("/") != "/api/agent/task"):
        raise ValueError("invalid_endpoint")
    if not isinstance(secret, str) or not secret.strip():
        raise ValueError("missing_secret")
    request = Request(
        url, data=b'{"version":"2"}',
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-navimind-agent-secret": secret,
        },
        method="POST",
    )
    try:
        with opener(request, timeout=15) as response:
            status = int(response.status)
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2048)
    except HTTPError as error:
        status = int(error.code)
        content_type = error.headers.get("Content-Type", "")
        body = error.read(2048)
    except URLError:
        return 0, "network_or_tls_error"
    return status, classify_auth_response(status, content_type, body)


def main() -> int:
    load_dotenv()
    url = os.environ.get("NAVIMIND_AGENT_V2_URL", "")
    secret = os.environ.get("NAVIMIND_AGENT_V2_SECRET", "")
    try:
        status, result = probe(url=url, secret=secret)
    except (ValueError, OSError) as exc:
        print("NAVIMIND_AUTH_LAYER=local_configuration_error")
        print("NAVIMIND_AUTH_HINT=" + type(exc).__name__)
        return 2
    print("NAVIMIND_AUTH_HTTP_STATUS=" + str(status))
    print("NAVIMIND_AUTH_LAYER=" + result)
    print("NAVIMIND_AUTH_MODEL_CALLED=False")
    if result == "navimind_auth_accepted_contract_validation_reached":
        return 0
    return 5


if __name__ == "__main__":
    raise SystemExit(main())

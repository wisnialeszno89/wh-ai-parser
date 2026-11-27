"""Read-only authenticated V2 route check; never sends customer or GUI data.

Uses a deliberately invalid synthetic version-2 request. A matching server
returns HTTP 400 / INVALID_AGENT_TASK_V2 *after* auth and provider checks.
No real model call or GUI action can result from an invalid contract.
Never prints secrets, full URLs, returned HTML, response headers or tokens.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, Request, build_opener,
)
import ssl


DOTENV = Path(__file__).resolve().parents[1] / ".env"
DEFAULT_V2_URL = "https://www.navimind.app/api/agent/task"
VERIFIED_RESULT = "v2_authenticated_contract_rejected_as_expected"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def effective_v2_environment():
    from dotenv import dotenv_values

    persisted = dotenv_values(DOTENV, interpolate=False)
    for url, secret in (
        ("NAVIMIND_AGENT_V2_URL", "NAVIMIND_AGENT_V2_SECRET"),
        ("NAVIMIND_AGENT_URL", "NAVIMIND_AGENT_SECRET"),
    ):
        if (persisted.get(url) or "").strip() and (persisted.get(secret) or "").strip():
            if url == "NAVIMIND_AGENT_URL":
                persisted.pop("NAVIMIND_AGENT_V2_URL", None)
            return persisted
    return os.environ



def configured_v2_connection(environ=None):
    """Return URL and credential only to local caller; no network or logging."""
    values = effective_v2_environment() if environ is None else environ
    dedicated_url = (values.get("NAVIMIND_AGENT_V2_URL") or "").strip()
    dedicated = bool(dedicated_url)
    url = dedicated_url or (values.get("NAVIMIND_AGENT_URL") or "").strip()
    secret_key = (
        "NAVIMIND_AGENT_V2_SECRET" if dedicated else "NAVIMIND_AGENT_SECRET"
    )
    secret = (values.get(secret_key) or "").strip()
    if not url:
        return "v2_endpoint_missing", None
    if not secret:
        return "v2_secret_missing", None
    try:
        parts = urlsplit(url)
        host = parts.hostname
        valid_scheme = parts.scheme == "https" or (
            parts.scheme == "http" and host in {"localhost", "127.0.0.1"}
        )
        if (
            not valid_scheme or not host or parts.username or parts.password
            or parts.query or parts.fragment
            or (not dedicated and parts.path.rstrip("/") != "/api/agent/task")
        ):
            return "v2_endpoint_invalid", None
    except ValueError:
        return "v2_endpoint_invalid", None
    bypass = (values.get("NAVIMIND_VERCEL_PROTECTION_BYPASS") or "").strip()
    return None, (url, secret, bypass)


def _safe_error_code(error):
    try:
        content_type = error.headers.get("Content-Type", "").lower()
        if "application/json" not in content_type:
            return None
        payload = json.loads(error.read(512).decode("utf-8"))
        code = payload.get("error") if isinstance(payload, dict) else None
        if code in {
            "INVALID_AGENT_TASK_V2", "UNAUTHORIZED",
            "AGENT_AUTH_NOT_CONFIGURED", "AGENT_PROVIDER_NOT_CONFIGURED",
        }:
            return code
    except (ValueError, UnicodeError, AttributeError, OSError):
        pass
    return None


def probe_v2(*, environ=None, opener=None):
    blocker, configuration = configured_v2_connection(environ)
    if blocker:
        return blocker
    url, secret, bypass = configuration
    if urlsplit(url).path.rstrip("/") != "/api/agent/task":
        return "v2_probe_requires_agent_task_route"
    # A synthetic invalid payload cannot pass V2 validation to the LLM.
    body = b'{"version":"2"}'
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-navimind-agent-secret": secret,
    }
    if bypass:
        headers["x-vercel-protection-bypass"] = bypass
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        if opener is None:
            opener = build_opener(
                HTTPSHandler(context=ssl.create_default_context()),
                NoRedirect(),
            )
        response = opener.open(request, timeout=12)
        try:
            # The deliberately invalid request should NOT return success.
            return "v2_unexpected_success_response"
        finally:
            response.close()
    except HTTPError as error:
        code = _safe_error_code(error)
        if error.code == 400 and code == "INVALID_AGENT_TASK_V2":
            return VERIFIED_RESULT
        if error.code == 401 and code == "UNAUTHORIZED":
            return "v2_application_secret_rejected"
        if error.code in (401, 403) and code is None:
            return "v2_vercel_or_proxy_access_denied"
        if error.code in (301, 302, 303, 307, 308):
            return "v2_redirect_refused_check_vercel_protection"
        if error.code == 503 and code:
            return "v2_server_" + code.lower()
        return "v2_http_" + str(error.code) + "_unverified"
    except (URLError, TimeoutError, OSError):
        return "v2_network_or_tls_unavailable"


def setup_v2(*, read=input, secret_read=getpass.getpass):
    from tools.configure_navimind_chat import _secure_save

    try:
        url = read(f"Endpoint aplikacji V2 [{DEFAULT_V2_URL}]: ").strip() or DEFAULT_V2_URL
        secret = secret_read("Sekret aplikacji NaviMind (NAVIMIND_AGENT_SECRET): ").strip()
        bypass = secret_read("Klucz ochrony wdrożenia Vercel (Enter, jeśli niewymagany): ").strip()
    except (EOFError, KeyboardInterrupt):
        return 2
    entries = {
        "NAVIMIND_AGENT_V2_URL": url,
        "NAVIMIND_AGENT_V2_SECRET": secret,
        "NAVIMIND_VERCEL_PROTECTION_BYPASS": bypass,
    }
    result = probe_v2(environ=entries)
    print("V2_PROBE_RESULT=" + result)
    if result != VERIFIED_RESULT:
        return 4
    try:
        _secure_save(entries, path=DOTENV)
    except (OSError, ValueError):
        print("NAVIMIND_V2_SETUP=save_failed")
        return 3
    print("NAVIMIND_V2_SETUP=saved_to_private_env")
    print("NAVIMIND_V2_HTTP_VERIFIED=True")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true")
    args = parser.parse_args(argv)
    if args.setup:
        return setup_v2()
    result = probe_v2()
    print("V2_READ_ONLY_NETWORK_CHECK=True")
    print("V2_PROBE_RESULT=" + result)
    print("NAVIMIND_V2_HTTP_VERIFIED=" + str(result == VERIFIED_RESULT))
    print("V2_NATIVE_INPUT=False")
    print("V2_CUSTOMER_DATA_TRANSMITTED=False")
    print("V2_REAL_REASONING_REQUEST=False")
    return 0 if result == VERIFIED_RESULT else 4


if __name__ == "__main__":
    raise SystemExit(main())

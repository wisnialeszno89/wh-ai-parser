"""Local NaviMind V2 configuration self-check, without network or GUI access.

Print only presence/validity diagnostics; never print URLs, access tokens,
secrets, customer data, or contents of private .env files.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def evaluate_navimind_setup(values: dict[str, str], *, env_file_present: bool = False) -> dict[str, str]:
    """Analyze configuration without leaking user-provided values."""
    v1 = (values.get("NAVIMIND_AGENT_URL") or "").strip()
    v2 = (values.get("NAVIMIND_AGENT_V2_URL") or "").strip()
    shared_secret = (values.get("NAVIMIND_AGENT_SECRET") or "").strip()
    v2_secret = (values.get("NAVIMIND_AGENT_V2_SECRET") or "").strip()

    def status(url: str) -> str:
        if not url:
            return "missing"
        try:
            parsed = urlsplit(url)
            if parsed.username is not None or parsed.password is not None:
                return "invalid_embedded_credentials"
            if parsed.query or parsed.fragment:
                return "invalid_query_or_fragment"
            if parsed.path.rstrip("/") != "/api/agent/task":
                return "wrong_endpoint_path"
            if not parsed.hostname:
                return "missing_host"
            if parsed.scheme == "https":
                return "format_valid"
            if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}:
                return "format_valid_local_only"
        except ValueError:
            return "malformed"
        return "not_secure_https"

    shared = status(v1)
    dedicated = status(v2)
    if shared.startswith("format_valid") and shared_secret:
        next_action = "deploy_navimind_v2_then_use_existing_shared_endpoint"
    elif dedicated.startswith("format_valid") and v2_secret:
        next_action = "deploy_navimind_v2_then_use_dedicated_config"
    elif not v1 and not v2:
        next_action = "configure_navimind_deployment_origin_and_auth_in_local_env"
    elif not shared_secret and not v2_secret:
        next_action = "configure_matching_navimind_secret_locally_and_on_server"
    elif shared == "wrong_endpoint_path" or dedicated == "wrong_endpoint_path":
        next_action = "use_exact_path_api_agent_task_on_existing_deployment"
    else:
        next_action = "fix_url_or_secret_configuration_before_reasoning"

    return {
        "DOTENV_FILE": "present" if env_file_present else "absent",
        "V1_URL": shared,
        "V1_SECRET": "set" if shared_secret else "missing",
        "V2_URL": dedicated,
        "V2_SECRET": "set" if v2_secret else "missing",
        "V2_SERVER_DEPLOYED": "not_verified",
        "NEXT_ACTION": next_action,
    }


def main() -> int:
    env_path = ROOT / ".env"
    load_dotenv(dotenv_path=env_path)
    data = evaluate_navimind_setup(
        {k: os.getenv(k, "") for k in (
            "NAVIMIND_AGENT_URL", "NAVIMIND_AGENT_SECRET",
            "NAVIMIND_AGENT_V2_URL", "NAVIMIND_AGENT_V2_SECRET",
        )},
        env_file_present=env_path.is_file(),
    )
    for key, value in data.items():
        print(f"{key}={value}")
    print("PROTOCOL_V2_ENDPOINT=/api/agent/task")
    print("DEPLOY_REQUIRED=NaviMind PR #26 must be merged and deployed before remote V2 reasoning.")
    print("SECRET_POLICY=Never paste secrets, keys, tokens or .env file contents into chat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

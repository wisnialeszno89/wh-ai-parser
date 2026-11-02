"""HTTP client for the isolated NaviMind Agent Observe/Act protocol v2.

The V2 client deliberately returns a validated V2 decision mapping. It does not
translate V2 decisions into V1 ReasoningProposal/ReasoningAction objects.
Local brokers and the runtime remain responsible for observations and actions.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agent.bridge.agent_task_contract_v2 import (
    AgentTaskV2Contract,
    MAX_BODY_BYTES,
    validate_agent_task_v2_payload,
    validate_agent_task_v2_response,
)
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasonerConfig,
)


MAX_RESPONSE_BYTES = 64 * 1024


class NaviMindTaskReasonerV2:
    """Send one V2 reasoning cycle and validate its single returned decision."""

    def __init__(
        self,
        *,
        config: NaviMindTaskReasonerConfig | None = None,
        opener: Callable = urlopen,
    ) -> None:
        self.config = (
            config
            if config is not None
            else NaviMindTaskReasonerConfig.from_environment()
        )
        self.opener = opener
        self.last_error: str | None = None

    def reason(
        self,
        request: AgentTaskV2Contract | Mapping[str, object],
    ) -> dict[str, object] | None:
        """Return one validated V2 response, or None on any boundary failure."""
        self.last_error = None

        try:
            payload = (
                request.to_payload()
                if isinstance(request, AgentTaskV2Contract)
                else dict(request)
            )
            validate_agent_task_v2_payload(payload)
            body = json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except Exception as exc:
            self.last_error = f"invalid_v2_request:{type(exc).__name__}"
            return None

        if len(body) > MAX_BODY_BYTES:
            self.last_error = "navimind_v2_request_too_large"
            return None

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.secret:
            headers["x-navimind-agent-secret"] = self.config.secret

        http_request = Request(
            self.config.url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with self.opener(
                http_request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            self.last_error = f"navimind_http_{exc.code}"
            return None
        except URLError as exc:
            self.last_error = f"navimind_connection_error:{type(exc.reason).__name__}"
            return None
        except Exception as exc:
            self.last_error = f"navimind_transport_error:{type(exc).__name__}"
            return None

        if not isinstance(raw, (bytes, bytearray)):
            self.last_error = "invalid_navimind_v2_response_body"
            return None
        if len(raw) > MAX_RESPONSE_BYTES:
            self.last_error = "navimind_v2_response_too_large"
            return None

        try:
            response_payload = json.loads(bytes(raw).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.last_error = "invalid_navimind_v2_json"
            return None

        if not isinstance(response_payload, dict):
            self.last_error = "invalid_navimind_v2_response"
            return None

        try:
            validate_agent_task_v2_response(
                response_payload,
                payload,
            )
        except (TypeError, ValueError) as exc:
            self.last_error = f"invalid_navimind_v2_decision:{str(exc)[:180]}"
            return None

        return response_payload

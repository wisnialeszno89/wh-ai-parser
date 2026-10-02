from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agent.reasoning.navimind_config import (
    NaviMindConfig,
)
from app.agent.reasoning.navimind_contract import (
    NaviMindActionResponse,
    NaviMindReasoningResponse,
    NaviMindTaskContract,
)


class NaviMindClientError(RuntimeError):
    """Base error for communication or contract failures."""


@dataclass(frozen=True)
class NaviMindClient:
    config: NaviMindConfig

    def reason(
        self,
        task: NaviMindTaskContract,
    ) -> NaviMindReasoningResponse:
        payload = json.dumps(
            task.to_payload(),
            ensure_ascii=False,
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "wh-ai-parser/navigating-agent-bridge"
            ),
        }

        if self.config.secret:
            headers[
                "x-navimind-agent-secret"
            ] = self.config.secret

        request = Request(
            self.config.url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read().decode(
                    "utf-8"
                )
        except HTTPError as exc:
            details = ""

            try:
                details = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                details = ""

            raise NaviMindClientError(
                "NaviMind request failed with "
                f"HTTP {exc.code}: {details[:500]}"
            ) from exc
        except URLError as exc:
            raise NaviMindClientError(
                "NaviMind request could not be sent: "
                f"{exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise NaviMindClientError(
                "NaviMind request timed out."
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NaviMindClientError(
                "NaviMind returned invalid JSON."
            ) from exc

        return self._parse_response(data)

    def _parse_response(
        self,
        data: object,
    ) -> NaviMindReasoningResponse:
        if not isinstance(data, dict):
            raise NaviMindClientError(
                "NaviMind response is not an object."
            )

        version = str(
            data.get("version", "")
        ).strip()

        task_id = str(
            data.get("task_id", "")
        ).strip()

        status = str(
            data.get("status", "")
        ).strip()

        rationale = str(
            data.get("rationale", "")
        )

        confidence = self._safe_confidence(
            data.get("confidence")
        )

        if version != "1":
            raise NaviMindClientError(
                "Unsupported NaviMind response version: "
                f"{version!r}"
            )

        if status not in {
            "continue",
            "done",
            "manual_review",
        }:
            raise NaviMindClientError(
                "Invalid NaviMind response status: "
                f"{status!r}"
            )

        if not task_id:
            raise NaviMindClientError(
                "NaviMind response is missing task_id."
            )

        raw_action = data.get("action")
        action = None

        if raw_action is not None:
            if not isinstance(
                raw_action,
                dict,
            ):
                raise NaviMindClientError(
                    "NaviMind action is not an object."
                )

            name = str(
                raw_action.get("name", "")
            ).strip()

            description = str(
                raw_action.get(
                    "description",
                    "",
                )
            ).strip()

            if not name or not description:
                raise NaviMindClientError(
                    "NaviMind action is missing "
                    "name or description."
                )

            action = NaviMindActionResponse(
                name=name,
                description=description,
                target=self._optional_string(
                    raw_action.get("target")
                ),
                value=self._optional_string(
                    raw_action.get("value")
                ),
                requires_confirmation=bool(
                    raw_action.get(
                        "requires_confirmation",
                        False,
                    )
                ),
            )

        if status == "continue" and action is None:
            raise NaviMindClientError(
                "NaviMind requested continuation "
                "without an action."
            )

        raw_metadata = data.get("metadata")

        metadata = (
            dict(raw_metadata)
            if isinstance(
                raw_metadata,
                dict,
            )
            else {}
        )

        requires_manual_review = (
            status == "manual_review"
            or bool(
                data.get(
                    "requires_manual_review",
                    False,
                )
            )
        )

        return NaviMindReasoningResponse(
            version=version,
            task_id=task_id,
            status=status,
            rationale=rationale,
            confidence=confidence,
            action=action,
            requires_manual_review=(
                requires_manual_review
            ),
            metadata=metadata,
        )

    @staticmethod
    def _optional_string(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _safe_confidence(
        value: object,
    ) -> float:
        try:
            numeric = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        return max(
            0.0,
            min(1.0, numeric),
        )

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from typing import Any

from pydantic import BaseModel, Field

from app.agent.reasoning.plan_reasoner import (
    PlanReasoner,
)

from app.agent.reasoning.replanning_context import (
    ReplanningContext,
)

from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)

from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)


class _OpenAIReasoningAction(BaseModel):
    name: str
    description: str
    target: str | None = None
    requires_confirmation: bool = False


class _OpenAIReasoningProposal(BaseModel):
    actions: list[_OpenAIReasoningAction]
    rationale: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    requires_manual_review: bool = False


@dataclass(frozen=True)
class OpenAIPlanReasonerConfig:
    """
    Configuration for the OpenAI-backed PlanReasoner.

    The API key should normally come from OPENAI_API_KEY.
    The model can be changed through AGENT_REASONING_MODEL.
    """

    api_key: str
    model: str = "gpt-5.6-luna"

    @classmethod
    def from_environment(
        cls,
        *,
        model: str | None = None,
    ) -> "OpenAIPlanReasonerConfig":
        load_dotenv()

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        return cls(
            api_key=api_key,
            model=(
                model
                or os.getenv(
                    "AGENT_REASONING_MODEL",
                    "gpt-5.6-luna",
                )
            ),
        )


class OpenAIPlanReasoner(
    PlanReasoner
):
    """
    OpenAI Responses API implementation of PlanReasoner.

    The model may propose semantic recovery actions only.
    It never receives executor objects or low-level GUI
    control primitives.
    """

    SYSTEM_INSTRUCTIONS = """
You are the reasoning component of a universal computer-use agent.

Your task is to recover from a failed verification cycle by
proposing a safer semantic continuation of the task.

Rules:
- Return only semantic actions.
- Never return mouse coordinates, keyboard commands, pyautogui calls,
  automation library calls, executor names, or direct GUI instructions.
- Do not assume that a target exists when the observed scene says it
  does not.
- Prefer small, reversible recovery steps.
- Preserve the user's original intent.
- Use manual review when the state is ambiguous or unsafe.
- Do not claim that an action was executed; you are proposing a plan.
- Confidence must reflect uncertainty.
""".strip()

    def __init__(
        self,
        *,
        config: OpenAIPlanReasonerConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else OpenAIPlanReasonerConfig.from_environment()
        )

        if client is None:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.config.api_key
            )

        self.client = client

    def reason(
        self,
        context: ReplanningContext,
    ) -> ReasoningProposal | None:
        try:
            response = self.client.responses.parse(
                model=self.config.model,
                instructions=self.SYSTEM_INSTRUCTIONS,
                input=json.dumps(
                    context.to_payload(),
                    ensure_ascii=False,
                ),
                text_format=_OpenAIReasoningProposal,
            )
        except Exception:
            # Fail closed. Runtime fallback remains responsible for
            # stopping or requesting manual review.
            return None

        parsed = getattr(
            response,
            "output_parsed",
            None,
        )

        if parsed is None:
            return None

        if not isinstance(
            parsed,
            _OpenAIReasoningProposal,
        ):
            return None

        return ReasoningProposal(
            actions=tuple(
                ReasoningAction(
                    name=action.name,
                    description=action.description,
                    target=action.target,
                    requires_confirmation=(
                        action.requires_confirmation
                    ),
                )
                for action in parsed.actions
            ),
            rationale=parsed.rationale,
            confidence=parsed.confidence,
            requires_manual_review=(
                parsed.requires_manual_review
            ),
        )

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)
from app.agent.reasoning.reasoning_proposal import (
    ReasoningProposal,
)
from app.agent.reasoning.task_planning_context import (
    TaskPlanningContext,
)
from app.agent.reasoning.task_reasoner import (
    TaskReasoner,
)


class _OpenAITaskReasoningAction(BaseModel):
    name: str
    description: str
    target: str | None = None
    requires_confirmation: bool = False


class _OpenAITaskReasoningProposal(BaseModel):
    actions: list[_OpenAITaskReasoningAction]
    rationale: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    requires_manual_review: bool = False


@dataclass(frozen=True)
class OpenAITaskReasonerConfig:
    """
    Configuration for the OpenAI-backed TaskReasoner.
    """

    api_key: str
    model: str = "gpt-5.6-luna"

    @classmethod
    def from_environment(
        cls,
        *,
        model: str | None = None,
    ) -> "OpenAITaskReasonerConfig":
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
                    "AGENT_TASK_REASONING_MODEL",
                    os.getenv(
                        "AGENT_REASONING_MODEL",
                        "gpt-5.6-luna",
                    ),
                )
            ),
        )


class OpenAITaskReasoner(TaskReasoner):
    """
    OpenAI Responses API implementation for initial task planning.

    The model proposes semantic actions only. Execution remains
    entirely outside the model.
    """

    SYSTEM_INSTRUCTIONS = """
You are the initial task-planning component of a universal computer-use agent.

Your job is to convert the user's natural-language request into a small,
semantic action plan that the runtime can execute safely.

Rules:
- Return only semantic actions.
- A target may be a human-readable UI label or other semantic identifier.
- Never return mouse coordinates, screen coordinates, window handles,
  runtime ids, automation ids, tracked object ids, keyboard commands,
  pyautogui calls, automation-library calls, executor names, or low-level
  GUI instructions.
- Prefer the smallest useful plan that directly serves the user's intent.
- Do not invent facts that are not supported by the request or supplied
  capability/skill context.
- When essential information is missing or the request is ambiguous,
  set requires_manual_review=true instead of guessing.
- Do not claim that actions were executed; you are proposing a plan.
- Confidence must reflect uncertainty.
""".strip()

    def __init__(
        self,
        *,
        config: OpenAITaskReasonerConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else OpenAITaskReasonerConfig.from_environment()
        )

        if client is None:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.config.api_key
            )

        self.client = client

    def reason(
        self,
        context: TaskPlanningContext,
    ) -> ReasoningProposal | None:
        try:
            response = self.client.responses.parse(
                model=self.config.model,
                instructions=self.SYSTEM_INSTRUCTIONS,
                input=json.dumps(
                    context.to_payload(),
                    ensure_ascii=False,
                ),
                text_format=(
                    _OpenAITaskReasoningProposal
                ),
            )
        except Exception:
            return None

        parsed = getattr(
            response,
            "output_parsed",
            None,
        )

        if not isinstance(
            parsed,
            _OpenAITaskReasoningProposal,
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

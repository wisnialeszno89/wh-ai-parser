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
    value: str | None = None
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
- For write_text actions, set target to the visible semantic field label and
  value to the exact text that should be entered.
- Never return mouse coordinates, screen coordinates, window handles,
  runtime ids, automation ids, tracked object ids, raw keyboard commands,
  pyautogui calls, automation-library calls, executor names, or low-level
  GUI instructions.
- The input may include a current semantic scene captured immediately
  before planning. Treat it as observed evidence of the visible UI state.
- Use visible element labels, kinds, interaction capabilities and any
  supplied current_value to decide whether an action is appropriate.
  If the requested value is already present in a field, do not write it
  again unless the task explicitly requires replacing it.
- When a scene is provided, an action target must be a visible element
  label from that scene (case-insensitive) unless no target is needed.
- Never use or invent technical identifiers such as AutomationId values,
  runtime ids, provider element ids, tracked object ids or other internal
  identifiers as action targets, even if they seem predictable.
- If the requested target cannot be expressed using a visible semantic
  label from the scene, set requires_manual_review=true rather than
  guessing an internal identifier.
- If application knowledge is provided, treat it as domain guidance for
  interpreting the application's workflow, field roles and safe sequence.
  It does not override the observed scene: actual visible controls in the
  current scene remain authoritative.
- If offer workflow state is provided, treat it as authoritative
  semantic workflow context for quotation tasks.
- If workflow data is incomplete but the user's request itself contains
  the missing value, use that value to plan the required visible GUI action,
  such as write_text or click_screen_element. Do not ask the salesperson
  to repeat information already present in request_message.
- If a required business value is missing from both the workflow data and
  request_message, set requires_manual_review=true.
- If workflow_state is READY_FOR_PRICING, the business workflow steps
  are already complete. Do NOT return analyze_request,
  collect_offer_context, validate_offer, build_construction or
  prepare_quote. Instead, choose only the next safe user-visible GUI
  action required to continue the current WindowHub workflow.
- If continuation_of_offer is true, the current offer must be continued,
  not restarted. Never select a reset/navigation action such as
  "NOWA OFERTA" / "Nowa oferta" or the semantic action open_new_offer.
- For a READY_FOR_PRICING task, prefer one small semantic GUI action,
  normally click_screen_element with a visible target from the current
  scene. Never guess the target.
- Prefer the next safe user-visible GUI action when continuing a
  READY_FOR_PRICING workflow.
- Use application workflow knowledge to recognize which stage the current
  WindowHub scene most likely represents, but do not assume a control exists
  until the scene contains a matching semantic target.
- If no clear visible control safely represents the next step,
  set requires_manual_review=true.
- If the requested goal is already represented by the current workflow
  state and observed scene, do not repeat the navigation step.
- If the requested UI state is not supported by the observed scene and
  the task cannot be planned safely without guessing, set
  requires_manual_review=true.
- Never infer coordinates or provider/runtime identifiers from the scene.
- Prefer the smallest useful plan that directly serves the user's intent.
- Do not invent facts that are not supported by the request, supplied
  capability/skill context, or observed semantic scene.
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
        self.last_error: str | None = None

    def reason(
        self,
        context: TaskPlanningContext,
    ) -> ReasoningProposal | None:
        self.last_error = None

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
        except Exception as exc:
            self.last_error = (
                f"{type(exc).__name__}: {exc}"
            )
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
            self.last_error = "provider_returned_no_parsed_proposal"
            return None

        return ReasoningProposal(
            actions=tuple(
                ReasoningAction(
                    name=action.name,
                    description=action.description,
                    target=action.target,
                    value=action.value,
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

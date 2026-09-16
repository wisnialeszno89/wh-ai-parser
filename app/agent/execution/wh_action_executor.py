from app.agent.agent_action import AgentAction

from app.agent.offers.offer_context import OfferContext
from app.agent.offers.offer_context_validator import OfferContextValidator
from app.agent.offers.offer_construction_resolver import (
    OfferConstructionResolver,
)

from app.agent.execution.action_executor import (
    ActionExecutor,
)

from app.agent.execution.execution_result import (
    ExecutionResult,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


class WHActionExecutor(ActionExecutor):
    """
    Controlled executor for WH-related semantic actions.

    This executor acts as an adapter between the generic agent
    execution layer and WH workflows.

    Semantic actions can enrich the shared execution context.
    Real WH runtime integration will later be connected behind
    the same interface.
    """

    SUPPORTED_ACTIONS = {
        "analyze_request",
        "collect_offer_context",
        "validate_offer",
        "build_construction",
        "prepare_quote",
    }

    def supports(
        self,
        action: AgentAction,
    ) -> bool:
        return action.name in self.SUPPORTED_ACTIONS

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        if action.name == "analyze_request":
            return self._analyze_request(
                action,
                context,
            )

        if action.name == "collect_offer_context":
            return self._collect_offer_context(
                action,
                context,
            )

        if action.name == "validate_offer":
            return self._validate_offer(
                action,
                context,
            )

        if action.name == "build_construction":
            return self._build_construction(
                action,
                context,
            )

        if action.name == "prepare_quote":
            return self._prepare_quote(
                action,
                context,
            )

        return ExecutionResult(
            action_name=action.name,
            success=False,
            message=(
                "Unsupported WH action: "
                f"{action.name}"
            ),
            requires_manual_review=True,
        )

    def _analyze_request(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        context.set_value(
            "request_analyzed",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                "WH request analysis completed."
            ),
            metadata={
                "workflow_stage":
                    "request_analysis",
            },
        )

    def _collect_offer_context(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        offer_context = context.get_value(
            "offer_context"
        )

        if offer_context is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "Offer context is missing."
                ),
                requires_manual_review=True,
                metadata={
                    "workflow_stage":
                        "offer_context",
                    "reason":
                        "missing_offer_context",
                },
            )

        context.set_value(
            "offer_context_collected",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                "Offer context collection completed."
            ),
            metadata={
                "workflow_stage":
                    "offer_context",
            },
        )

    def _validate_offer(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        context.set_value(
            "offer_validated",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                "Offer validation completed."
            ),
            metadata={
                "workflow_stage":
                    "validation",
            },
        )

    def _build_construction(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        offer_context = context.get_value(
            "offer_context"
        )

        if offer_context is None:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "Offer context is missing."
                ),
                requires_manual_review=True,
                metadata={
                    "workflow_stage":
                        "construction",
                    "reason":
                        "missing_offer_context",
                },
            )

        if not isinstance(
            offer_context,
            OfferContext,
        ):
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "Invalid offer context."
                ),
                requires_manual_review=True,
                metadata={
                    "workflow_stage":
                        "construction",
                    "reason":
                        "invalid_offer_context",
                },
            )

        validation = OfferContextValidator().validate(
            offer_context
        )

        if not validation.is_valid:
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "Offer context validation failed."
                ),
                requires_manual_review=True,
                metadata={
                    "workflow_stage":
                        "construction",
                    "reason":
                        "invalid_offer_context",
                    "missing_fields":
                        validation.missing_fields,
                    "conflicts":
                        validation.conflicts,
                },
            )

        construction_definition = (
            OfferConstructionResolver().resolve(
                offer_context
            )
        )

        if (
            offer_context.opening is not None
            and construction_definition is None
        ):
            return ExecutionResult(
                action_name=action.name,
                success=False,
                message=(
                    "Construction could not be resolved "
                    "from the offer context."
                ),
                requires_manual_review=True,
                metadata={
                    "workflow_stage":
                        "construction",
                    "reason":
                        "construction_not_resolved",
                    "opening":
                        offer_context.opening,
                },
            )

        context.set_value(
            "offer_validated",
            True,
        )

        if construction_definition is not None:
            context.set_value(
                "construction_definition",
                construction_definition,
            )

        context.set_value(
            "construction_build_started",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                "Construction build workflow completed."
            ),
            metadata={
                "workflow_stage":
                    "construction",
            },
        )

    def _prepare_quote(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:

        context.set_value(
            "quote_prepared",
            True,
        )

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                "Quotation preparation completed."
            ),
            requires_manual_review=True,
            metadata={
                "workflow_stage":
                    "quotation",
                "confirmation_required":
                    True,
            },
        )

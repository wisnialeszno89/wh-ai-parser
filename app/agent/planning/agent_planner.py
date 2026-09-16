import re

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep


class AgentPlanner:
    """
    Converts a salesman request into a semantic action plan.

    This layer intentionally does not execute GUI actions.
    It only decides WHAT should happen.
    """

    QUOTE_KEYWORDS = (
        "wycena",
        "wycenę",
        "wyceny",
        "wycenić",
        "wycenic",
        "oferta",
        "ofertę",
        "oferty",
        "przygotuj ofertę",
        "przygotuj oferte",
        "zrób ofertę",
        "zrob ofertę",
        "zrob oferte",
    )

    TECHNICAL_KEYWORDS = (
        "techniczne",
        "techniczny",
        "czy można",
        "czy mozna",
        "parametry",
        "profil",
        "szyba",
        "okucie",
        "okucia",
    )

    COMPARE_KEYWORDS = (
        "porównaj",
        "porownaj",
        "porównanie",
        "porownanie",
        "różnica",
        "roznica",
        "wariant",
        "warianty",
    )

    CUSTOMER_REPLY_KEYWORDS = (
        "odpowiedz klientowi",
        "napisz do klienta",
        "odpowiedź dla klienta",
        "odpowiedz dla klienta",
        "mail do klienta",
        "email do klienta",
    )

    MARKET_KEYWORDS = (
        "ceny rynku",
        "cena rynkowa",
        "sprawdź ceny",
        "sprawdz ceny",
        "rynek",
        "konkurencja",
    )

    OBSERVE_KEYWORDS = (
        "obserwuj",
        "obserwacja",
        "sprawdź jak pracuję",
        "sprawdz jak pracuje",
        "pomóż mi pracować",
        "pomoz mi pracowac",
    )

    HELP_KEYWORDS = (
        "pomoc",
        "pomóż",
        "pomoz",
        "co potrafisz",
        "jak możesz pomóc",
        "jak mozesz pomoc",
    )

    def _looks_like_quote_request(
        self,
        message: str,
    ) -> bool:
        """
        Detect a quotation request from explicit
        product and dimensional information.

        This deliberately does not treat a generic
        product word such as "okno" as a quotation
        request by itself.
        """

        has_window_product = any(
            term in message
            for term in (
                "okno",
                "okna",
                "fenster",
                "window",
                "windows",
            )
        )

        has_dimensions = (
            re.search(
                r"\b\d{2,5}\s*[x×]\s*\d{2,5}\b",
                message,
            )
            is not None
        )

        return (
            has_window_product
            and has_dimensions
        )

    def detect_intent(
        self,
        request: AgentRequest,
    ) -> AgentIntent:

        message = request.message.lower()

        if request.metadata.get(
            "continuation_of_offer"
        ) is True:
            return AgentIntent.CREATE_QUOTE

        if any(
            keyword in message
            for keyword in self.QUOTE_KEYWORDS
        ):
            return AgentIntent.CREATE_QUOTE

        if self._looks_like_quote_request(
            message
        ):
            return AgentIntent.CREATE_QUOTE

        if any(
            keyword in message
            for keyword in self.TECHNICAL_KEYWORDS
        ):
            return AgentIntent.CHECK_TECHNICAL

        if any(
            keyword in message
            for keyword in self.COMPARE_KEYWORDS
        ):
            return AgentIntent.COMPARE_VARIANTS

        if any(
            keyword in message
            for keyword in self.CUSTOMER_REPLY_KEYWORDS
        ):
            return AgentIntent.WRITE_CUSTOMER_REPLY

        if any(
            keyword in message
            for keyword in self.MARKET_KEYWORDS
        ):
            return AgentIntent.CHECK_MARKET

        if any(
            keyword in message
            for keyword in self.OBSERVE_KEYWORDS
        ):
            return AgentIntent.OBSERVE_WORKFLOW

        if any(
            keyword in message
            for keyword in self.HELP_KEYWORDS
        ):
            return AgentIntent.HELP

        return AgentIntent.UNKNOWN

    def plan(
        self,
        request: AgentRequest,
    ) -> ActionPlan:

        intent = self.detect_intent(request)

        if intent == AgentIntent.CREATE_QUOTE:
            return ActionPlan(
                intent=intent,
                confidence=1.0,
                requires_manual_review=False,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="analyze_request",
                            description=(
                                "Analyze salesman request "
                                "and extract quotation intent."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="collect_offer_context",
                            description=(
                                "Collect technical, dimensional "
                                "and commercial offer context."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=3,
                        action=AgentAction(
                            name="validate_offer",
                            description=(
                                "Validate collected offer context "
                                "and detect missing or conflicting data."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=4,
                        action=AgentAction(
                            name="build_construction",
                            description=(
                                "Build or select the appropriate "
                                "window construction based on the "
                                "validated offer context."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=5,
                        action=AgentAction(
                            name="prepare_quote",
                            description=(
                                "Prepare quotation workflow "
                                "for controlled execution."
                            ),
                            requires_confirmation=True,
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.CHECK_TECHNICAL:
            return ActionPlan(
                intent=intent,
                confidence=0.85,
                requires_manual_review=False,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="analyze_technical_question",
                            description=(
                                "Analyze the technical question."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="check_technical_knowledge",
                            description=(
                                "Check product, construction "
                                "and technical knowledge."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=3,
                        action=AgentAction(
                            name="prepare_technical_answer",
                            description=(
                                "Prepare a clear technical answer "
                                "for the salesman."
                            ),
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.COMPARE_VARIANTS:
            return ActionPlan(
                intent=intent,
                confidence=0.85,
                requires_manual_review=False,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="identify_variants",
                            description=(
                                "Identify variants to compare."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="compare_variants",
                            description=(
                                "Compare technical and commercial "
                                "differences."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=3,
                        action=AgentAction(
                            name="prepare_comparison",
                            description=(
                                "Prepare a concise comparison "
                                "for the salesman."
                            ),
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.WRITE_CUSTOMER_REPLY:
            return ActionPlan(
                intent=intent,
                confidence=0.8,
                requires_manual_review=True,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="analyze_customer_context",
                            description=(
                                "Analyze customer request "
                                "and available offer context."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="draft_customer_reply",
                            description=(
                                "Prepare a customer-ready response."
                            ),
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.CHECK_MARKET:
            return ActionPlan(
                intent=intent,
                confidence=0.75,
                requires_manual_review=True,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="define_market_query",
                            description=(
                                "Determine what market information "
                                "is required."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="research_market",
                            description=(
                                "Research current market information."
                            ),
                        ),
                        ),
                    ActionStep(
                        index=3,
                        action=AgentAction(
                            name="prepare_market_summary",
                            description=(
                                "Prepare findings and clearly "
                                "separate facts from estimates."
                            ),
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.OBSERVE_WORKFLOW:
            return ActionPlan(
                intent=intent,
                confidence=0.8,
                requires_manual_review=False,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="observe_workflow",
                            description=(
                                "Observe the salesman workflow "
                                "and collect useful context."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=2,
                        action=AgentAction(
                            name="identify_repetitive_tasks",
                            description=(
                                "Identify repetitive tasks that "
                                "can potentially be automated."
                            ),
                        ),
                    ),
                    ActionStep(
                        index=3,
                        action=AgentAction(
                            name="suggest_assistance",
                            description=(
                                "Suggest or prepare assistance "
                                "for the current workflow."
                            ),
                        ),
                    ),
                ),
            )

        if intent == AgentIntent.HELP:
            return ActionPlan(
                intent=intent,
                confidence=1.0,
                requires_manual_review=False,
                steps=(
                    ActionStep(
                        index=1,
                        action=AgentAction(
                            name="explain_capabilities",
                            description=(
                                "Explain current agent capabilities "
                                "and available workflows."
                            ),
                        ),
                    ),
                ),
            )

        return ActionPlan(
            intent=AgentIntent.UNKNOWN,
            confidence=0.0,
            requires_manual_review=True,
            steps=(),
        )

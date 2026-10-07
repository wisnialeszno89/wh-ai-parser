from __future__ import annotations

from app.agent.agent_action import AgentAction


class BrowserActionRiskPolicy:
    """Local fail-closed risk classification for semantic browser actions.

    Model output cannot lower the risk of a known high-impact browser target.
    This policy is intentionally narrow: it protects common irreversible or
    externally visible click targets while leaving ordinary navigation and
    workflow controls available for autonomous execution.
    """

    HIGH_IMPACT_TERMS = (
        "zatwierdź",
        "zatwierdz",
        "potwierdź",
        "potwierdz",
        "wyślij",
        "wyslij",
        "usuń",
        "usun",
        "skasuj",
        "opublikuj",
        "kup",
        "zapłać",
        "zaplac",
        "wystaw",
        "zamów",
        "zamow",
        "anuluj",
        "usuń",
        "delete",
        "submit",
        "confirm",
        "send",
        "publish",
        "purchase",
        "pay",
        "cancel",
    )

    @classmethod
    def requires_confirmation(
        cls,
        action: AgentAction,
    ) -> bool:
        if action.name != "browser_click":
            return False

        values = (
            action.target,
            action.description,
        )

        normalized = " ".join(
            value.strip().casefold()
            for value in values
            if isinstance(value, str) and value.strip()
        )

        return any(
            term in normalized
            for term in cls.HIGH_IMPACT_TERMS
        )

    @classmethod
    def evaluate(
        cls,
        action: AgentAction,
    ) -> tuple[bool, str | None]:
        if not cls.requires_confirmation(action):
            return False, None

        return (
            True,
            "Local browser risk policy requires explicit confirmation "
            "for this high-impact action.",
        )

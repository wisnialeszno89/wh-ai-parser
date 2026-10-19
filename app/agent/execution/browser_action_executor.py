from __future__ import annotations

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_action import AgentAction
from app.agent.execution.action_executor import ActionExecutor
from app.agent.execution.execution_result import ExecutionResult
from app.agent.runtime.execution_context import ExecutionContext


class BrowserActionExecutor(ActionExecutor):
    """
    Controlled executor for semantic browser actions.

    Technical browser selectors, handles and provider runtime objects stay
    behind BrowserAdapter/BrowserProvider. The executor accepts only semantic
    action names and visible element labels.
    """

    SUPPORTED_ACTIONS = {
        "browser_navigate",
        "browser_read",
        "browser_click",
        "browser_write_text",
        "browser_select_option",
        "browser_back",
    }

    _FORBIDDEN_LOW_LEVEL_TERMS = (
        "css=",
        "xpath=",
        "xpath:",
        "locator(",
        "queryselector",
        "query_selector",
        "browser_handle",
        "page_handle",
        "element_handle",
        "runtime_id",
        "automation_id",
        "selector:",
        "selector=",
    )

    _TECHNICAL_TARGET_PREFIXES = (
        "idc_",
        "uia:",
        "automationid:",
        "automation_id=",
        "runtimeid:",
        "runtime_id=",
        "tracked_object:",
        "tracked_object_id=",
    )

    def __init__(self, browser_adapter: BrowserAdapter) -> None:
        if not isinstance(browser_adapter, BrowserAdapter):
            raise TypeError(
                "BrowserActionExecutor requires BrowserAdapter."
            )

        self.browser_adapter = browser_adapter

    def supports(self, action: AgentAction) -> bool:
        return (
            action.name in self.SUPPORTED_ACTIONS
            and self.browser_adapter.is_available()
        )

    def execute(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        if action.name not in self.SUPPORTED_ACTIONS:
            return self._failure(
                action,
                "Unsupported browser action.",
                manual_review=True,
            )

        if not self.browser_adapter.is_available():
            return self._failure(
                action,
                "Browser adapter is unavailable.",
                manual_review=True,
            )

        try:
            if action.name == "browser_navigate":
                return self._navigate(action, context)

            if action.name == "browser_read":
                return self._read(action, context)

            if action.name == "browser_click":
                return self._click(action, context)

            if action.name == "browser_write_text":
                return self._write_text(action, context)

            if action.name == "browser_select_option":
                return self._select_option(action, context)

            if action.name == "browser_back":
                return self._back(action, context)

            return self._failure(
                action,
                "Unsupported browser action.",
                manual_review=True,
            )
        except (TypeError, ValueError, PermissionError) as exc:
            return self._failure(
                action,
                str(exc),
                manual_review=False,
            )

    def _navigate(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        url = self._required_value(
            action,
            "browser_navigate requires a URL value.",
        )

        if self._contains_low_level_value(url):
            return self._failure(
                action,
                "Browser navigation value contains a forbidden technical locator.",
                manual_review=False,
            )

        page = self.browser_adapter.open(url)
        return self._success(
            action,
            context,
            page,
            operation="navigate",
            executed=not self.browser_adapter.dry_run,
        )

    def _read(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        page = self.browser_adapter.read()
        return self._success(
            action,
            context,
            page,
            operation="read",
            executed=False,
        )

    def _click(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        target = self._resolve_target(
            action,
            context,
            capability="CLICKABLE",
        )

        page = self.browser_adapter.click(target)
        return self._success(
            action,
            context,
            page,
            operation="click",
            target=target.label,
            executed=not self.browser_adapter.dry_run,
        )

    def _write_text(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        value = self._required_value(
            action,
            "browser_write_text requires a text value.",
        )

        target = self._resolve_target(
            action,
            context,
            capability="EDITABLE",
        )

        page = self.browser_adapter.write_text(
            target,
            value,
        )
        return self._success(
            action,
            context,
            page,
            operation="write_text",
            target=target.label,
            executed=not self.browser_adapter.dry_run,
        )

    def _select_option(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        value = self._required_value(
            action,
            "browser_select_option requires an option value.",
        )

        target = self._resolve_target(
            action,
            context,
            capability="SELECTABLE",
        )

        page = self.browser_adapter.select_option(
            target,
            value,
        )
        return self._success(
            action,
            context,
            page,
            operation="select_option",
            target=target.label,
            executed=not self.browser_adapter.dry_run,
        )

    def _back(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionResult:
        page = self.browser_adapter.back()
        return self._success(
            action,
            context,
            page,
            operation="back",
            executed=not self.browser_adapter.dry_run,
        )

    def _resolve_target(
        self,
        action: AgentAction,
        context: ExecutionContext,
        *,
        capability: str,
    ) -> BrowserElement:
        target = (
            action.target.strip()
            if isinstance(action.target, str)
            else ""
        )

        if not target:
            return self._target_failure(
                "Browser action requires a semantic target."
            )

        if self._contains_low_level_value(target):
            return self._target_failure(
                "Browser target contains a forbidden technical locator."
            )

        page = context.get_value("browser_page")
        if not isinstance(page, BrowserPage):
            page = self.browser_adapter.read()
            context.set_value("browser_page", page)

        candidates = [
            element
            for element in page.elements
            if (
                isinstance(element.label, str)
                and element.label.strip().casefold()
                == target.casefold()
                and (
                    element.interaction_capability
                    .strip()
                    .upper()
                    == capability
                )
            )
        ]

        if not candidates:
            self._target_failure(
                f"No visible browser target matched '{target}'."
            )

        if len(candidates) > 1:
            self._target_failure(
                f"Browser target '{target}' is ambiguous."
            )

        return candidates[0]

    @staticmethod
    def _target_failure(message: str):
        raise PermissionError(message)

    @staticmethod
    def _required_value(
        action: AgentAction,
        message: str,
    ) -> str:
        if (
            not isinstance(action.value, str)
            or not action.value.strip()
        ):
            raise ValueError(message)

        return action.value

    @classmethod
    def _contains_low_level_value(cls, value: str) -> bool:
        normalized = value.strip().casefold()

        if any(
            term in normalized
            for term in cls._FORBIDDEN_LOW_LEVEL_TERMS
        ):
            return True

        return normalized.startswith(
            cls._TECHNICAL_TARGET_PREFIXES
        )

    @staticmethod
    def _success(
        action: AgentAction,
        context: ExecutionContext,
        page: BrowserPage,
        *,
        operation: str,
        executed: bool,
        target: str | None = None,
    ) -> ExecutionResult:
        context.set_value(
            "browser_page",
            page,
        )

        context.set_value(
            "browser_last_operation",
            operation,
        )

        metadata: dict[str, object] = {
            "browser_operation": operation,
            "browser_url": page.url,
            "browser_title": page.title,
            "executed": executed,
        }

        if target is not None:
            metadata["target"] = target

        return ExecutionResult(
            action_name=action.name,
            success=True,
            message=(
                f"Browser {operation} completed."
            ),
            metadata=metadata,
        )

    @staticmethod
    def _failure(
        action: AgentAction,
        message: str,
        *,
        manual_review: bool,
    ) -> ExecutionResult:
        return ExecutionResult(
            action_name=action.name,
            success=False,
            message=message,
            requires_manual_review=manual_review,
            metadata={
                "browser_operation": action.name,
                "executed": False,
            },
        )

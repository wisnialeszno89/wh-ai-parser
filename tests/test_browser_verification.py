from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.fake_environment import FakeEnvironment
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.execution_result import ExecutionResult
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.runtime.verification_loop import VerificationLoop
from app.agent.perception.perception_engine import PerceptionEngine
from app.agent.verification.expectation_resolver import ExpectationResolver
from app.agent.verification.outcome_verifier import OutcomeVerifier


def create_context() -> ExecutionContext:
    return ExecutionContext(
        request=AgentRequest(
            message="browser verification test",
        )
    )


def create_page(
    *,
    url="https://example.com/form",
    value="",
) -> BrowserPage:
    return BrowserPage(
        url=url,
        title="Example form",
        text="Form",
        elements=(
            BrowserElement(
                label="Imię",
                kind="textbox",
                interaction_capability="EDITABLE",
                current_value=value,
                confidence=0.99,
            ),
        ),
    )


def test_expectation_resolver_creates_browser_navigation_expectation():
    resolver = ExpectationResolver()

    expected = resolver.resolve(
        AgentAction(
            name="browser_navigate",
            description="Open the target page.",
            value="https://example.com/form/",
        ),
        create_context(),
    )

    assert expected is not None
    assert expected.expected_browser_url == "https://example.com/form/"


def test_expectation_resolver_creates_browser_field_expectation():
    resolver = ExpectationResolver()

    expected = resolver.resolve(
        AgentAction(
            name="browser_write_text",
            description="Enter the name.",
            target="Imię",
            value="Adam",
        ),
        create_context(),
    )

    assert expected is not None
    assert expected.expected_browser_element_label == "Imię"
    assert expected.expected_browser_element_current_value == "Adam"


def test_browser_verifier_accepts_matching_field_value():
    verifier = OutcomeVerifier()

    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_write_text",
            description="Enter the name.",
            target="Imię",
            value="Adam",
        ),
        create_context(),
    )

    result = verifier.verify_browser(
        expected,
        create_page(value="Adam"),
    )

    assert result.verified is True


def test_browser_verifier_rejects_wrong_field_value():
    verifier = OutcomeVerifier()

    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_write_text",
            description="Enter the name.",
            target="Imię",
            value="Adam",
        ),
        create_context(),
    )

    result = verifier.verify_browser(
        expected,
        create_page(value="Ewa"),
    )

    assert result.verified is False
    assert result.metadata is not None
    assert result.metadata["actual_value"] == "Ewa"


def test_browser_verifier_rejects_ambiguous_field():
    verifier = OutcomeVerifier()

    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_write_text",
            description="Enter the name.",
            target="Imię",
            value="Adam",
        ),
        create_context(),
    )

    page = BrowserPage(
        url="https://example.com/form",
        title="Example form",
        text="Form",
        elements=(
            BrowserElement(
                label="Imię",
                interaction_capability="EDITABLE",
                current_value="Adam",
                confidence=0.99,
            ),
            BrowserElement(
                label="Imię",
                interaction_capability="EDITABLE",
                current_value="Adam",
                confidence=0.98,
            ),
        ),
    )

    result = verifier.verify_browser(expected, page)

    assert result.verified is False
    assert "ambiguous" in result.reason.casefold()


def test_browser_verification_loop_uses_browser_page_not_desktop_observe():
    class BrowserExecutor:
        def supports(self, action: AgentAction) -> bool:
            return action.name == "browser_write_text"

        def execute(
            self,
            action: AgentAction,
            context: ExecutionContext,
        ) -> ExecutionResult:
            context.set_value(
                "browser_page",
                create_page(value="Adam"),
            )
            return ExecutionResult(
                action_name=action.name,
                success=True,
                message="Browser field updated.",
                metadata={
                    "browser_operation": "write_text",
                    "executed": True,
                },
            )

    environment = FakeEnvironment(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title="Test Window",
            screen_width=1920,
            screen_height=1080,
        )
    )

    def exploding_observe():
        raise AssertionError(
            "Desktop environment observation must not be used "
            "for browser verification."
        )

    environment.observe = exploding_observe

    loop = VerificationLoop(
        execution_engine=ExecutionEngine(
            ExecutorRegistry(
                executors=(BrowserExecutor(),)
            )
        ),
        environment=environment,
        perception_engine=PerceptionEngine(),
        expectation_resolver=ExpectationResolver(),
        outcome_verifier=OutcomeVerifier(),
    )

    result = loop.run(
        AgentAction(
            name="browser_write_text",
            description="Enter the name.",
            target="Imię",
            value="Adam",
        ),
        create_context(),
    )

    assert result.success is True
    assert result.last_attempt is not None
    assert result.last_attempt.verification_result is not None
    assert result.last_attempt.verification_result.verified is True


def test_browser_click_expectation_verifies_semantic_page_change():
    context = create_context()
    baseline_page = create_page()
    context.set_value("browser_page", baseline_page)

    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_click",
            description="Click the button.",
            target="Zakończ",
        ),
        context,
    )

    assert expected is not None
    assert expected.require_browser_change is True
    assert expected.baseline_browser_signature is not None

    changed_page = create_page(value="changed")
    result = OutcomeVerifier().verify_browser(
        expected,
        changed_page,
    )

    assert result.verified is True


def test_browser_click_verification_rejects_unchanged_page():
    context = create_context()
    baseline_page = create_page()
    context.set_value("browser_page", baseline_page)

    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_click",
            description="Click the button.",
            target="Zakończ",
        ),
        context,
    )

    assert expected is not None

    result = OutcomeVerifier().verify_browser(
        expected,
        baseline_page,
    )

    assert result.verified is False
    assert result.metadata is not None
    assert result.metadata["browser_page_changed"] is False


def test_browser_click_verification_captures_baseline_before_execution():
    class BrowserExecutor:
        def supports(self, action: AgentAction) -> bool:
            return action.name == "browser_click"

        def execute(
            self,
            action: AgentAction,
            context: ExecutionContext,
        ) -> ExecutionResult:
            context.set_value(
                "browser_page",
                BrowserPage(
                    url="https://example.com/form",
                    title="Success",
                    text="Done",
                    elements=(),
                ),
            )
            return ExecutionResult(
                action_name=action.name,
                success=True,
                message="Browser clicked.",
                metadata={
                    "browser_operation": "click",
                    "executed": True,
                },
            )

    baseline = create_page()
    context = create_context()
    context.set_value("browser_page", baseline)

    loop = VerificationLoop(
        execution_engine=ExecutionEngine(
            ExecutorRegistry(
                executors=(BrowserExecutor(),)
            )
        ),
        environment=None,
        perception_engine=PerceptionEngine(),
        expectation_resolver=ExpectationResolver(),
        outcome_verifier=OutcomeVerifier(),
    )

    result = loop.run(
        AgentAction(
            name="browser_click",
            description="Click the button.",
            target="Zakończ",
        ),
        context,
    )

    assert result.success is True
    assert len(result.attempts) == 1
    assert result.last_attempt is not None
    assert result.last_attempt.verification_result is not None
    assert result.last_attempt.verification_result.verified is True
    assert result.last_attempt.verification_result.reason == (
        "Browser page matches expected outcome."
    )

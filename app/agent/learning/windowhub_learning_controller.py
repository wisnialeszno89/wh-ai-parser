from __future__ import annotations

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)
from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)
from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)
from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.environment.windowhub_focus_window_preparation_handler import (
    WindowHubFocusWindowPreparationHandler,
)
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from app.agent.learning.learning_observation_coordinator import (
    LearningObservationCoordinator,
)
from app.agent.learning.learning_session import LearningSession
from app.agent.learning.windowhub_mouse_observer import (
    WindowHubMouseObserver,
)
from app.agent.learning.workflow_memory_store import (
    WorkflowMemoryStore,
)
from app.agent.learning.workflow_repository import WorkflowRepository
from app.agent.runtime.windowhub_agent_control_loop import (
    create_windowhub_agent_control_loop,
)


class WindowHubLearningController:
    """
    Real WindowHub teaching session.

    It focuses WindowHub, captures semantic scenes through the existing
    Universal Agent control loop, observes human clicks scoped to WindowHub,
    and records the demonstrated actions as a semantic workflow.
    """

    def __init__(
        self,
        *,
        learning_session: LearningSession | None = None,
        observer: WindowHubMouseObserver | None = None,
        workflow_memory_store: WorkflowMemoryStore | None = None,
        control_loop=None,
        focus_handler: WindowHubFocusWindowPreparationHandler | None = None,
    ) -> None:
        self.learning_session = (
            learning_session or LearningSession()
        )
        self.observer = (
            observer or WindowHubMouseObserver()
        )
        self.workflow_memory_store = (
            workflow_memory_store
            if workflow_memory_store is not None
            else WorkflowMemoryStore(
                repository=WorkflowRepository(),
                load_persisted=True,
            )
        )
        self.control_loop = (
            control_loop or create_windowhub_agent_control_loop()
        )
        # Learning needs event-time semantic snapshots. The full Universal
        # Control Loop is intentionally expensive because it includes CV and
        # ROI analysis. Use a fast UIA-only observation path while teaching so
        # rapid consecutive human clicks cannot overtake perception.
        self._learning_environment = WindowHubEnvironmentAdapter()
        self._learning_uia_provider = WindowHubUIAutomationProvider()
        self.focus_handler = (
            focus_handler
            or WindowHubFocusWindowPreparationHandler()
        )
        self._coordinator: (
            LearningObservationCoordinator | None
        ) = None

    def _observe_learning_scene(self) -> ScreenScene:
        observation = self._learning_environment.observe()
        elements = self._learning_uia_provider.perceive(observation)
        return ScreenScene(
            observation=observation,
            elements=elements,
        )

    def start(
        self,
        *,
        workflow_id: str,
        name: str,
        trigger: str,
    ) -> None:
        focus_result = self.focus_handler.execute(
            EnvironmentPreparation(
                preparation_type=EnvironmentPreparationType.PREPARE,
                strategy=EnvironmentPreparationStrategy.FOCUS_WINDOW,
                target_application="WindowHub",
                reason="Focus WindowHub before learning.",
            )
        )

        if not focus_result.success:
            raise RuntimeError(
                "WindowHub could not be focused: "
                f"{focus_result.reason}"
            )

        scene = self._observe_learning_scene()

        application = (
            scene.observation.state.active_application
        )

        self.learning_session.start(
            workflow_id=workflow_id,
            name=name,
            trigger=trigger,
            application=application,
            scene=scene,
        )

        self._coordinator = LearningObservationCoordinator(
            session=self.learning_session,
            observer=self.observer,
            scene_provider=self._observe_learning_scene,
        )
        self._coordinator.start()

    def stop_observing(self) -> None:
        coordinator = self._coordinator
        if coordinator is not None:
            coordinator.stop()

    def finish(
        self,
        *,
        notes: str = "",
        metadata: dict[str, object] | None = None,
    ) -> LearnedWorkflow:
        self.stop_observing()

        if not self.learning_session.is_active:
            raise RuntimeError("No WindowHub learning session is active.")

        workflow = self.learning_session.finish(
            notes=notes,
            metadata=metadata,
        )
        self.workflow_memory_store.save(workflow)
        self._coordinator = None
        return workflow

    def discard(self) -> None:
        self.stop_observing()
        self.learning_session.discard()
        self._coordinator = None

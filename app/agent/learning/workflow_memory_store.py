from __future__ import annotations

from app.agent.learning.learned_workflow import LearnedWorkflow


class WorkflowMemoryStore:
    """
    Small in-memory workflow memory.

    This is deliberately an interface-shaped first implementation. It gives
    the runtime a stable semantic memory boundary while persistence,
    embeddings and database storage can evolve independently later.
    """

    def __init__(
        self,
        workflows: tuple[LearnedWorkflow, ...] = (),
    ) -> None:
        self._workflows: dict[str, LearnedWorkflow] = {
            workflow.workflow_id: workflow
            for workflow in workflows
        }

    def save(self, workflow: LearnedWorkflow) -> None:
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> LearnedWorkflow | None:
        return self._workflows.get(workflow_id)

    def all(self) -> tuple[LearnedWorkflow, ...]:
        return tuple(self._workflows.values())

    def find(
        self,
        *,
        application: str | None = None,
        trigger: str | None = None,
    ) -> tuple[LearnedWorkflow, ...]:
        normalized_application = (
            application.casefold()
            if isinstance(application, str)
            else None
        )
        normalized_trigger = (
            trigger.casefold()
            if isinstance(trigger, str)
            else None
        )

        matches = []
        for workflow in self._workflows.values():
            if (
                normalized_application is not None
                and (
                    workflow.application is None
                    or workflow.application.casefold()
                    != normalized_application
                )
            ):
                continue

            if (
                normalized_trigger is not None
                and normalized_trigger
                not in workflow.trigger.casefold()
            ):
                continue

            matches.append(workflow)

        return tuple(matches)

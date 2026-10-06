from __future__ import annotations

from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.workflow_matcher import (
    WorkflowMatch,
    WorkflowMatcher,
)
from app.agent.learning.workflow_repository import WorkflowRepository


class WorkflowMemoryStore:
    """In-memory workflow cache with optional durable persistence.

    The runtime keeps fast in-process lookup while a repository can provide
    persistence across agent restarts. Keeping both behind this boundary
    leaves the storage technology replaceable later.
    """

    def __init__(
        self,
        workflows: tuple[LearnedWorkflow, ...] = (),
        *,
        repository: WorkflowRepository | None = None,
        load_persisted: bool = True,
    ) -> None:
        self.repository = repository
        self._workflows: dict[str, LearnedWorkflow] = {
            workflow.workflow_id: workflow
            for workflow in workflows
        }

        if repository is not None and load_persisted:
            for workflow in repository.all():
                self._workflows[workflow.workflow_id] = workflow

    def save(self, workflow: LearnedWorkflow) -> None:
        self._workflows[workflow.workflow_id] = workflow

        if self.repository is not None:
            self.repository.save(workflow)

    def get(self, workflow_id: str) -> LearnedWorkflow | None:
        workflow = self._workflows.get(workflow_id)
        if workflow is not None:
            return workflow

        if self.repository is None:
            return None

        workflow = self.repository.get(workflow_id)
        if workflow is not None:
            self._workflows[workflow.workflow_id] = workflow
        return workflow

    def all(self) -> tuple[LearnedWorkflow, ...]:
        return tuple(self._workflows.values())

    def find(
        self,
        *,
        application: str | None = None,
        trigger: str | None = None,
    ) -> tuple[LearnedWorkflow, ...]:
        """Return legacy-filtered matches.

        New callers that need ranking should use the match method. This method
        keeps the older exact/substring behavior for compatibility.
        """
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

    def match(
        self,
        message: str,
        *,
        application: str | None = None,
        limit: int = 5,
        min_score: float = 0.55,
        matcher: WorkflowMatcher | None = None,
    ) -> tuple[WorkflowMatch, ...]:
        """Rank stored workflows against a semantic user request."""
        workflow_matcher = matcher or WorkflowMatcher()
        return workflow_matcher.match(
            message,
            self.all(),
            application=application,
            limit=limit,
            min_score=min_score,
        )

    def delete(self, workflow_id: str) -> bool:
        existed = workflow_id in self._workflows
        self._workflows.pop(workflow_id, None)

        if self.repository is not None:
            persisted = self.repository.delete(workflow_id)
            existed = existed or persisted

        return existed

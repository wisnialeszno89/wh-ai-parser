"""Lifecycle service for persisted resumable task checkpoints."""
from __future__ import annotations

from collections.abc import Callable, Mapping

from app.agent.runtime.resumable_task import ResumableTaskRunner, TaskCheckpoint


class ResumableTaskService:
    """Store checkpoints around one-step runner advances.

    A host supplies the runner factory because environment observation and live
    execution must be configured explicitly by the application. This service
    never chooses live mode on its own.
    """

    def __init__(
        self,
        *,
        repository,
        runner_factory: Callable[[TaskCheckpoint], ResumableTaskRunner],
    ) -> None:
        if repository is None:
            raise ValueError("A checkpoint repository is required.")
        if not callable(runner_factory):
            raise ValueError("runner_factory must be callable.")
        self.repository = repository
        self.runner_factory = runner_factory

    def create(self, checkpoint: TaskCheckpoint) -> TaskCheckpoint:
        if not isinstance(checkpoint, TaskCheckpoint):
            raise TypeError("create expects a TaskCheckpoint.")
        existing = self.repository.get(checkpoint.task_id)
        if existing is not None:
            raise FileExistsError(
                f"A checkpoint already exists for task {checkpoint.task_id!r}."
            )
        self.repository.save(checkpoint)
        return checkpoint

    def get(self, task_id: str) -> TaskCheckpoint | None:
        return self.repository.get(task_id)

    def advance(self, task_id: str) -> TaskCheckpoint:
        checkpoint = self.repository.get(task_id)
        if checkpoint is None:
            raise KeyError(f"No checkpoint exists for task {task_id!r}.")
        runner = self.runner_factory(checkpoint)
        if not isinstance(runner, ResumableTaskRunner):
            raise TypeError("runner_factory must return a ResumableTaskRunner.")
        updated = runner.advance(checkpoint)
        if not isinstance(updated, TaskCheckpoint):
            raise TypeError("ResumableTaskRunner.advance must return a TaskCheckpoint.")
        if updated.task_id != checkpoint.task_id:
            raise ValueError("Runner changed the task id; refusing to save its output.")
        self.repository.save(updated)
        return updated

    def supply_facts(
        self, task_id: str, values: Mapping[str, object]
    ) -> TaskCheckpoint:
        checkpoint = self._require(task_id)
        updated = checkpoint.with_facts(values)
        self.repository.save(updated)
        return updated

    def resolve_issue(self, task_id: str, issue: str) -> TaskCheckpoint:
        checkpoint = self._require(task_id)
        updated = checkpoint.resolve_issue(issue)
        self.repository.save(updated)
        return updated

    def approve_pending_action(
        self, task_id: str, *, approve_submission: bool = False
    ) -> TaskCheckpoint:
        checkpoint = self._require(task_id)
        updated = checkpoint.approve_pending_action(
            approve_submission=approve_submission
        )
        self.repository.save(updated)
        return updated

    def resume_after_review(self, task_id: str) -> TaskCheckpoint:
        checkpoint = self._require(task_id)
        updated = checkpoint.resume_after_review()
        self.repository.save(updated)
        return updated

    def delete(self, task_id: str) -> bool:
        return self.repository.delete(task_id)

    def _require(self, task_id: str) -> TaskCheckpoint:
        checkpoint = self.repository.get(task_id)
        if checkpoint is None:
            raise KeyError(f"No checkpoint exists for task {task_id!r}.")
        return checkpoint

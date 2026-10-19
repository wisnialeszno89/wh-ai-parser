"""Local persistence for resumable agent task checkpoints.

Checkpoints may contain customer/quote data. The repository stores files only
on the configured local filesystem; it never uploads them or executes actions.
Configure AGENT_TASK_CHECKPOINT_STORE_DIR for an application-owned data path.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Mapping

from app.agent.runtime.resumable_task import TaskCheckpoint


class TaskCheckpointRepository:
    """Atomic JSON storage for versioned task checkpoints."""

    def __init__(self, root: str | Path | None = None) -> None:
        configured_root = os.getenv("AGENT_TASK_CHECKPOINT_STORE_DIR", "").strip()
        self.root = Path(
            root if root is not None else configured_root or "runtime_data/task_checkpoints"
        ).expanduser()

    @staticmethod
    def _validate_task_id(task_id: str) -> str:
        if not isinstance(task_id, str):
            raise ValueError("task_id must be a string.")
        normalized = task_id.strip()
        if not normalized:
            raise ValueError("task_id must not be empty.")
        if len(normalized) > 200:
            raise ValueError("task_id is too long.")
        return normalized

    def path_for(self, task_id: str) -> Path:
        normalized = self._validate_task_id(task_id)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

    def save(self, checkpoint: TaskCheckpoint) -> Path:
        if not isinstance(checkpoint, TaskCheckpoint):
            raise TypeError("TaskCheckpointRepository.save expects a TaskCheckpoint.")
        payload = checkpoint.to_payload()
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        target = self.path_for(checkpoint.task_id)
        self.root.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.stem}.",
            suffix=".tmp",
            dir=self.root,
        )
        temporary = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(serialized)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(target)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        return target

    def get(self, task_id: str) -> TaskCheckpoint | None:
        normalized = self._validate_task_id(task_id)
        target = self.path_for(normalized)
        if not target.exists():
            return None
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Stored checkpoint for {normalized!r} is unreadable or invalid JSON."
            ) from exc
        if not isinstance(payload, Mapping):
            raise ValueError(
                f"Stored checkpoint for {normalized!r} must be a JSON object."
            )
        checkpoint = TaskCheckpoint.from_payload(payload)
        if checkpoint.task_id != normalized:
            raise ValueError("Stored checkpoint id does not match the requested task id.")
        return checkpoint

    def delete(self, task_id: str) -> bool:
        target = self.path_for(task_id)
        try:
            target.unlink()
        except FileNotFoundError:
            return False
        return True

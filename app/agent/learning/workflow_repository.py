from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from app.agent.learning.learned_workflow import LearnedWorkflow


class WorkflowRepository:
    """Persistent JSON repository for learned workflows.

    Files are stored outside the source tree by default so learned company
    procedures are local runtime data, not source-controlled application code.
    """

    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:
        configured_root = os.getenv("AGENT_WORKFLOW_STORE_DIR", "").strip()
        self.root = Path(
            root
            if root is not None
            else configured_root or "runtime_data/learned_workflows"
        ).expanduser()

    def path_for(self, workflow_id: str) -> Path:
        normalized = self._validate_workflow_id(workflow_id)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
        return self.root / f"{digest}.json"

    def save(self, workflow: LearnedWorkflow) -> Path:
        if not isinstance(workflow, LearnedWorkflow):
            raise TypeError("WorkflowRepository.save expects a LearnedWorkflow.")

        target = self.path_for(workflow.workflow_id)
        self.root.mkdir(parents=True, exist_ok=True)

        temporary = target.with_suffix(".json.tmp")
        payload = json.dumps(
            workflow.to_payload(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(target)
        return target

    def get(self, workflow_id: str) -> LearnedWorkflow | None:
        target = self.path_for(workflow_id)
        if not target.exists():
            return None

        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(
                f"Stored workflow {workflow_id!r} does not contain an object."
            )

        workflow = LearnedWorkflow.from_payload(payload)
        if workflow.workflow_id != workflow_id:
            raise ValueError(
                "Stored workflow id does not match the requested workflow id."
            )
        return workflow

    def all(self) -> tuple[LearnedWorkflow, ...]:
        if not self.root.exists():
            return ()

        workflows: list[LearnedWorkflow] = []
        for path in sorted(self.root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(
                    f"Stored workflow file {path.name!r} is not an object."
                )
            workflows.append(LearnedWorkflow.from_payload(payload))

        return tuple(
            sorted(
                workflows,
                key=lambda workflow: (
                    workflow.name.casefold(),
                    workflow.workflow_id,
                ),
            )
        )

    def delete(self, workflow_id: str) -> bool:
        target = self.path_for(workflow_id)
        try:
            target.unlink()
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def _validate_workflow_id(workflow_id: str) -> str:
        if not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a string.")

        normalized = workflow_id.strip()
        if not normalized:
            raise ValueError("workflow_id must not be empty.")

        if len(normalized) > 200:
            raise ValueError("workflow_id is too long.")

        return normalized

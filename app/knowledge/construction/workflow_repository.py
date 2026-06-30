import json

from pathlib import Path

from app.knowledge.construction.models.workflow_definition import (
    WorkflowDefinition
)


class WorkflowRepository:

    BASE_PATH = Path(
        "app/knowledge/construction/workflows"
    )

    def load(
        self,
        workflow_name: str
    ) -> WorkflowDefinition:

        path = (
            self.BASE_PATH /
            f"{workflow_name}.json"
        )

        with open(
            path,
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return WorkflowDefinition(

            name=data["name"],

            difficulty=data["difficulty"],

            manual_review=data["manual_review"],

            steps=data["steps"]
        )
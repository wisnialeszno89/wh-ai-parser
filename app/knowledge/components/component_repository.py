import json
from pathlib import Path

from app.knowledge.components.component_definition import ComponentDefinition


class ComponentRepository:

    def __init__(self, data_path: Path | None = None):
        data = (
            data_path
            if data_path is not None
            else Path(__file__).parent / "profiles.json"
        )

        with open(data, encoding="utf-8") as fp:
            raw = json.load(fp)

        self._components = [
            ComponentDefinition(
                profile=item["profile"],
                default_frame=item["default_frame"],
                default_glass=item["default_glass"],
                default_hardware=item["default_hardware"],
            )
            for item in raw
        ]

    def components(self) -> list[ComponentDefinition]:
        return list(self._components)

    def get_by_profile(self, profile: str) -> ComponentDefinition | None:
        for component in self._components:
            if component.profile == profile:
                return component

        return None

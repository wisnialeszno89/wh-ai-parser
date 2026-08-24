from __future__ import annotations

from dataclasses import dataclass

from app.gui.enums.gui_tool import GuiTool
from app.window_model.model import WindowElementType, WindowModel
from app.window_model.topology import WindowSide, WindowTopology


@dataclass(frozen=True)
class ExecutableStep:
    element_id: str
    element_type: WindowElementType
    gui_tool: GuiTool
    side: WindowSide
    parent_id: str | None
    blocked_by: tuple[str, ...] = ()


class DependencyPlanner:
    """Turn a semantic topology plan into a dependency-safe execution order."""

    def plan(self, desired: WindowModel, topology: WindowTopology) -> list[ExecutableStep]:
        pending = [e for e in desired.elements.values() if e.id != desired.id]
        pending.sort(key=self._priority)
        result: list[ExecutableStep] = []
        completed: set[str] = {desired.id}

        while pending:
            progressed = False
            for element in list(pending):
                dependencies = self._dependencies(element, desired)
                if not dependencies.issubset(completed):
                    continue
                node = topology.node(element.id)
                result.append(
                    ExecutableStep(
                        element_id=element.id,
                        element_type=element.type,
                        gui_tool=GuiTool[element.type.value],
                        side=node.side if node else WindowSide.UNKNOWN,
                        parent_id=element.parent_id,
                        blocked_by=tuple(sorted(dependencies - completed)),
                    )
                )
                completed.add(element.id)
                pending.remove(element)
                progressed = True
                break
            if not progressed:
                unresolved = ", ".join(e.id for e in pending)
                raise ValueError(f"Cyclic or unsatisfied construction dependencies: {unresolved}")
        return result

    @staticmethod
    def _priority(element) -> tuple[int, str]:
        priority = {
            WindowElementType.MULLION: 10,
            WindowElementType.HORIZONTAL_MULLION: 10,
            WindowElementType.MOVABLE_MULLION: 10,
            WindowElementType.SASH: 20,
            WindowElementType.GLASS: 30,
            WindowElementType.HARDWARE: 40,
            WindowElementType.CONNECTOR: 50,
            WindowElementType.LIMITER: 60,
        }
        return priority.get(element.type, 100), element.id

    @staticmethod
    def _dependencies(element, model: WindowModel) -> set[str]:
        deps = set()
        if element.parent_id:
            deps.add(element.parent_id)
        if element.type == WindowElementType.GLASS and element.parent_id:
            deps.add(element.parent_id)
        if element.type == WindowElementType.HARDWARE and element.parent_id:
            deps.add(element.parent_id)
        return deps

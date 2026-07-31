from dataclasses import dataclass, field

from app.gui.gui_action import GuiAction
from app.runtime.mission.mission_step import MissionStep


@dataclass(slots=True)
class MissionTrace:

    steps: list[MissionStep] = field(
        default_factory=list,
    )

    def add_step(
        self,
        step: MissionStep,
    ) -> None:

        self.steps.append(step)

    def has_executed(
        self,
        action: GuiAction,
    ) -> bool:

        return any(

            step.action == action

            for step in self.steps

        )

    def execution_count(
        self,
        action: GuiAction,
    ) -> int:

        return sum(

            1

            for step in self.steps

            if step.action == action

        )

    def last_step(
        self,
    ) -> MissionStep | None:

        if not self.steps:
            return None

        return self.steps[-1]

    @property
    def total_steps(
        self,
    ) -> int:

        return len(self.steps)

    @property
    def success_count(
        self,
    ) -> int:

        return sum(

            1

            for step in self.steps

            if step.result.success

        )

    @property
    def failed_count(
        self,
    ) -> int:

        return self.total_steps - self.success_count

    @property
    def total_duration_ms(
        self,
    ) -> int:

        return sum(

            step.result.duration_ms

            for step in self.steps

        )

    @property
    def average_duration_ms(
        self,
    ) -> float:

        if not self.steps:
            return 0

        return (
            self.total_duration_ms
            / self.total_steps
        )

    @property
    def success_rate(
        self,
    ) -> float:

        if not self.steps:
            return 0.0

        return (
            self.success_count
            / self.total_steps
        )
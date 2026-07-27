from abc import ABC
from abc import abstractmethod


class BaseSkill(ABC):

    @abstractmethod
    def build_actions(
        self,
        world,
        context,
    ):
        """
        Returns GuiActions required
        to accomplish the goal.
        """
        pass
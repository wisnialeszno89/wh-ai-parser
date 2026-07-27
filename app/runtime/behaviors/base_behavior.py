from abc import ABC
from abc import abstractmethod


class BaseBehavior(ABC):

    @abstractmethod
    def execute(
        self,
        world,
        context,
    ):
        """
        Executes high-level behavior.
        """
        pass
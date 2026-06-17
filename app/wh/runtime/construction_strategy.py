from abc import (
    ABC,
    abstractmethod
)


class ConstructionStrategy(

    ABC

):

    @abstractmethod
    def plan(

        self,

        construction

    ):

        pass
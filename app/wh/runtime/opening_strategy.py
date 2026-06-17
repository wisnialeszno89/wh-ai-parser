from abc import (
    ABC,
    abstractmethod
)


class OpeningStrategy(

    ABC

):

    @abstractmethod
    def plan(

        self

    ):

        pass
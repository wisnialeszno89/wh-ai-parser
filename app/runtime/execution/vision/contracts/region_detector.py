from abc import ABC
from abc import abstractmethod


class RegionDetector(ABC):

    @abstractmethod
    def detect(
        self,
        screenshot,
    ):

        ...
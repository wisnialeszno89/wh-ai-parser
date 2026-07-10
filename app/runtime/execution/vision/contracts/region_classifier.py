from abc import ABC
from abc import abstractmethod


class RegionClassifier(ABC):

    @abstractmethod
    def classify(
        self,
        region,
    ):

        ...
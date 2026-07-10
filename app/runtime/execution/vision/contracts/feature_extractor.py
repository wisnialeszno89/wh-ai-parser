from abc import ABC
from abc import abstractmethod


class FeatureExtractor(ABC):

    @abstractmethod
    def extract(
        self,
        region,
    ):

        ...
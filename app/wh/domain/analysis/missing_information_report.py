from dataclasses import dataclass, field

from app.wh.domain.analysis.missing_information_item import (
    MissingInformationItem
)


@dataclass(slots=True)
class MissingInformationReport:

    items: list[MissingInformationItem] = field(default_factory=list)

    def add(

        self,

        item: MissingInformationItem

    ):

        self.items.append(item)

    @property
    def is_complete(

        self

    ) -> bool:

        return len(self.items) == 0
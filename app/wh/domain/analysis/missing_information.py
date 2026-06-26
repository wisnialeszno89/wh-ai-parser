from dataclasses import dataclass, field


@dataclass(slots=True)
class MissingInformation:

    fields: list[str] = field(default_factory=list)

    def add(

        self,

        field_name: str

    ):

        if field_name not in self.fields:

            self.fields.append(field_name)

    @property
    def is_complete(

        self

    ) -> bool:

        return len(self.fields) == 0
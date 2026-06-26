from dataclasses import dataclass, field

from app.wh.runtime.vision.mail.mail_entity import (
    MailEntity
)


@dataclass(slots=True)
class MailEntities:

    items: list[MailEntity] = field(

        default_factory=list

    )

    def add(

        self,

        entity: MailEntity

    ):

        self.items.append(

            entity

        )

    def find(

        self,

        entity_type: str

    ):

        return [

            item

            for item in self.items

            if item.entity_type == entity_type

        ]
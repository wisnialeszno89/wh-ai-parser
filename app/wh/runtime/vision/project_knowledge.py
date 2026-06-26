from dataclasses import (
    dataclass
)


@dataclass
class ProjectKnowledge:

    most_common_profile: str | None = None

    most_common_color: str | None = None

    most_common_security: str | None = None
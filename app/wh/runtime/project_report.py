from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.configuration_report import (
    ConfigurationReport
)

from app.wh.runtime.geometry_report import (
    GeometryReport
)


@dataclass
class ProjectReport:

    configuration: ConfigurationReport = field(

        default_factory=ConfigurationReport

    )

    geometry: GeometryReport = field(

        default_factory=GeometryReport

    )
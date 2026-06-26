from dataclasses import (
    dataclass
)


@dataclass
class SalesAnalytics:

    total_offers: int

    average_execution_time: float

    average_error_count: float

    success_rate: float
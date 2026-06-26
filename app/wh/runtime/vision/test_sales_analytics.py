from app.wh.runtime.vision.sales_analytics import (
    SalesAnalytics
)


def test_sales_analytics():

    analytics = (

        SalesAnalytics(

            total_offers=1000,

            average_execution_time=17.8,

            average_error_count=0.3,

            success_rate=0.98

        )

    )

    assert (

        analytics.total_offers

        ==

        1000

    )

    assert (

        analytics.success_rate

        ==

        0.98

    )
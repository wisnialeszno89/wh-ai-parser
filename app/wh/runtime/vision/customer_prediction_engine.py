from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


class CustomerPredictionEngine:

    def predict(

        self,

        customer_preference

    ):

        return (

            CustomerPrediction(

                customer_name=(

                    customer_preference.customer_name

                ),

                profile=(

                    customer_preference.profile_preference

                ),

                color=(

                    customer_preference.color_preference

                ),

                addon=(

                    customer_preference.addon_preference

                ),

                confidence=(

                    customer_preference.confidence

                )

            )

        )
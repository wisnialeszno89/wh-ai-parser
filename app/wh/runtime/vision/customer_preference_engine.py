from app.wh.runtime.vision.customer_preference import (
    CustomerPreference
)


class CustomerPreferenceEngine:

    def analyze(

        self,

        customer_knowledge

    ):

        profile = ""

        color = ""

        addon = ""

        if customer_knowledge.top_profiles:

            profile = (

                customer_knowledge.top_profiles[0]

            )

        if customer_knowledge.top_colors:

            color = (

                customer_knowledge.top_colors[0]

            )

        if customer_knowledge.top_addons:

            addon = (

                customer_knowledge.top_addons[0]

            )

        return (

            CustomerPreference(

                customer_name=(

                    customer_knowledge.customer_name

                ),

                profile_preference=profile,

                color_preference=color,

                addon_preference=addon,

                confidence=0.95

            )

        )
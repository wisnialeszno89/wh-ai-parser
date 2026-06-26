from app.wh.runtime.construction_features import (
    ConstructionFeatures
)


class FeatureParser:

    def parse(

        self,

        text

    ):

        features = (

            ConstructionFeatures()

        )

        lower = (

            text.lower()

        )

        if "antracyt" in lower:

            features.color_inside = (

                "anthracite"

            )

            features.color_outside = (

                "anthracite"

            )

        if "3 szyby" in lower:

            features.glass = (

                "3glass"

            )

        if "ciepła ramka" in lower:

            features.warm_edge = (

                True

            )

        if "swisspacer" in lower:

            features.swisspacer = (

                True

            )

        if "v-perfect" in lower:

            features.v_perfect = (

                True

            )

        if "ukryte zawiasy" in lower:

            features.hidden_hinges = (

                True

            )

        if "kontaktrony" in lower:

            features.contacts = (

                True

            )

        if "p4" in lower:

            features.security_glass_p4 = (

                True

            )

        if "rc2" in lower:

            features.security_class_rc2 = (

                True

            )

        if "48 mm" in lower:

            features.glass_package_mm = (

                48

            )

        if "52 mm" in lower:

            features.glass_package_mm = (

                52

            )

        return features
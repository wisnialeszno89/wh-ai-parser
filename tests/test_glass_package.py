from app.wh.runtime.features.glass_package import (
    GlassPackage
)


def test_glass_package():

    package = (

        GlassPackage(

            type="3glass",

            thickness_mm=48,

            warm_edge=True,

            swisspacer=True,

            security_p4=True

        )

    )

    assert package.type == "3glass"

    assert package.thickness_mm == 48

    assert package.warm_edge is True

    assert package.swisspacer is True

    assert package.security_p4 is True
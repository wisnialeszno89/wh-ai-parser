from app.wh.runtime.features.hardware_package import (
    HardwarePackage
)


def test_hardware_package():

    package = (

        HardwarePackage(

            hidden_hinges=True,

            v_perfect=True

        )

    )

    assert package.hidden_hinges is True

    assert package.v_perfect is True
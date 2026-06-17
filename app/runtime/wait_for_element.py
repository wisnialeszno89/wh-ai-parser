from app.runtime.locator import (
    locate_element
)


def wait_for_element(

    element,

    retries=3

):

    for _ in range(

        retries

    ):

        location = locate_element(

            element

        )

        if location:

            return location

    return None
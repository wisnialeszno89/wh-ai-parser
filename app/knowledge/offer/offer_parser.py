from app.knowledge.offer.offer_draft import (
    OfferDraft
)

from app.knowledge.offer.unknown_item import (
    UnknownItem
)

from app.knowledge.text.text_to_schema import (
    text_to_schema
)

from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)

from app.knowledge.colors.color_parser import (
    parse_color
)

from app.knowledge.glass.glass_parser import (
    parse_glass
)

from app.knowledge.profiles.profile_parser import (
    parse_profile
)


def parse_offer(
    text
):

    constructions = []

    accessories = []

    colors = []

    glasses = []

    profiles = []

    unknown_items = []

    #
    # whole text -> construction
    #

    try:

        schema = text_to_schema(
            text
        )

        if schema.segments:

            constructions.append(
                schema
            )

    except:

        pass

    #
    # process line by line
    #

    for line in text.splitlines():

        line = line.strip()

        if not line:

            continue

        #
        # skip construction lines
        #

        try:

            line_schema = text_to_schema(
                line
            )

            if line_schema.segments:

                continue

        except:

            pass

        #
        # color
        #

        color = parse_color(
            line
        )

        if color:

            colors.append(
                color
            )

            continue

        #
        # glass
        #

        glass = parse_glass(
            line
        )

        if glass:

            glasses.append(
                glass
            )

            continue

        #
        # profile
        #

        profile = parse_profile(
            line
        )

        if profile:

            profiles.append(
                profile
            )

            continue

        #
        # accessory
        #

        accessory = parse_accessory(
            line
        )

        if accessory:

            accessories.append(
                accessory
            )

            continue

        #
        # unknown
        #

        unknown_items.append(

            UnknownItem(

                source_text=
                    line

            )

        )

    return OfferDraft(

        constructions=
            constructions,

        accessories=
            accessories,

        colors=
            colors,

        glasses=
            glasses,

        profiles=
            profiles,

        unknown_items=
            unknown_items

    )
NORMALIZED_IDS = {

    "ru_ru":
        "double_sash_movable_mullion",

    "fix_ru":
        "fix_ru",

    "hst_2_panel":
        "hst_2_panel",

    "single_sash":
        "single_sash",
}


def normalize_construction_id(
    construction_id: str
):

    return NORMALIZED_IDS.get(

        construction_id,

        construction_id
    )
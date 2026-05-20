from app.wh.templates.fix_ru_fix import (
    FIX_RU_FIX_TEMPLATE
)


TEMPLATES = {

    "fix_ru_fix":

        FIX_RU_FIX_TEMPLATE
}


def get_template(name):

    return TEMPLATES.get(name)
from app.wh.runtime.intent import (
    WindowIntent
)

from app.wh.runtime.workflows.create_fix import (
    create_fix_workflow
)


intent = WindowIntent(

    geometry="FIX",

    width=1000,

    height=1000,

    glass="3glass",

    color="antra"
)

create_fix_workflow(
    intent
)
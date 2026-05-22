from app.wh.runtime.intent import (
    WindowIntent
)

from app.wh.runtime.workflow_registry import (
    WorkflowRegistry
)

from app.wh.runtime.actions.action_replay import (
    ActionReplay
)

from app.wh.runtime.engine import (
    WHRuntime
)


intent = WindowIntent(

    geometry="FIX",

    width=1000,

    height=1000,

    glass="3glass",

    color="antra"
)

registry = WorkflowRegistry()

workflow = registry.resolve(
    intent
)

workflow(
    intent
)

runtime = WHRuntime(
    intent
)

ActionReplay.replay(

    runtime,

    "runtime_data/ru_pipeline.json"
)
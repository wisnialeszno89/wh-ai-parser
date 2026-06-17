from app.actions.planner.build_action_plan import (
    build_action_plan
)

from app.runtime.serializer.serialize_plan import (
    serialize_plan
)

from app.runtime.exporters.export_ahk import (
    export_ahk
)

from app.core.scene.models.scene_graph import (
    SceneGraph
)

from app.core.scene.models.scene_object import (
    SceneObject
)

from app.ui.models.ui_scene_graph import (
    UISceneGraph
)

from app.ui.models.ui_object import (
    UIObject
)


construction_graph = SceneGraph(

    objects=[

        SceneObject(

            id="segment_1",

            object_type="segment",

            x=0,
            y=0,

            width=100,
            height=100
        ),

        SceneObject(

            id="segment_2",

            object_type="segment",

            x=100,
            y=0,

            width=100,
            height=100
        )
    ]
)

ui_graph = UISceneGraph(

    objects=[

        UIObject(

            id="frame_tool",

            object_type="tool",

            x=50,
            y=20,

            width=30,
            height=30
        ),

        UIObject(

            id="mullion_tool",

            object_type="tool",

            x=100,
            y=20,

            width=30,
            height=30
        )
    ]
)

plan = build_action_plan(

    construction_graph,

    ui_graph
)

commands = serialize_plan(

    plan,

    ui_graph
)

export_ahk(

    commands,

    "outputs/runtime/generated_runtime.ahk"
)
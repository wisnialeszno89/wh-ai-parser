from pprint import pprint

from app.ui.agent.task_builder import (
    build_tasks
)


construction = {

    "width_mm": 2090,

    "height_mm": 1440,

    "profile_system":
        "VEKA Softline 82",

    "glass_type":
        "44.4/16/4",

    "segments": [

        {
            "opening":
                "tilt_turn"
        },

        {
            "opening":
                "tilt_turn"
        }
    ]
}

tasks = build_tasks(
    construction
)

print()

print("=" * 80)
print("TASKS")
print("=" * 80)

print()

for task in tasks:

    pprint(task)

print()
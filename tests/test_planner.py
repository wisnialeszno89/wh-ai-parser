from pprint import pprint

from app.ui.agent.planner import (
    build_plan
)


construction = {

    "glass_type":
        "44.4/16/4",

    "profile_system":
        "VEKA Softline 82"
}

plan = build_plan(
    construction
)

print()

print("=" * 80)
print("PLAN")
print("=" * 80)

print()

for step in plan:

    pprint(
        step
    )

print()
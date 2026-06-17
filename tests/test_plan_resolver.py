from pprint import pprint

from app.ui.agent.planner import (
    build_plan
)

from app.ui.agent.plan_resolver import (
    resolve_plan
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

resolved = resolve_plan(
    plan
)

print()

print("=" * 80)
print("RESOLVED PLAN")
print("=" * 80)

print()

for item in resolved:

    pprint(item)

print()
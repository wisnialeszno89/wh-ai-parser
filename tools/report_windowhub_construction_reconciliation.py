"""Offline report for existing WindowHub construction model and verification."""
from app.agent.learning.windowhub_construction_reconciliation import two_sash_example, reconcile_construction
from app.window_model.dependency_planner import DependencyPlanner
from app.window_model.topology import infer_topology

def main():
    model = two_sash_example()
    plan = DependencyPlanner().plan(model, infer_topology(model))
    status = reconcile_construction(model)
    print("=== WINDOWHUB CONSTRUCTION PLAN: OFFLINE ===")
    for i, step in enumerate(plan, 1):
        print(f"{i}. {step.element_id}: {step.gui_tool.name}, {step.side.value}, parent={step.parent_id}")
    print("STEPS =", len(plan))
    print("NEXT_COMPONENT =", status.next_step.element_id if status.next_step else "NONE")
    print("VERIFICATION =", status.status)
    print("LIVE_COMPONENT_IDENTITIES = NOT_YET_VERIFIED")
    print("ACTIONS_EXECUTED = 0")
    print("MODEL_REQUESTS = 0")

if __name__ == "__main__":
    main()

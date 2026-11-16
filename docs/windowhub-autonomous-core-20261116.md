# WindowHub autonomous agent: integration architecture and acceptance gates

## Actual diagnosis (2026-11-16)

The repository has two different execution styles:
- Fixed `tools/run_windowhub_sales_offer_live.py` and the older `Top Trans` runner: hardcoded business flow, status flags, and wizard-stage order. Successful fixture/unit tests prove only their bounded behaviors.
- `tools/run_windowhub_goal_v2.py`: free-text `--goal`, semantic UIA world model, action capability inventory, NaviMind reasoning, scoped verification. This is the **intended central agent loop**, but its live dependability and goal-specific completion verification are not established.
- Local-only `adaptive_goal_runtime.py` and `verified_goal_loop.py` mentioned during development are **not on this remote branch**. Preserve the other Windows worktree until reviewed and selectively imported.

Problem seen in real dimension run: a generic control-loop retry sent Ctrl+A and 1500 twice but never confirmed target field value. Replacement with UIA `ValuePattern.SetValue` was committed afterward; there is **no live result proving that it works**. DevExpress controls may demand separate commit semantics. Therefore determine the actual before/after native value and focus, do not assume Ctrl+A append was the sole root cause.

## One universal cognitive loop

1. **Goal**: parse user language into observable outcomes; a customer is optional. Example: "change the current window's width" does NOT require starting an offer or a customer lookup.
2. **Observe**: WindowHub currently supports application discovery, stage inference, UIA accessibility, local screenshots and native capability bounds.
3. **World state**: ephemeral `ProgressMemory` preserves what changed across cycles (field value hashes, checked/selected flags and stage) without customer text or pixel coordinates. The no-progress guard refuses an identical attempted action on the same unchanged observed state.
4. **Plan**: reasoner receives the free-form objective, current world and allowed semantic actions. It may select a verified local skill for an operation, but it must not invent control identity or assume all UIA elements are actually clickable.
5. **Execute**: local executor rebinds the native target, confirms foreground/scope and handles one bounded action. Separate adapters for legacy widgets must support complete replacement and explicit commit with actual native readback.
6. **Verify & recover**: distinguish action executed, screen changed, business goal achieved, and document approved. If no progress, provide a diagnosis and choose a *different evidence-based* method. Never repeat the same write with unchanged state or infer success from being in Modyfikator.
7. **Teach**: passive observation of a skilled user is a hint, not proof of cause. Promote a demonstrated skill only after a repeated test, exact readback, and human approval; retain version/environment scoping and reversal. Manual confirmation should let the agent continue from the observed state.
8. **Final approval**: all documents/preferences/offers go to the salesperson for review before customer delivery; no unsupervised sending, final save, or irreversible order.

## Committed changes in this iteration

- `app/agent/runtime/goal_progress_memory.py` generic observation fingerprint, anti-repeat state ledger and non-sensitive feedback.
- `tools/run_windowhub_goal_v2.py` reports world stage/change/semantic control count to the reasoning loop, blocks same action on unchanged observed world, and **no longer falsely marks arbitrary goals complete just because the editor is open**.
- `tests/test_goal_progress_memory.py` tests state changes, repeated action gating and input privacy.

## Next milestones (not yet delivered)

A. Validate model-backed `think` mode in the real `Wielkość okna` screen, with V2 endpoint configured; inspect proposed target and its postcondition before live mode.
B. Implement goal-specific completion evidence (width/height 1500×1400, exact color sides, glazing) and a native DevExpress text replacement/commit skill only if `SetValue` passes live readback.
C. Make skill registry and coordinator choose `dimension_replace`, `select_exact_customer`, `set_checkbox`, `select_catalog_choice` based on observed controls rather than task-specific prewritten steps.
D. Extend recovery to UIA-native selection, keyboard with verified focus, visual fallback (with independent validation); never repeat uncertain writes.
E. Teach mode should learn successful causal action patterns and test them in a sandbox/new draft before reuse in business data. Permanent skill memory requires explicit opt-in.
F. Instrument end-to-end benchmark on real WindowHub for three tasks: edit current dimensions with defaults already set; resume a wizard at basic parameters; create a new draft with optional customer and request final salesperson approval.

No live tests executed by GitHub connector. No Vercel change.

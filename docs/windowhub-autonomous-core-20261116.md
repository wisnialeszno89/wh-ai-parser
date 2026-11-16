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


## 2026-11-16: Discovery, recovery and timed operator help

Live read-only V2 inspect returned `Expected one unambiguous WindowHub workflow window; found 0`. This is before any reasoning or field writing. It may mean WindowHub is closed, minimized without top-level visible title, or has changed window titles. We must not guess which. `app/agent/runtime/windowhub_discovery_diagnostics.py` now reports only process/window class counts and a recovery category, without titles, customer data or HWND. The V2 runner calls this upon failed focus. `python -m app.agent.runtime.windowhub_discovery_diagnostics` can also be run alone, read-only.

`app/agent/runtime/goal_task_supervisor.py` provides:
- A dependency-aware `TaskLedger` with pending/verified/skipped/blocked states.
- An optional independent task can be skipped when unresolved, but required tasks and all downstream dependents are blocked.
- Minimal local JSONL audit records (task key, reason, outcome) through `append_unresolved_issues`. No customer details or screenshots.
- A nonblocking Windows `msvcrt` console prompt which returns after 60 seconds by default. A scripted test reader is supported for deterministic tests.
- The ledger does **not** yet automatically parse arbitrary natural language into dependency graphs or orchestrate skips in a live business mission. Failing to establish dependency should conservatively stop.

The V2 runner now has `--interactive-handoff --handoff-timeout 60` in execute mode. When model confidence is insufficient, it asks the salesperson and on consent restores WindowHub focus and reobserves. After a rejected/unverified step, the model receives a bounded failure record and can propose a different method; identical action on unchanged observed state is blocked. All cycles are limited by `--max-actions`. Do not confuse demonstration/consent with proof that the application business state matches the user's request.

Tests: `python -m pytest tests/test_goal_progress_memory.py tests/test_goal_task_supervisor.py tests/test_goal_v2_handoff.py tests/test_windowhub_dimension_replace.py -q`.

Tested on GitHub only by code review; local Pytest and live WindowHub must still run. V2 live execution requires the configured NaviMind V2 endpoint. It should not be enabled merely to diagnose a missing window.

## 2026-11-16: Goal relevance and print-template interference

Real read-only observation: 21 offline checks passed; WindowHub focused the `Okna - OFR/4678-` offer document, but its 64 available UI capabilities were dominated by print template labels, `Otwórz` and `Edytuj`. A visible control is not evidence that it belongs to the user's immediate task; we must not interpret a print-template editor as a window-construction editor.

- `app/agent/runtime/goal_affordance_ranking.py`: general natural-language relevance score (Polish diacritics, semantic labels, tiny domain synonym vocabulary), stable ordering of *existing* allowed affordances. Does not invent targets, execute clicks or certify an outcome.
- `ComputerUseV2ActionSession.prepare_cycle` now prioritizes task-relevant affordances before the strict V2 action budget can truncate the list. Unrelated controls are not treated as nonexistent: they remain discoverable subject to the cap.
- `windowhub_skill_knowledge` no longer hardcodes “create a new offer”. The live user's request is authoritative. Added guidance to distinguish print templates from construction and to avoid customer/new-offer detours for independent edits.
- `run_windowhub_goal_v2.py --mode inspect` prints `GOAL_RELEVANT_ACTIONS` and `GOAL_CONTEXT`, plus existing observation. Zero direct semantic overlap is a **diagnostic**, not proof that the task is impossible (navigation might still be required).
- Unit checks: `tests/test_goal_affordance_ranking.py` and `tests/test_windowhub_goal_specific_knowledge.py`.

Current limitations: ranking != understanding of which MDI panel/dialog is active; that requires structural UIA provenance and stronger action-specific business outcomes. Never choose `Edytuj` solely by text: it may be the print-template editor. V2 `think` requires a configured reasoning endpoint. Do not run unverified `--mode execute` on production records.


## Active panel understanding, 2026-11-16

Latest user evidence: `17 passed`, WindowHub process exists, one visible titled window with an unfamiliar title, and V2 read-only inspect returned EXIT_CODE=3 before any perception.

New `app/agent/runtime/active_panel_context.py` infers:
- the one UIA `tabitem` explicitly reporting `uia_selected=True`;
- the UIA control reporting `uia_focused=True`;
- named parent containers from the UIA ancestor chain (panel, group, tab, window);
- the closest container(s) shared with the focused control, as a better indicator of active pane context.

These indicators now adjust the order of *already authorized* affordances in `ComputerUseV2ActionSession`. Model-facing `panel_model_context` contains only recognized generic panel category names, never arbitrary customer/project panel titles or private native IDs. Selection/focus are not authorizations and are not inferred from visibility alone. Action ranking is not a business-task completion signal.

New read-only recovery: in V2 `--mode inspect` only, an unknown WindowHub title can still be inspected if `Okna.exe` is already foreground, or the runtime can focus exactly one visible, non-minimized `Okna.exe` top-level window regardless of title. This **does not** enable unknown-title think/execute actions. More than one candidate fails safely.

Unit tests: `python -m pytest tests/test_active_panel_context.py tests/test_goal_affordance_ranking.py tests/test_windowhub_goal_specific_knowledge.py tests/test_goal_progress_memory.py -q`.

The new code is committed to the integration branch; local offline tests and a live unknown WindowHub screen observation have NOT yet been run by the user. If the runtime cannot expose selected/focused UIA states or ancestry, it will report low-confidence panel context instead of making a confident claim. Next architectural task: confirm correct hierarchy in the user's application and create contextual local skill activation after field-specific readback and human supervision.


## 2026-11-16: Active focus ambiguity and contextual skill choice

Live evidence from user's `OFR/4680-`: 19 offline tests passed; one selected tab, **six** apparent UIA-focused controls, 137 ancestry-scoped controls; 64 action capabilities, only one direct goal-relevant target. Earlier ranking prominently exposed note/scroll controls rather than a verified window-construction entry.

Changes:
- `active_panel_context.py` distinguishes a genuinely unique focused control from 2+ ambiguous UIA focus markers; ambiguous focus no longer gives an action priority boost or claims a known active area. Selected tab and contextual hierarchy remain independent evidence.
- `goal_affordance_ranking.py` decomposes direct label relevance and panel evidence. Generic scrolling/table navigation receives a low rank unless the request explicitly mentions it. Generated affordance descriptions never independently certify semantic meaning.
- `run_windowhub_goal_v2.py --mode inspect` now emits the five best candidates with separate `DIRECT`, `PANEL` and `TOTAL` scores, as well as the total number of direct matches and panel-context matches. This is read-only explanation, **not** a decision to click.
- `windowhub_semantic_world.py` attaches the established business meaning `Dodaj nową pozycję okna do oferty` only to a unique, active, UIA-enabled `Dodaj` button on an existing `Okna - OFR/...` document, excluding controls in recognizable print-template ancestry. Native labels and identifiers remain local and unchanged for execution. This capability is a candidate, not proof that a new position was created.
- Added offline tests for focus ambiguity, goal relevance, scrolling penalty, contextual skill labeling, and rejection of print-template controls.

No model call or real WindowHub click was performed during development. Next acceptance: run the read-only inspection against the existing offer, review `GOAL_CANDIDATE` scores, and only then try `--mode think` if NaviMind V2 is configured, with no desktop actions.

# WindowHub Agent Execution Milestones

This document tracks the path from verified navigation to controlled execution of a complete user-requested workflow.

## Verified checkpoint (2026-10-28)

- The native MDI activation path for the Start1 document tab has been exercised in the real WindowHub process. The current integration branch contains PR #157.
- PR #158 adds handling for legacy UI Automation tab providers that do not expose SelectionItemPattern. The PR workflow reports success for commit `fa03a705778ab96343fa4be271ab6dfa46477eb0`; confirm the PR/branch status before assuming these changes are present in the integration branch.
- `tools/live_windowhub_new_offer_open_smoke.py` is a supervised, single-action live test. It requires WindowHub, a configured task reasoner, `WH_REAL_WINDOWHUB=1`, and `COMPUTER_REAL=0`. It permits one semantic click on a unique UIA-grounded NOWA OFERTA button and then checks for the owned dialog. It does not enter data or save.
- CI tests cover the smoke's preflight and plan guard. CI does not prove the dialog opened on the user's desktop.

## Immediate acceptance sequence

1. Confirm the PR #158 changes are in the local checkout and the integration branch state is up to date.
2. Run the focused guard test suite.
3. On the real Windows desktop, run `tools/live_windowhub_new_offer_open_smoke.py` with the explicit environment flags documented in the repository. Before running it, close any existing new-offer dialog and leave Start1 active.
4. Accept the step only when the JSON report says `result=PASS`, `action_executed=true`, `execution_success=true`, and `new_offer_dialog_detected=true`. Keep the dialog open for the next supervised field-inventory step. Do not click OK, Cancel, or Save as part of this milestone.
5. If it aborts or fails, diagnose the reported blocker from observed evidence. Never weaken target uniqueness, document-scope, visibility, enabled-state, active-document, or post-action checks just to obtain a PASS.

## Next implementation milestone: controlled field actions

Once the dialog-opening milestone passes locally:

- Observe and inventory the dialog's real UIA controls, labels, control types, enabled/visible state, field identity, and ownership.
- Select one low-risk, reversible field (prefer a plain text or numeric field in a disposable draft); verify exact pre-state and target scope.
- Add a single-field live smoke with one write action and a fresh post-action observation. Require the observed value to equal the exact requested test value; do not save.
- Add tests for duplicate/ambiguous labels, wrong active dialog, stale target, missing value evidence, focus mismatch, typed-value mismatch, and no coordinate-click fallback.
- Only then allow bounded multi-step execution. Keep a maximum step/action budget, re-observe after every mutation, verify each postcondition, checkpoint state, and stop for human review whenever evidence is missing or mismatched.

## Definition of useful autonomy

For each step, the agent must demonstrate:
`goal -> observe -> reason about next action -> local policy/target validation -> one action -> observe -> verify -> checkpoint`

The agent must not report completion merely because a tool call returned success. Completion must be supported by the resulting application state. Consequential actions (save, send, accept, submit, price confirmation) remain separately gated until their semantics and outcome can be independently verified.

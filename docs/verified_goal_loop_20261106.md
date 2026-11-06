# WindowHub verified-goal loop — isolated core, 2026-11-06

Status: CORE ONLY, NOT WIRED TO LIVE DESKTOP. The local uncommitted files listed by the operator have not been read or overwritten. This branch does not authorize any live action.

## Verified existing pieces (remote snapshot)
- `tools/run_windowhub_goal_v2.py`: document intake, task goal, NaviMind V2 decision, verified local action.
- `app/agent/runtime/windowhub_goal_v2_coordinator.py`: resolves UIA identity, guards persistent actions, verifies one action.
- `app/agent/runtime/verification_loop.py`: fresh perception after performed actions.
- Local-only reported: `app/agent/visual/`, `adaptive_goal_runtime.py`, `reactive_customer_loop.py`. Their actual content must be reviewed before integration.
- NaviMind `app/api/agent/task/route.ts` is V2 semantic endpoint. The visual endpoint used by the operator may be on a deployment/branch not represented by the remote main tree.

## Core contract
`run_verified_goal(observe, decide, execute, verify_action, verify_goal, fingerprint)`
- Observe relevant foreground WindowHub state (UIA / Win32; vision fallback only).
- Decide with NaviMind given current observation and sanitized previous outcomes. Convert a validated model response to `GoalDecision`.
- Resolve a step's semantic target **locally** against the current observed UIA element; never trust stale coordinates or native IDs from the model.
- Execute exactly one locally approved action.
- Observe again. Verify the *exact postcondition* of that action. Do not retry failed actions blindly.
- Independently verify the *goal*, not just a model "done" declaration.
- Stop on any ambiguous verification, repeated identical action in unchanged state, action budget or unapproved persistent operation.

## Planned safe integration (not yet implemented)
1. Read and preserve local working-tree changes and visual driver. Map them to the six callbacks, reusing `execute_v2_step` and existing `VerificationLoop`, not creating another executor.
2. Add value-centric task plan, e.g. `width=1500`, `height=1400`, `glass=triple`, `client=...`; each field has a supported mapping or is marked blocked.
3. Make `verify_goal` check required fields through WindowHub readback. No "verified" if any required field is unobservable.
4. For vision-only elements require fresh screenshot, correct image scale/DPI, foreground/window bounds, protected action policy and post-action verification.
5. First live acceptance scenario: disposable offer draft; type width 1500, read it back as 1500, stop. No save, send, submit or customer creation.
6. Only then expand to full draft generation with operator confirmation before persistence.

## Tests
`python -m pytest -q tests/test_verified_goal_loop.py`
These use fake adapters. Passing proves control-flow behavior, **not** correct WindowHub interaction or compatibility with local uncommitted modules.

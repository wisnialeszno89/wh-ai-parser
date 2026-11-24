# NaviMind: human/agent shared control contract

Human control has priority over autonomous execution in all environments.
The pure controller in `app/agent/runtime/navimind_human_handoff.py` is tested
without Windows and must eventually be adapted to every desktop provider.

## Operator interaction

- **Take over:** interrupt before the next atomic GUI action. Increment the
  ownership epoch; invalidate every queued pre-interruption model proposal.
- **Work manually:** do not execute autonomous mouse, keyboard, clipboard or
  window-activation actions. Preserve mission goal, readback history and
  previously observed documents.
- **Release:** give control back without executing an old action. On the next
  scheduler tick, freshly inspect foreground application, exact document,
  active position and required fields.
- **Continue automatically:** if no conflicting manual edit occurred, plan
  from independently observed state and skip previously completed operations.
- **Changes by operator:** preserve the hand-edited price, description, image
  or position, raise a precise review event and do not overwrite anything.
  Operator may approve revised requirements through a separate replan and
  tests before autonomous execution. An acknowledgement alone is insufficient.
- **Missing/unavailable document:** keep the mission paused. Do not guess the
  intended customer or open another offer merely because it is in front.

## Concurrency and integration requirements

- The epoch gate MUST be rechecked immediately before each real GUI operation,
  not just before calling a remote reasoner.
- Do not interrupt partway through an atomic native action. Finish its
  postcondition observation before releasing application control.
- Human takeover should be available even during model reasoning: stale
  results are discarded by the epoch check rather than executed.
- Use a single local input arbiter for keyboard, mouse, clipboard and window
  focus; the model cannot unilaterally reacquire control.
- A pause/resume button must not authorize saving, sending, ordering or
  deleting documents.
- No background monitoring, desktop hooks or live concurrency adapter is
  implemented by this PR.

## Offline test

```bash
python -m pytest -q tests/test_navimind_human_handoff.py \
  tests/test_navimind_virtual_desktop_workspace.py \
  tests/test_navimind_virtual_windowhub.py \
  tests/test_navimind_mission_coordinator.py \
  tests/test_portable_editor_skills.py \
  tests/test_windowhub_commercial_quote_routes.py \
  tests/test_navimind_evidence_decision_engine.py \
  tests/test_windowhub_sales_mission_review.py
```

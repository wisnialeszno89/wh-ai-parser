# NaviMind V3 shadow audit of existing V2 runner

## Purpose

This branch adds a strictly **advisory** V3 comparison at the existing
model-response boundary in `tools/run_windowhub_goal_v2.py`. It does not
replace the V2 action resolver, protected-action policy, visual verification,
or live Windows executor.

The V2 model returns its usual response. The shadow evaluator receives only
the already-available capability list, local stage and response, then prints
bounded, sanitized diagnostic fields. It never alters the model response and
never calls the GUI executor. No client values, names or raw refs are logged
by the new module.

## Safety and uncertainty

- `--decision-shadow` is opt-in and defaults to disabled.
- It produces output in `think` or `execute` modes (not `inspect`, which
  intentionally returns before asking the model).
- The shadow logic flags save/send/order actions and missing document
  identity; this comparison is **not** a substitute for V2's stricter
  application-specific native policy.
- Document identity is considered locally confirmed for shadow only with
  an explicit matching `--expected-offer` caption in `offer_document`.
  Other stages remain conservative until a verified ancestry adapter exists.
- The shadow stage assumes the fresh scene read immediately before the V2
  request; it is **not** independent proof that the UI remained unchanged
  while awaiting a remote model response.
- V3 cannot yet decide every native WindowHub UI action. A disagreement is a
  diagnostic for review, **not** evidence that V2 did something wrong.
- Existing Windows live-execution authorization flags are unchanged.
- Memory-mission learning in the parent branch is still an offline preflight
  module; this patch does not automatically inject customer or learning data
  into the V2 request.

## Tests in Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_v2_shadow_audit.py \
  tests/test_navimind_memory_mission_bridge.py \
  tests/test_navimind_versioned_rule_memory.py \
  tests/test_navimind_memory_decision_bridge.py \
  tests/test_navimind_correction_rulebook.py \
  tests/test_navimind_human_handoff.py \
  tests/test_navimind_virtual_desktop_workspace.py \
  tests/test_navimind_virtual_windowhub.py \
  tests/test_navimind_mission_coordinator.py \
  tests/test_portable_editor_skills.py \
  tests/test_windowhub_commercial_quote_routes.py \
  tests/test_navimind_evidence_decision_engine.py \
  tests/test_windowhub_sales_mission_review.py

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_v2_shadow.py
```

## Supervised Windows acceptance — later

After moving to Windows, activate `--decision-shadow --mode think` on a
disposable test offer, retaining all existing authorization requirements.
Record disagreements and reconcile against actual UI controls and verified
document identity. Do not use `--mode execute` until a separate supervised
acceptance approves the action scope; no permission is implied by shadow mode.

## Next implementation gates

1. Derive authoritative selected-document identity and action ancestry from
   the local Windows UI, rather than broad stage assumptions.
2. Correlate pre-model vs post-model observation freshness.
3. Wire approved, scoped rule suggestions as limited evidence at the V2
   payload planning boundary, not as raw GUI instructions.
4. Validate human takeover epoch immediately before actual native action.
5. Test end-to-end on Windows with fully disposable drafts and no
   autonomous persistence.

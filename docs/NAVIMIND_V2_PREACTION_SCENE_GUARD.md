# NaviMind V2 — pre-action scene guard (offline and Windows integration)

## Zasada

The V2 runner now retains the *raw scene observed before reasoning*. It still
uses the existing enriched scene, V2 model, semantic target resolver, native
local policy and verified outcome executor.

Only for an EXECUTE operation, the runner passes `pre_model_scene` to
`execute_v2_step()`. Before any native GUI action, the coordinator requests
a NEW independent observation of the current desktop. The proposed action is
rejected if:

- The process is no longer `Okna.exe`.
- The foreground title or window handle differs.
- The selected offer tab differs, is ambiguous or is missing in an OFR scene.
- The WindowHub wizard stage changed while the model reasoned.
- A visible UIA control's identity, label, current value, enabled state,
  focused state, selection or supported document scope changed.
- Reobservation fails or the scene is malformed.

If the scene is unchanged, V2 **still** applies its existing local action
policies and postcondition verifier, now against a freshly enriched scene.
This comparison adds no new autonomous persistence permissions. The
`--decision-shadow` comparison remains observational.

## Deliberate limitations

A scene fingerprint is **not a lock**. The operator could change the desktop
and restore it to an indistinguishable state (ABA), or input could arrive
between the final observation and a native click. Real shared-desktop
operation requires a single local input arbiter and ownership epoch check
at the native action dispatch boundary. The current patch does not implement
these capabilities, true automatic pause/resume, or perform a live test.

This guard may conservatively reject valid actions if UIA observation
produces different runtime IDs or focus changes; conservative failure is
preferable to editing a different customer's offer. It will demand a unique
selected tab for offer-document stages. The operator should then inspect
UIA tab recognition, **not** disable the guard.

No raw names, prices, controls or customer values are logged by the guard:
only bounded reason codes such as `preaction_uia_state_changed` are returned.
The snapshot fingerprint remains in process memory.

## Codespaces acceptance

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_v2_preaction_scene_guard.py \
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
```

## Live acceptance gate

Do not perform a live WindowHub test until a real Windows machine has a
disposable offer, the operator is present, and the action is explicitly
approved. The first supervised test should compare two read-only scenes
across a staged offer switch. Next check the existing V2 `--mode think`
without issuing GUI actions. Only then consider an isolated, reversible GUI
action using the standard V2 permissions.

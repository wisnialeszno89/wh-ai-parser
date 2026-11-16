# WindowHub unified core integration — 2026-11-16

Integration home: `integration/windowhub-live-acceptance-20261116`. Do **not** merge all historical feature branches into main: many are already ancestors, others diverged. A live WindowHub end-to-end success has **not** been established yet. NaviMind/Vercel changes are frozen.

## Current executable entry

`python tools/run_windowhub_sales_offer_live.py --customer-name "Limi Fensterbau" --quantity 1 --width 1500 --height 1400 --color-outside "antracyt" --color-inside "biały" --glazing-panes 2 --execute-live`

Stages:
1. Auto-find WindowHub and inspect current stage.
2. If on `document_properties`, resume **without creating a duplicate offer**.
3. If on Start1 or an existing offer workspace, use the verified Start1 tab and New Offer route.
4. Reuse native exact-customer search (short prefix chunks and unique result).
5. In the unified `windowhub_document_core`, set all four requested checkbox states: construction price visible; installation, removal, finishing prices excluded.
6. **Only if exact customer commit is proven and all four flags have fresh UIA readback**, click the document's one uniquely resolved OK button and verify reaching the editor or position stage.
7. On the offer editor, try one uniquely verified `Dodaj` toolbar action, verify position wizard; then populate and read back quantity and 1500×1400 mm dimensions.
8. Color and glazing selection in the real WindowHub catalog, hardware/opening, and saving the final offer are **not yet proven**. Do not misreport them as done.

## Diagnostic observations

- On 2026-11-16 real WindowHub test confirmed `OFR/4670-` → `Start1` through an actual UIA `tabitem` and New Offer → `document_properties`.
- Exact customer result `Limi Fensterbau` found once and clicked, but the proprietary `LookUpEdit` did not expose a native committed value; prior script stopped before price flags. That does **not** establish client commitment and is not a reason to select a random row.
- New document core can proceed to *independently verified* four price switches even when the client commit signal is inconclusive; it leaves the dialog open instead of confirming a possibly wrong client.
- The old `tools/run_windowhub_top_trans_single_window_mission.py` logs a demo `TARGET` even with `--customer-name Limi Fensterbau`. The new entry no longer delegates the business mission to this demo runner; it reuses verified lower-level skills only.

## Repository consolidation

Historical branches `feat/windowhub-order-preferences-20261109`, `fix/window-enquiry-completeness-20261113`, `feat/windowhub-teach-and-reason-v1-20261104`, `feat/windowhub-intent-driven-offer-v1-20261104` and `fix/windowhub-v2-generic-control-capabilities-20261105` were checked and are ancestors of the integration branch; remerging them adds nothing.

The user's original worktree has valuable **uncommitted** `app/agent/runtime/adaptive_goal_runtime.py`, `verified_goal_loop.py`, and other local-only files. Their content is not on GitHub and has not been incorporated. Keep that tree intact; integrate them after a deliberate clean-source import/review, never through git clean/reset.

## Validation gate

`python -m pytest tests/test_windowhub_new_offer_action.py tests/test_windowhub_navigation_verification.py tests/test_windowhub_sales_offer_live.py tests/test_windowhub_document_core.py -q`

Offline test success proves safety policies/branch wiring, not successful live execution. In actual WindowHub, confirm individual stage transitions, selected customer identity, the four price flags, `Dodaj`, position dimensions and catalog options through readback.


## Incremental autonomy, teaching and screenshot policy

- New unified invocation supports `--interactive-handoff` (explicit opt-in). When the DevExpress lookup hides the selected customer value, the agent configures all four observable price switches and requests **exact customer-name confirmation**, then asks whether to **continue from the current stage**. This is recorded as `human_explicit_confirmation` rather than falsely claiming a native UIA customer readback. On refusal, it does not click OK.
- Batch policy: the four independent document-price checkboxes are inspected from one semantic UIA scene. Each change binds a fresh native control and checks live foreground plus TogglePattern state, then one full semantic observation verifies all four desired values together. Do **not** apply this to navigation, destructive actions, client search, or changing dependent catalog menus. Failure stops the batch; no blind retry.
- The main entry can resume from an already open position, dimensions, basic-parameters or glazing wizard only after explicit confirmation of the customer and permission to resume; it checks stage again after the handoff. If the current scene is document properties, it resumes that dialog without creating a duplicate new offer.
- After verified 1500×1400 dimensions, `windowhub_catalog_continuation` uses existing exact native Next/ComboBox skills for the basic-parameters and glazing screens, reading back state after each selection. The known `antracyt outside / biały inside` options are *two-sided*, not an unrestricted `antracyt` match. If WindowHub exposes a different exact label, fail closed and offer teach mode.
- `windowhub_catalog_handoff`: user can select an exact catalog item manually, choose whether to record the observed label in local `~/.windowhub_agent/verified_catalog_skills.json`, then explicitly approve resuming. The agent re-observes the stage/value. This is a verified expert demonstration, **not** proof that the agent autonomously operated that catalog option; next autonomous selection must still be validated.
- `hardware` is a verified wizard stage but **not** synonymous with a completed frame/sash construction editor. Do not claim offer completion, save, or final WindowHub calculation.
- No Vercel deployment or production sync. No automatic background desktop watcher; prompts appear during an actively running `--interactive-handoff` mission only.

Validation:
```powershell
python -m pytest tests/test_windowhub_new_offer_action.py tests/test_windowhub_navigation_verification.py tests/test_windowhub_document_core.py tests/test_windowhub_sales_offer_live.py tests/test_windowhub_catalog_memory.py tests/test_windowhub_catalog_handoff.py -q
```


## Interactive mission command (current continuation)

```powershell
python tools/run_windowhub_sales_offer_live.py --customer-name "Limi Fensterbau" --quantity 1 --width 1500 --height 1400 --color-outside "antracyt" --color-inside "biały" --glazing-panes 2 --interactive-handoff --execute-live
```

- When in Document Properties, do not create duplicate new offer.
- The customer form remains opaque to UIA until either a native exact selected-value readback or an explicit human confirmation is available. The interactive handoff requests the exact full company name and separate resume approval. Human approval is not mislabeled as native evidence.
- **Focus restoration is part of every interactive handoff.** The terminal takes foreground during input. Agent must reactivate the existing WindowHub process before inspecting customer, catalog or hardware states.
- After validating 4 pricing flags and exact customer, OK is invoked once through unique native identity, followed by stage readback.
- The goal runner then invokes the verified `Dodaj` toolbar, position and dimension skills, and attempts exact two-sided color and glazing catalog options.
- At unavailable catalog options, user may demonstrate and approve recording an exact UIA readback label. With explicit resume permission, the same running process continues; future runs read the local skill memory.
- At the hardware wizard, human may demonstrate the move to the `Modyfikator` editor, then agent verifies the editor stage and asks whether to resume. This is **not** automated hardware configuration or a completed offer. The final offer is never saved.
- Screenshots are batched only for independent pricing fields, with per-toggle native live checks and a single post-batch full UIA readback. Do not batch dependent stages or customer selection.
- This code is committed, but its updated offline suite and live WindowHub flow are awaiting execution on the user's machine.

Run:
```powershell
python -m pytest tests/test_windowhub_new_offer_action.py tests/test_windowhub_navigation_verification.py tests/test_windowhub_document_core.py tests/test_windowhub_sales_offer_live.py tests/test_windowhub_catalog_memory.py tests/test_windowhub_catalog_handoff.py -q
```


## Native dimension replacement — regression 2026-11-16

Observed live: Position wizard reached `Wielkość okna` but legacy generic `WRITE` issued Ctrl+A and `1500` twice (the generic control loop automatically retried after a postcondition failure). The desired first width was not verified; default dimensions 1000×1000 had been present. The screenshot log does not prove whether the underlying cause was append, focus, or commit semantics, therefore do not assert one cause.

The unified mission now delegates width/height edits to `app/agent/runtime/windowhub_dimension_replace.py`. It:
- reads the actual current value from exactly mapped `width_1`/`height_1`;
- skips a field already equal to the requested dimensions;
- blocks if current value is unreadable;
- freshly rebinds one native UIA Edit by automation ID, runtime ID and exact bounds, confirming foreground `Okna.exe`;
- compares native ValuePattern value with the fresh semantic observation, checks editability, then calls **SetValue** once to replace the complete existing value;
- performs up to three *readback observations* to handle UIA propagation without a second input;
- stops instead of retrying input or appending if postcondition cannot be proved.

Run regression: `python -m pytest tests/test_windowhub_dimension_replace.py -q`.
Resume a verified wizard in interactive mode with the normal unified mission, without creating a new offer. A requested 1500x1400 change does not touch extra width/height slots 2–5 (skos geometry).

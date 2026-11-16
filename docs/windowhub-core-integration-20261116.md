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

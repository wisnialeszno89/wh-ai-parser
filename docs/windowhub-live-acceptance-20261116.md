# WindowHub LIVE acceptance — 2026-11-16

Integration branch: `integration/windowhub-live-acceptance-20261116`, created from `fix/window-enquiry-completeness-20261113` after the v2 offer-specification merge (#191). The ancestry includes order preferences from PR #189. This is **not** a verified live WH integration nor a production release.

## Operator safety

1. Start WindowHub on Windows and enter a disposable/test document only. Never use a real order or customer without permission.
2. Check `git status --short` before changing branches; preserve local changes. Never use `reset --hard` or `git clean -fd` as a shortcut.
3. Use an isolated, synthetic four-row preferences CSV with UTF-8 encoding.
4. Run `python tools/live_windowhub_new_offer_mission.py --preferences-file <path> --inspect-preferences` first (no UI actions).
5. For a visible WH test, use `--customer-mode select --customer-name 'Top Trans' --preferences-file <path> --quantity 1 --width 1500 --height 1400 --execute-live`. Only after confirming this is a test record. The runner must verify the exact selected customer and preferences, stop if it cannot, and must not claim to have saved an offer.
6. Record the ending status codes and relevant UIA control labels (without client details or screenshots containing private data). Re-run the same objective after each fix.
7. Run offline regression separately with `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_navimind_regression.ps1`. The PAGEN lab is separate and is not evidence of WH behavior.

## Gate for a genuinely complete WindowHub offer

- Exact customer selected, verified by current UI.
- Four price preferences match the specified CSV.
- Position wizard entered; window type, profile, quantity, width and height verified on screen.
- Construction, opening direction, color, glass and fittings match the source and catalog. Unsupported choices cause review, not silent substitution.
- Only with explicit test-save approval: draft saved, reopened, and every field read back.
- No claims of E2E completion from offline tests, browser fixtures, or synthetic flows.

The NaviMind Vercel frontend is maintained in the separate `navimind` repository. A Vercel READY deployment does not establish local Windows/WindowHub execution.

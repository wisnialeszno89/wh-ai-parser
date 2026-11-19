# Acceptance task — Top Trans Janik Artur, photographed enquiry

**Status:** Parsed and validated mission fixture; **not executed in Windows**.
Source upload: `obraz(20261119-130807).png` in conversation (image bytes are not in repository).

## Exact operator order
- New offer via Start1 → NOWA OFERTA, existing customer **Top Trans Janik Artur**; do not select source quotation's Hartmut Zingelmann.
- Perfectline PVC, **external anthracite only**, inside white, double glazing.
- 4 windows, 1 each; after verifying the German handwritten `ohne Fußleisten!`, exclude the 30-mm bottom strips:
  1. **1640 × 1010**, two leafs 820+820, marked top box
  2. **1020 × 1010**, one sash, marked top box
  3. **1180 × 950**, one sash, no box (drawing also shows 980 incl. bottom strip)
  4. **880 × 980**, one sash, no box (drawing also shows 1010 incl. bottom strip)
- 20% **window** discount; top-box positions with **no price**.
- Top boxes only for window positions 1 and 2. Determine complete dimensions from actual installed catalogue and verified sizing rule; do not invent heights.
- Verify opening/view/sash types against source; drawing alone is insufficient for an unqualified technical assertion.
- The agent may pick an alternative only if live dealer catalogue availability, technical compatibility, and functional suitability are demonstrated. Record every divergence.
- If it cannot construct, leave an unfinished dimensioned position when the program actually supports that operation.
- **No save before salesperson review.** End with an open working offer and a report.

## Offline preparation
```powershell
python tools/prepare_windowhub_enquiry_mission.py --out reports/top-trans-preflight.json
python -m pytest tests/test_windowhub_top_trans_enquiry_mission.py -q
```

Both are **offline**; neither creates a WindowHub offer. The existing two-position
test runner does **not** implement this full 4+2 mission, and should not be
mistaken for acceptance.

## Live acceptance not yet implemented
- Add mission JSON task-intake to the NaviMind V2 plan/execute/reobserve loop.
- Feed actual customer lookup proof and dynamically recognize 4 window positions.
- Handle optional roller positions through a verified WindowHub capability path.
- Verify 20% in the correct **window** pricing dialog, not on every added position.
- Ensure every executor path forbids save, send and order actions (including menus
  and keyboard shortcuts) until human review.
- Produce real completed/partial/substituted evidence per position, never claim
  GUI success from an offline preflight.

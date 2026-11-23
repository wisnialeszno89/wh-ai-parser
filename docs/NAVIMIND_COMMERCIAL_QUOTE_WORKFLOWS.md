# NaviMind: commercial quotation != production approval

The operator's sales practice is an intentional supported workflow. WindowHub
can be used to prepare a draft quotation even when the exact product cannot be
built directly from an available catalogue system.

## Route selection

1. If a requested construction is verified in the current installed catalogue,
   plan a normal catalogue position.
2. Otherwise, when WindowHub has a confirmed editable description field and
   a verified ability to create a blank representative construction, prepare
   a **descriptive placeholder**. For example, 1000 × 1000 mm may represent
   a pricing/description slot while the customer's requested 2300 × 2700 mm
   appears explicitly in the position description. These are never mixed.
3. If a representative construction is inappropriate, choose an actual
   **text-only position** when the installed WindowHub UI supports it.
4. If neither route is verified, request targeted salesperson assistance.
   Do not improvise an unobserved UI control.

## Evidence and safety

- Manufacturer guidance, warranty conditions, construction limits and
  unverified compatibility are **reported** under the relevant item.
- Preparing an out-of-warranty or technically atypical **quotation** is allowed;
  this never authorizes production, save, dispatch or order conversion.
- A warranty statement needs a real, inspectable source. Unknown warranty
  status is not silently treated as compliance or noncompliance.
- Prices may come from the enquiry, a separate authorized price calculation or
  the salesperson. An ungrounded amount must not be invented.
- A picture may be attached only when the user has the right to use the asset
  and WindowHub insertion support has been independently confirmed.
- Descriptions can include transparent price breakdowns, exclusions, assumptions,
  supplier disclaimers, scope, and requested geometry.
- Every actual write to WindowHub must be followed by independent readback.
- Quotation plan != completed position. Neither is production approval.

## Existing UI evidence

The WindowHub form-map already lists radio item types:
- `Pozycja tekstowa` (automation id 1338)
- `Inne artykuły` (1333)
- `Inny artykuł (kalkulacja)` (1345)
- `Opis pozycji` combo/edit in the add-position wizard

These are previously mapped controls, **not proof** of the image insertion,
description field availability in every program version, price editing, or
that a representative construction can be safely committed.

## Implementation

- `app/agent/offers/windowhub_commercial_quote_routes.py`: offline pure route
  planner, technical reporting, manual-price and image capability gates.
- `tests/test_windowhub_commercial_quote_routes.py`: offline contract tests.
- `windowhub_training_context.py`: new operator-aligned context sent to V2.

## Future WindowHub acceptance

1. Test and register the exact live description control and independent readback.
2. Detect actual picture-in-description insertion UI (editor type, clipboard and
   image rendering, preservation of aspect ratio) on an approved test asset.
3. Identify and verify local manual price control and price breakdown semantics.
4. Demonstrate inserting a representative blank construction then prove that
   displayed customer geometry remains in the description and correctly
   reports technical deviations.
5. Produce final per-position evidence report, never save or send autonomously.

# Shared browser regression pack

The same `contracts/browser-regression-v1.json` is mirrored in NaviMind and wh-ai-parser. Both runners print its SHA-256. Compare the digests before treating their results as coverage of the same revision. Changes must update both copies.

Nine phases cover a four-command correction chain, a German command with centimetres and exact Top Trans S.A. selection, changing only the customer, ambiguous Top search, a missing height, and an unavailable green colour. Correction phases explicitly list writable fields. Rewriting a preserved field is rejected by the model evaluation even if its final value is unchanged. Missing inputs must produce an appropriate question; unavailable options must not be substituted.

## Windows command

From the current checkout in `C:\Users\HP\wh-offer-lab`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_navimind_regression.ps1 -InstallDependencies
```

The suite opens an owned Chromium laboratory, runs offer contracts and the offline offer pipeline, browser executor contracts, then the shared fixture replay. Use `-Headless` for unattended runs. The same PowerShell entry point is exercised by Windows CI. Reports are written to `Desktop\NaviMind-Praca\Testy-agenta`; `-OutputDirectory` overrides it. Browser reports use unique names, record individual cases and are read back after writing. Nonzero exits stop subsequent stages.

## What each check proves

| Check | Real model | Real Chromium | Scope |
|---|---|---|---|
| NaviMind build gate | Yes | No | Built API route, current snapshot refs, actual model decisions, receipts and correction history; positive completion and grounded clarification |
| Windows fixture replay | No | Yes | Field targeting, exact selection, readback, offscreen corrections, preview invalidation, preserved fields |
| Windows negative probes | No | Yes | Both similar clients are exposed, missing height blocks preview, green is unavailable; these probes do not prove AI clarification |
| User chat trial | Yes | Yes | Actual frontend, network, local bridge and owned Chromium together |

The first two checks cover complementary boundaries; they are not a combined unattended model-to-desktop test. They do not verify WindowHub, a supplier price, an offer document or any external submission. Model build checks use synthetic customer names only. Existing live PAGEN testing remains available separately.

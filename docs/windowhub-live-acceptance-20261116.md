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

## Salesperson-style adaptive offer contract

The new pure policy module `app/agent/offers/windowhub_salesperson_policy.py`
and tests `tests/test_windowhub_salesperson_policy.py` are included on this branch.
They are **not yet wired into the live WindowHub executor**. Their scope is
business defaults, safe routing recommendations, per-position state and report
contract; they do not click, write or save.

- Locate the running `Okna.exe` from Windows, observe a fresh scene and classify
  the active stage before choosing any action. Login is always operator-owned.
- If on Start1, create a new offer. If already in document properties, verify
  customer and document settings. When an offer/editor is open, continue only
  after establishing that it is the authorized offer; otherwise protect the
  unrelated document. Unknown screens require further observation rather than
  fabricated clicks.
- No specified profile color means white inside and out. A missing glass package
  means two panes. When an opening direction is not provided, the agent may
  propose one only using verified construction context and catalog capability;
  the proposal is recorded as an assumption. Never present a guess as a
  customer requirement.
- Process a multi-position request sequentially. Each position can become
  `complete`, `partial`, or `blocked`. Partial status requires readback of
  dimensions **and** an actual verified incomplete position placeholder. If
  WindowHub does not permit such a placeholder, report `blocked` and
  continue if a safe way to navigate to the next position exists.
- A saved draft is *not* verified merely because a click succeeded. Explicit
  permission, save and fresh readback are required. Never silently change the
  client's requested specifications.
- End-of-run report lists positions, assumptions, missing properties, and
  whether customer and saved draft were verified.

Offline policy test: `python -m unittest tests.test_windowhub_salesperson_policy -v`.
Before live integration, compare local-only `adaptive_goal_runtime.py` and
`verified_goal_loop.py` against the integration branch in a separate worktree.
Do not overwrite local changes or claim tests prove actual WH operation.


## 2026-11-18 — katalog i przejście do edytora

W próbie na `OFR/4494-` agent odczytał 124 pozycje koloru, wybrał
`BIAŁY CZARNA USZCZELKA` i odczytał tę samą etykietę po zmianie.
Uruchomił `Zakończ` z parametrów podstawowych. Operator zgłosił wejście
do kreatora okiennego. Automat odnotował `basic_parameters_confirmation_unverified`;
potwierdzenie przejścia przez automat pozostaje otwarte. Brak odczytu osobnego
formularza szklenia i brak potwierdzenia zapisu pozycji lub oferty.

Tryb `--from-start` testu `tools/run_windowhub_existing_offer_position_test.py`
obejmuje Start1, nową ofertę, dokładnego istniejącego klienta testowego,
cztery flagi cen i pierwszą pozycję do potwierdzonego edytora. Flagi ustawiają
widoczną cenę konstrukcji i wyłączają kalkulację montażu, demontażu i wykończenia.
Test wymaga odczytu powiązania z numerem OFR utworzonym przez przebieg.
Gdy instalacja przechodzi bezpośrednio do edytora, osobny krok szklenia oznacza
jako niezaobserwowany.


Próba od początku startuje z rozpoznanego Start1 albo z istniejącej oferty,
z której używa zweryfikowanej nawigacji do Start1. Otwarty kreator jest
oddzielnym stanem i zatrzymuje rozpoczęcie nowej oferty. Wariant akceptacyjny
wymaga antracytu na zewnątrz i bieli wewnątrz oraz odczytu dokładnego pakietu
4/12/4/12/4. Wejście do edytora bez odczytu pakietu to wynik częściowy.

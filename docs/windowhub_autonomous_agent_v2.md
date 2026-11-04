# WindowHub — agent od celu do wykonania (V2)

## Dlaczego zmieniamy sposób pracy
Nie programujemy już osobnego skryptu dla każdego kliknięcia. Wykorzystujemy istniejące komponenty:
`OfferContextParser`, NaviMind V2, `ComputerUseV2ActionSession`,
`AgentControlLoop`, UIA, OCR i executor. Oddzielamy:
1. **Cel handlowy** (co ma powstać).
2. **Aktualny świat** (co jest teraz na ekranie).
3. **Wiedza i doświadczenie** (które przyciski mają jakie znaczenie, jakie przejścia widzieliśmy).
4. **Propozycja decyzji** NaviMind.
5. **Lokalna zgoda i weryfikacja** (co wolno wykonać i czy efekt nastąpił).

Nie przepisujemy UIA na współrzędne w promptach. Identyfikator i geometria pozostają lokalnie.

## Pierwszy trening przez pokazanie pracy

```powershell
git switch feat/windowhub-teach-and-reason-v1-20261104
python tools/teach_windowhub_by_demonstration.py --seconds 240 --goal "Pokaż przygotowanie jednej oferty okiennej od Start1 do modyfikatora"
```

Po uruchomieniu operator przechodzi **ręcznie** całą sekwencję w WindowHub.
Narzędzie nie klika, nie przechwytuje klawiszy, nie czyta nazw klientów ani wartości wpisywanych do pól. Zapisuje tylko rozpoznane etapy i stany widocznych kontrolek do `outputs/agent_learning/windowhub-demo-*.jsonl`.

**Ograniczenie:** zmiana ekranu jest obserwacją, a nie dowodem, który przycisk ją spowodował. Wersja V1 nie jest automatycznym uczeniem modelu z wideo i nie odtwarza ruchów operatora.

## Agent rozumie zadania (NaviMind V2)

Bez serwera / bez wywołania modelu:
```powershell
python tools/run_windowhub_goal_v2.py --mode inspect --goal "Utwórz ofertę na 1 okno 1230x1478, jednostronny antracyt"
```

Po ustawieniu `NAVIMIND_AGENT_V2_URL` (+ opcjonalnego `NAVIMIND_AGENT_V2_SECRET`):
```powershell
python tools/run_windowhub_goal_v2.py --mode think --goal "Utwórz ofertę na 1 okno 1230x1478, jednostronny antracyt" --demo "outputs/agent_learning/windowhub-demo-PRZYKLAD.jsonl"
```

`--mode think` wysyła cel i semantyczny świat do **skonfigurowanego serwera NaviMind**, który proponuje następną czynność. Nie wykonuje wejścia myszy/klawiatury.

Po sprawdzeniu połączenia i zachowania na danych testowych:
```powershell
$env:WH_REAL_WINDOWHUB="1"
$env:COMPUTER_USE_LIVE="1"
python tools/run_windowhub_goal_v2.py --mode execute --execute-live --max-actions 6 --goal "Utwórz nową ofertę okienną"
```

Tryb execute jest eksperymentalny: każda akcja musi pochodzić z bieżącego UIA, mieć sprawdzalny postcondition, zostać odrębnie wykonana i zweryfikowana. Zapis rekordu wymaga jawnego `--approve-persistent` **wyłącznie w środowisku testowym**. Skuteczne kliknięcie bez weryfikacji nie oznacza sukcesu.

## Zadania tekstowe/PDF
```powershell
python tools/run_windowhub_goal_v2.py --mode inspect --task-file ".\zapytanie.pdf"
```
Pliki tekstowe oraz PDF zawierające tekst są obsługiwane lokalnie; skany i fotografie wymagają osobnej warstwy OCR/wizji. Nie zgadujemy brakujących wymiarów. W trybie think/execute treść zadania może zostać wysłana do skonfigurowanego NaviMind.

## Następne prace, w kolejności wpływu na produkt
1. Kalibracja semantycznej obserwacji w WindowHub (w tym weryfikacja aktywnego klienta oraz katalogu kolorów).
2. Nauka na demonstracjach poprzez nadzorowane, obserwowane przejścia i lokalną bazę sprawdzonych umiejętności — promowanie tylko potwierdzonych sukcesów.
3. Adapter dokumentów: pełny `OfferContext` z PDF/obrazu/tekstu, z pytaniami o brakujące parametry.
4. Głos: transkrypcja -> ten sam cel zadaniowy i ten sam plan (nie osobny agent).
5. Model wizyjny/computer-use API jako **wymienny provider** obok NaviMind; bez kopiowania wewnętrznych mechanizmów ChatGPT Work.
6. E2E: Start1 -> klient -> ceny -> pozycja -> wymiary -> jednostronny kolor -> modyfikator, 3 pełne przebiegi bez ręcznych kliknięć i bez błędnego zapisu do bazy.

## Bezpieczeństwo i prywatność
- Demostracje pozostają lokalnie w katalogu `outputs/` ignorowanym przez Git.
- Brak automatycznego powtarzania niezweryfikowanych kliknięć.
- Przed akcjami powodującymi trwały zapis wymagamy jawnej zgody.
- Dane klienta/ekranu mogą trafić do zewnętrznego reasonera **wyłącznie przy świadomym użyciu `--mode think/execute`**.
- Jeśli agent nie ma wystarczających dowodów, zatrzymuje się i raportuje brakującą umiejętność zamiast zgadywać.

## Testy
```powershell
python -m pytest tests/test_windowhub_semantic_world_bridge.py tests/test_windowhub_demonstration_learning.py tests/test_windowhub_goal_v2_coordinator.py tests/test_windowhub_task_document_intake.py -q
```


## Pakiet preflight bez serwera — na pierwsze uruchomienie

W PowerShell z katalogu projektu:
```powershell
git -c core.commitGraph=false -c fetch.writeCommitGraph=false pull --ff-only origin feat/windowhub-teach-and-reason-v1-20261104
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_windowhub_v2_preflight.ps1
```

Pakiet odpala testy kontraktu V2, lokalny syntetyczny cykl
`Observe → V2 protocol → proposed action → local UIA guard → verified scene change`,
bezpieczną diagnozę `.env` i raport z najnowszej demonstracji. Nie łączy się
z serwerem i nie klika. `PREFLIGHT_STATUS=LOCAL_CHECKS_PASSED` **nie
oznacza** jeszcze działającego NaviMind V2 w sieci.

Następnie przy otwartym WindowHub na Start1:
```powershell
python tools/run_windowhub_goal_v2.py --mode inspect --goal "Utwórz nową ofertę"
```

Szukamy `START_NEW_OFFER_GUARD=PASS`, który potwierdza nie tylko obecność
przycisku, ale też możliwość jednoznacznego lokalnego związania celu z UIA
**bez wykonania działania**. Jeśli wynik to `BLOCKED`, kod poda precyzyjny
warunek, który nie został spełniony.

## Po wdrożeniu NaviMind PR #26 (osobny, jawnie płatny test)

Serwer V2 używa wspólnego endpointu `POST /api/agent/task` z polem
`version="2"`. Konieczne są prawidłowe `NAVIMIND_AGENT_URL` i
`NAVIMIND_AGENT_SECRET` w lokalnym `.env` oraz poprawna konfiguracja
serwera. Nie umieszczaj sekretów w GitHubie ani w logach wysyłanych do czatu.

```powershell
python tools/probe_navimind_v2_server.py --reuse-shared-navimind-endpoint --allow-model-request
```

Test wysyła **jedną sztuczną scenę**, bez danych klientów, i żąda decyzji
modelu. Nie wykonuje żadnych kliknięć ani operacji na bazie; wywołanie serwera
może być płatne. Dopiero po `V2_REMOTE_CONTRACT=PASS` przechodzimy do
`--mode think` na prawdziwym WindowHub i ograniczonych testów `execute`.

Jeśli nie masz skonfigurowanego endpointu, uruchom najpierw
`python tools/diagnose_navimind_setup.py`, który nie wyświetla URL ani
sekretów. Nie wymyślaj adresów Vercel/serwera.


## 2026-11-04: Offline validated, production V2 connection pending

Windows operator confirmed:
- `34 passed in 9.94s`;
- `OFFLINE_V2_STATUS=PASS`;
- `OFFLINE_V2_UNCHANGED_REJECTED=True`;
- `OFFLINE_V2_CHANGED_ACCEPTED=True`;
- `PREFLIGHT_STATUS=LOCAL_CHECKS_PASSED`;
- `DOTENV_FILE=absent`, missing V1/V2 URL and secrets;
- `REMOTE_REASONING_STATUS=NOT_TESTED`.

NaviMind PR #26 CI now passes and GitHub reports it mergeable. The PR
is still **draft/unmerged**; green CI is not proof of deployed Production
secrets or server availability. The connected Vercel project must be checked
before a production deployment; never guess a deployment URL or echo secrets.

### Release checklist (no scripts touch production automatically)

1. Verify the Vercel project is really connected to `wisnialeszno89/navimind`,
   and determine which Git branch deploys to Production.
2. Verify **presence** of server-side Production `OPENAI_API_KEY` and
   `NAVIMIND_AGENT_SECRET` without exposing values. Set/rotate them in
   Vercel if needed.
3. After conscious approval, merge and deploy NaviMind PR #26. This introduces
   V2 in the *same* endpoint `POST /api/agent/task`, selected by
   payload `version: "2"`. V1 remains supported.
4. On the **local Windows machine**, with no existing `.env`, run:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\setup_navimind_v2_local.ps1
   python tools/diagnose_navimind_setup.py
   ```
   Enter the canonical **production Vercel URL** and the exact same secret as
   configured on Vercel. The prompt masks the secret, and the local file
   remains ignored by Git. The wizard refuses to overwrite existing `.env`.
5. **Only after V2 deployment**, authorize the optional, possibly paid, single
   synthetic request (without business/customer data):
   ```powershell
   python tools/probe_navimind_v2_server.py --allow-model-request
   ```
6. If `V2_REMOTE_CONTRACT=PASS`, open WindowHub on Start1 and run
   `--mode think` with the earlier demonstration. That is the **first
   genuine next-action decision test**. Test the live execution loop only
   after inspecting the proposal and using isolated/test customer records.

The local wizard does **not** deploy Vercel, does not verify the server, does
not generate new server credentials, and never prints the secret.

## Vercel — odczytany stan 2026-11-04 (bez pobierania sekretów)

Źródło: odczyt metadanych połączonego projektu Vercel.

- Projekt: `navimind`, repozytorium `wisnialeszno89/navimind`.
- Production: domena `https://www.navimind.app`, aktualny gotowy deployment
  `dpl_6zHRB4L6jr1EzZUPvFxMEr48kaJm`, commit main
  `0e4a5f74bfade425fae9a327969d9961788011bb` (**bez** PR #26).
- Preview V2: `dpl_DexY91UdCXgUoXAFqyoen7JqSFB2`,
  commit `ce83ef1e53784c8255857b7084b921510adf375c` gałęzi
  `architecture/agent-observe-act-protocol-v2`, status `READY`.
- Metadane projektu pokazują obecność `OPENAI_API_KEY` w Production i
  `NAVIMIND_AGENT_SECRET` w Production i Preview. **Nie** weryfikowano
  wartości ani poprawności tych sekretów.
- Ochrona SSO: włączona dla deploymentów z wyjątkiem domen niestandardowych.
  Podgląd `*.vercel.app` może wymagać uwierzytelnienia Vercel przed
  dotarciem do aplikacyjnego `/api/agent/task`.

### Ścieżka do pierwszej prawdziwej decyzji modelu

1. Dla *Preview* nie wyłączaj SSO ani nie publikuj `NAVIMIND_AGENT_SECRET`.
   Test wykonaj za pomocą uwierzytelnionego narzędzia Vercel (np. `vercel curl`)
   i sztucznego payloadu V2, a nie zwykłym lokalnym `requests.post`.
   Operacja modelu może generować koszty. Przygotowany Python
   `tools/probe_navimind_v2_server.py` nie obsługuje ochrony SSO; uruchom go
   przeciw Preview tylko po prawidłowym skonfigurowaniu dostępu.
2. Po weryfikacji Preview, przed produkcją uzyskaj zgodę na scalenie PR #26.
   Wdrożenie będzie wykonywało zapytania modelu na koszt właściciela.
3. Po wdrożeniu na Production użyj lokalnego kreatora
   `tools/setup_navimind_v2_local.ps1` (tylko gdy brak `.env`) z publiczną
   domeną produkcyjną i tym samym sekretem, który jest na serwerze. Kreator nie
   pobiera sekretu z Vercel automatycznie, nie weryfikuje go i nie tworzy nowego.
4. `--mode think` może zostać zweryfikowany na prawdziwym WindowHub.
   Do włączenia `execute` wymagany jest osobny test lokalnych akcji i
   zabezpieczenie trwałego zapisu danych.

Bezpośredni adres chronionego deploymentu nie jest publicznym API bez SSO.
Nie należy uruchamiać testu przeciw `www.navimind.app`, dopóki nie potwierdzono,
że produkcja rzeczywiście zawiera V2.

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

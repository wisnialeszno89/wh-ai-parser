# Pilot: screenshot → decyzja → działanie → nowy screenshot

## Aktualizacja po pierwszej próbie na Windows

Użytkownik potwierdził `VISUAL_CONNECTION=ready`, a po poprawce schematu serwera wykonawca przyjął 16 akcji `click`. Zadania nie ukończono: `step_budget_exhausted`, bez potwierdzenia poprawienia klienta. To dowód przejścia transportu i walidacji, nie poprawnego wyboru punktów ani osiągnięcia celu.

Poprawka pętli zachowuje w historii współrzędne i parametry akcji, mierzy przybliżoną zmianę obrazu, blokuje ponowne pobliskie kliknięcie bez efektu oraz powrót do podobnego stanu obrazu. Małe zmiany kursora nie są traktowane jako postęp; sama zmiana obrazu też nie potwierdza celu. Ta heurystyka może zatrzymać uzasadnione ponowne kliknięcie i wymaga oceny na żywym środowisku. Weryfikator celu pozostaje niezależny.

Domyślny limit próby wynosi 8 decyzji. Opcjonalne `-TraceDirectory` zapisuje lokalnie obrazy i JSON proponowanych akcji z punktem żądanym na pulpicie; nie zapisuje adresów API, nagłówków ani sekretów. Ślad dotyczy wyłącznie fikcyjnego laboratorium. W nim `proposed_action` jest propozycją, a nie dowodem wysłania wejścia; wykonanie i blokady potwierdza log.

Walidacja tej poprawki: 31 testów jednostkowych oraz 1 test lokalnego HTTP, także przy ustawionym obcym linku Preview w środowisku. Nie potwierdzono jeszcze sukcesu poprawionej pętli na Windows.

## Stan dostarczenia

Kod klienta przygotowano na bazie `wh-ai-parser` HEAD `2850827b02a9dd5d66f5bf0e222170980c9efe87`, obok wcześniej nałożonych poprawek V1–V5. Nowy pakiet dodaje pliki; nie zastępuje poprzednich pętli. Serwer przygotowano na `navimind` HEAD `e9f9501a85d3aa5a0ac237a808927fb8d6561fcd`.

Kod przygotowano do przeglądu w osobnych draft PR-ach. Nie wykonano merge, zmian konfiguracji produkcji, odczytu sekretów ani zapytań do rzeczywistego modelu. Podgląd gałęzi na Vercel jest gotowy; endpoint włączono wyłącznie dla gałęzi testowej. Dostęp z klienta musi przejść przez ochronę podglądu. Nowe pliki pilota nie wymagają wcześniejszych lokalnych poprawek V1–V5.

## Co jest nowe

- Osobny protokół `visual-1` i endpoint `POST /api/agent/visual-task`.
- Model dostaje PNG jako `image_url`, a nie sam OCR ani opis kontrolek.
- Cel jest podawany jako wynik do osiągnięcia. Nie ma w nim współrzędnych ani kolejności klikania.
- Narzędzia: kliknięcie, wpisanie literalnego tekstu, ograniczone klawisze, przewinięcie, oczekiwanie i przybliżenie fragmentu.
- Po każdej czynności następuje nowy screenshot i nowa decyzja modelu.
- Podstawowa wiedza obsługi komputera jest w instrukcji systemowej serwera; zawartość ekranu jest danymi.
- Sterownik lokalny mapuje współrzędne obrazu na właściwe okno, w tym po powiększeniu fragmentu. Kontroluje PID, HWND, aktywne okno, położenie i proces pod punktem kliknięcia.
- Nieaktualny obraz blokuje wykonanie. Identyczna czynność na niezmienionym obrazie wraca jako brak postępu, aby model wybrał inną strategię.
- Deklaracja `done` nie oznacza sukcesu bez niezależnego weryfikatora.

## Pierwszy test

Lokalny formularz „NaviMind Visual Lab” zawiera celowo błędne `ATop Trans`, niezaznaczony montaż i przycisk „Sprawdź”. Agent ma doprowadzić do potwierdzonego wyniku: `Top Trans`, montaż TAK. Model musi rozpoznać formularz i wybrać metodę. Nie ma zaprogramowanego kliknięcia przycisku w konkretnym miejscu.

Weryfikator odczytuje rzeczywisty stan formularza zapisany przez aplikację testową, sprawdza jej PID i identyfikator sesji. Wartości wpisane bez naciśnięcia „Sprawdź” nie zaliczają testu. Sama deklaracja modelu również go nie zalicza.

Nowy program uruchamiający dopuszcza obecnie wykonywanie tylko w tym formularzu testowym. To zamierzony zakres pierwszego pilota. Nie steruje jeszcze WindowHub, przeglądarką ani całym pulpitem.

## Walidacja wykonana

- Przy przygotowaniu pilota przeszło 99 testów Python obejmujących także wybraną regresję wcześniejszej pracy. Po dodaniu obsługi chronionego podglądu przeszło 20 testów nowego modułu oraz 1 test rzeczywistego lokalnego HTTP.
- 39 testów Node: nowe endpointy obrazowe i regresja dotychczasowego V1/V2.
- TypeScript `tsc --noEmit --incremental false`: PASS.
- Rzeczywiste lokalne HTTP: Python wysyła PNG → TypeScript waliduje → obraz trafia do części `image_url` testowego dostawcy → odpowiedź wraca do klienta.
- W testach model i wykonanie ekranu zastąpiono atrapami. Nie potwierdzono rozpoznawania formularza przez rzeczywisty model ani sterownika Windows.

## Warunki przed pierwszym wywołaniem modelu

Serwer jest przygotowany w draft PR #30. Istnieje podgląd gałęzi `feat/visual-goal-pilot-20261106`; włączono go jedynie dla tego Preview. Przed testem należy potwierdzić dostęp oraz następujące ustawienia:

| Ustawienie serwera | Znaczenie |
|---|---|
| `NAVIMIND_VISUAL_ENABLED=1` | Włącza nowy endpoint; bez tej wartości zwraca 503 |
| `NAVIMIND_AGENT_SECRET` | Istniejący sekret uwierzytelniania, bez publikowania jego wartości |
| `OPENAI_API_KEY` | Istniejący klucz serwerowy |
| `NAVIMIND_VISUAL_MODEL` | Opcjonalny model z obrazem i structured outputs; domyślnie istniejący V2 model, a następnie `gpt-4.1-mini` |

Konfiguracja klienta: `NAVIMIND_VISUAL_URL` musi wskazywać dokładny, zweryfikowany endpoint `/api/agent/visual-task`. Nie jest zgadywany na podstawie domeny. Klient korzysta z istniejącego `NAVIMIND_AGENT_V2_SECRET` lub `NAVIMIND_AGENT_SECRET` z lokalnego `.env`. Nie wklejaj ich do czatu.

Produkcji nie zmieniono. Chroniony podgląd można otworzyć zalogowanym dostępem Vercel. Opcjonalny tymczasowy link współdzielony wymaga osobnej, wyraźnej zgody na dostęp osób posiadających link. Automatyczna kontrola odrzuciła jego utworzenie bez takiej zgody; nie utworzono linku i nie wyłączono ochrony.

## Ochrona Preview

Klient opcjonalnie przyjmuje `NAVIMIND_VISUAL_ACCESS_URL`: zaakceptowany tymczasowy link Vercel tego samego podglądu z parametrem `_vercel_share`. Nie wpisuj linku do repozytorium ani do logów. Klient pobiera cookie GET-em bez aplikacyjnego sekretu, a sekret API wysyła wyłącznie do endpointu na tej samej domenie. Przekierowania do innej domeny są blokowane. Kod nie tworzy linków i nie wyłącza ochrony.

Bez prawidłowo skonfigurowanego dostępu nie uruchamiaj kolejnych prób modelu. Przykładowe linki z dokumentacji nie są danymi dostępowymi.

## Komendy po potwierdzeniu dostępu do serwera

1. Zastosuj `windowhub-visual-client.patch` w lokalnym repozytorium; najpierw `git apply --check`, potem `git apply`.
2. Uruchom formularz w jednym oknie PowerShell:

```powershell
Set-Location 'E:\wh-ai-parser-navimind-world-model-v2'
python tools/visual_agent_lab.py
```

3. W drugim oknie, z poprawną lokalną konfiguracją endpointu:

```powershell
Set-Location 'E:\wh-ai-parser-navimind-world-model-v2'
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_visual_agent.ps1
```

Bez `-ExecuteLive` program aktywuje formularz i prosi model o jedną propozycję, bez wpisywania i klikania. To pierwsze prawdziwe potwierdzenie odpowiedzi modelu na obraz.

4. Po ocenie propozycji uruchom:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_visual_agent.ps1 -ExecuteLive
```

Limit: 16 cykli, jedno działanie na cykl. Screenshoty formularza są przesyłane do NaviMind i OpenAI; wywołania są płatne według użycia API. Na tym etapie screenshoty obejmują wyłącznie fikcyjne dane laboratorium.

## Dalsza droga

Po udanym pilocie: dołączyć odczyt UIA do obrazu, adapter przeglądarki/DOM, narzędzia czytania arkuszy oraz wiedzę domenową WindowHub. Następnie przetestować to samo zadanie w zmienionym układzie formularza i dopiero dopuścić właściwości oferty WH.

Nie ma tu jeszcze kompletnego tworzenia okna, weryfikacji konstrukcji ani zapisu szkicu. Działająca pętla obrazowa nie zastępuje tych narzędzi i dowodów.

Źródła implementacji API: [Images and vision](https://developers.openai.com/api/docs/guides/images-vision?api-mode=chat), [Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use).

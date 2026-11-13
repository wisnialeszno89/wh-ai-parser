# Test na Windows bez WindowHub

Uruchamiaj w PowerShell w katalogu repozytorium. Zamknij okno Chromium testu
przed aktualizowaniem gałęzi. Nie używaj reset --hard do usuwania lokalnych zmian.

```powershell
$ErrorActionPreference = 'Stop'
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Git fetch failed.' }
git switch fix/window-enquiry-completeness-20261113
if ($LASTEXITCODE -ne 0) { throw 'Git switch failed. Preserve your local changes first.' }
git pull --ff-only origin fix/window-enquiry-completeness-20261113
if ($LASTEXITCODE -ne 0) { throw 'Git pull failed.' }
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_window_offer_pipeline.ps1 -InstallDependencies
```

Skrypt zakłada oddzielną `.venv-offer-lab`, bez modyfikowania zwykłej `.venv`.
Instaluje wyłącznie pakiety testowe z przypiętymi wersjami. Nie wymaga klucza AI,
parowania komputera ani WindowHub. Nie otwiera przeglądarki bez `-ExecuteLive`.
Wersja PowerShell 5.1 jest obsługiwana; Python co najmniej 3.10, test Windows
w CI używa 3.13. Opcjonalnie podaj `-Python 'C:\sciezka\python.exe'` przy tworzeniu
środowiska, jeśli polecenie `python` nie wskazuje właściwego interpretera.

## Etap 1: lokalna kontrola

Sprawdzamy kontrakt i import specyfikacji, regułę R/L, ograniczenia adaptera,
zachowanie wcześniejszych wartości i kompletność importu tekstu/PDF. Potem:

- przygotowanie dwóch różnych pozycji FIX: 2 × 1230×1478 mm oraz 1 × 1100×950 mm;
- zapis i ponowny odczyt tego samego modelu danych;
- oczekiwane zatrzymanie dodatku, szczegółowego szklenia i nieobsługiwanego DKR
  w pozycji 2, bez pomijania tej pozycji;
- nowy katalog wyników dla każdego uruchomienia — starszy sukces nigdy nie
  zastępuje nieudanego bieżącego testu.

Oczekiwane końcowe znaczniki:

```text
WINDOW_OFFER_LAB=offline_passed
LIVE_FORM=not_verified
SUBMITTED=False WH_OFFER_CREATED=False
WINDOW_OFFER_EXIT_CODE=0
```

To potwierdzenie testów lokalnych, nie pracy w rzeczywistym formularzu.

## Etap 2: widoczny formularz PAGEN

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_window_offer_pipeline.ps1 -InstallDependencies -ExecuteLive -KeepOpen
```

Instalacja pobiera także Chromium Playwright. Następne uruchomienia mogą pominąć
`-InstallDependencies`, jeśli pakiety i Chromium są już dostępne.
Publiczny formularz otrzyma typ/profil okna, ilości, wymiary i obsługiwany kolor.
Nie podajemy danych kontaktowych i nie wysyłamy zapytania. `-KeepOpen` zostawia
okno do obejrzenia i naciśnięcia Enter w PowerShell, również po błędzie kroku.

Oczekiwane znaczniki po zgodnym odczycie wszystkich pól:

```text
WINDOW_OFFER_LAB=form_verified
LIVE_FORM=verified
SUBMITTED=False WH_OFFER_CREATED=False
WINDOW_OFFER_EXIT_CODE=0
```

Podgląd Vercel i plik specyfikacji nie są potrzebne do dwóch powyższych etapów.
To test wykonawcy na sztucznych danych, bez bieżącego wywołania modelu AI.

## Etap 3: rzeczywisty eksport z Workspace

Otwórz podgląd z PR NaviMind #33 w swojej przeglądarce zalogowanej do Vercel.
Zaznacz **Odczytaj zapytanie okienne PL/DE** i wklej poniższy test:

```text
Pos. 1: Fenster FIX, 2 Stk., 1230 x 1478 mm. Innen weiß, außen weiß.
Profil: Okna PVC Premium Line (Salamander).
Pos. 2: Fenster FIX, 1 Stk., 1100 x 950 mm. Innen weiß, außen weiß.
Profil: Okna PVC Premium Line (Salamander).
```

Naciśnij **Odczytaj zapytanie**, sprawdź pozycje i pobierz wynik przez
**Pobierz specyfikację pozycji**. Następnie wskaż dokładną ścieżkę pobranego pliku:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\test_window_offer_pipeline.ps1 -SpecificationFile "$env:USERPROFILE\Downloads\specyfikacja-okien.json"
```

Jeżeli wynik jest zgodny i kompatybilny z adapterem, dodaj `-ExecuteLive -KeepOpen`
do tego samego polecenia. Jeśli wynik ma `review`, sprawdź przyczynę. Nie kasuj
uwag ani wymagań w JSON tylko po to, by wymusić przejście testu.
Model może dodać uwagę lub inaczej sformułować wymagania między odczytami;
most celowo zatrzymuje taki odczyt. Nie jest to automatyczny dowód błędu wymiarów,
ale nie wolno uznać całej specyfikacji za potwierdzoną.

## Co przekazać po teście

Końcowe znaczniki i linię `REPORT_DIRECTORY`. Na Pulpicie, w
`NaviMind-Praca\Testy-ofert\<identyfikator uruchomienia>`, są:

- `result.json` — wynik tego uruchomienia, wersja Pythona i zakres testu;
- `specification.json`, `compatibility.json`, `prepared-order.json` — źródło
  oraz plan, jeśli był kompatybilny;
- `form-readback.json` i `form.jpg` — tylko po udanej kontroli formularza;
- `browser-error.json` — jeśli błąd wystąpił po otwarciu okna testu.

Można zmienić folder przez `-OutputDirectory`. Katalogi `.venv-offer-lab`
i `.artifacts` są wyłączone z gita. Wyników rzeczywistych klientów nie dodawaj
do publicznego repozytorium. Do diagnostyki wystarczą znaczniki i bezpieczne kody.

## Co nadal nie jest potwierdzone

Nie wykonano oferty w WH, obliczenia ceny ani zapisu szkicu w rzeczywistym
programie Windows. Najbliższe rozszerzenie to jawny model skrzydeł, słupka,
podziału i okuć. Dzięki temu będzie można bezpiecznie przenieść do konfiguracji
DKR/DKL i okna wieloskrzydłowe, zamiast pomijać ich wymagania.

# NaviMind — pierwszy nadzorowany test tworzenia oferty w WindowHub

## Cel i granice

Sprawdzamy działającą ścieżkę czat → zatwierdzony PDF/tekst → lokalny manifest pozycji → Start1/wybór klienta → niezapisany Dokument1/OFR → kreator pozycji → V2 → lokalna kontrola wartości pól. Agent **nie zapisuje i nie wysyła** oferty. Test w rzeczywistym WindowHub uruchamia operator dopiero po osobnej decyzji.

**Stan:** testy offline CI nie dowodzą działania w konkretnym WindowHub. Mechanizm uznania całej konstrukcji za ukończoną nadal wymaga odczytu biznesowego z widoku oferty (wymiary, ilość, geometria otwierania, profil, kolor, szyby). Samo wpisanie wymiarów nie jest ukończeniem konstrukcji.

## 0. Bezpieczny preflight — bez działań na Windows UI

Z katalogu repozytorium:

```powershell
python tools/run_navimind_offer_preflight.py
```

Wyświetli wyłącznie obecność bibliotek, flag wykonawczych i konfiguracji V2. Nie odczytuje PDF, nie wysyła zapytań, nie pokazuje kluczy, nie aktywuje WindowHub i nie przyznaje dostępu do sterowania. `reasoner_url_configured=true` oznacza **jedynie obecność konfiguracji**, nie poprawne uwierzytelnienie! Problemy 401/Deployment Protection nadal wymagają osobnego testu połączenia.

### Zabezpieczenie Vercel — bez wyłączania SSO

Sprawdzono konfigurację projektu NaviMind na Vercel: produkcyjne wdrożenie jest w stanie `READY`, ale `ssoProtection.enabled=true` z `deploymentType=all`. Wywołanie endpointu V2 może więc zwrócić 401 mimo poprawnego `NAVIMIND_AGENT_SECRET`. Lokalny klient `NaviMindTaskReasonerV2` **już** obsługuje nagłówek `x-vercel-protection-bypass`, jeśli operator posiada osobny `NAVIMIND_VERCEL_PROTECTION_BYPASS`. Nie wyłączaj globalnej ochrony aplikacji ani nie dodawaj sekretu do GitHub.

Przy `NAVIMIND_AGENT_V2_URL` wymagany jest odpowiadający mu `NAVIMIND_AGENT_V2_SECRET`. Przy wspólnym `NAVIMIND_AGENT_URL` wymagany jest `NAVIMIND_AGENT_SECRET`. Kontrola offline pokazuje tylko wartości logiczne; nie potwierdza działania automatycznego bypassu ani dostępności zewnętrznego API.

## 1. Przygotowanie bez wykonywania

Uruchom WindowHub i otwórz Start1. Uruchom panel:

```powershell
python tools/run_navimind_shared_control_center.py --new-offer
```

Podaj polecenie przygotowania **jednej** roboczej oferty, np. `Utwórz nową niezapisaną ofertę: 1 Stk Fenster 1500x1400, kolor biały, 2 szyby. Nie zapisuj.`

Oczekiwane: przekazanie zadania do koordynatora V2, brak kliknięć w trakcie planowania. W panelu sprawdź stan etapu. Jeśli silnik V2 jest nieosiągalny, przerwij; nie zgaduj parametrów na podstawie odpowiedzi modelu.

## 2. Pierwszy kontrolowany test live — dopiero po świadomym uruchomieniu przez operatora

Do rzeczywistego działania lokalnego wymagane są jednocześnie `WH_REAL_WINDOWHUB=1`, `COMPUTER_USE_LIVE=1` oraz przycisk `Wznów pracę`. Sama obecność flag nie uruchamia kliknięć. Korzystaj wyłącznie z testowego, możliwego do odrzucenia dokumentu i testowego klienta, a nie aktywnego zamówienia.

Sprawdzaj po kolei:

1. Jednoznaczny Start1. Przy nieznanym oknie **brak aktywacji** i przegląd.
2. Pojedynczy `NOWA OFERTA`; bez drugiego wywołania przy powolnym ekranie.
3. Nowy dialog `Właściwości dokumentu` należy do natywnie obserwowanej transakcji MDI.
4. Otwarty wybór klienta; niejednoznacznego klienta wskazuje ręcznie handlowiec.
5. Niezapisany `Dokument1` albo rzeczywiście zaznaczony OFR należą do tej samej transakcji.
6. W kreatorze ilość/szerokość/wysokość muszą odpowiadać jednej aktywnej pozycji. Po wpisaniu pole musi być **odczytane ponownie z tego samego runtime UIA**; w panelu pojawia się `pola odczytane 1/3` … `3/3`.
7. Agent może zaproponować natywne `Okno` oraz `Dalej >` (`AutomationId=12324`) tylko wtedy, gdy istnieją wymagane odczyty: w etapie pozycji — ilość, w etapie wymiarów — szerokość i wysokość. Zły identyfikator przycisku lub brak któregokolwiek odczytu musi oznaczać STOP. Przy katalogu systemu, szyb, okuć, nietypowym otwieraniu lub braku niezależnego odczytu konstrukcji — **zatrzymanie do przeglądu**, a nie samodzielny zapis.
8. Sprawdź, czy ręczne `Przejmij sterowanie`, cofnięcie zgody na PDF, zmiana zakładki albo okna obcego programu anulują uprzednie uprawnienia.

## 3. Wielopozycyjne zapytanie testowe

Po przejściu prostego scenariusza dopiero osobna misja, np.:

```text
Pos. 1: 2 Stk Fenster 1500x1400
Pos. 2: 1 Stk Fenster 1300x1200
Pos. 3: 3 Stk Fenster 1500x1400
Pos. 4: 1 Stk Fenster 1000x1100
```

Prawidłowy manifest: cztery odrębne ID `S01-P001` … `S01-P004`, pozycje 1 i 3 **pozostają oddzielne**. V2 może używać ilości i wymiarów wyłącznie bieżącej pozycji. Żaden z odczytów pól pierwszego okna nie może zaliczyć drugiego okna. Po osiągnięciu 20 działań bez kompletnego, niezależnego checkpointa agent przechodzi do przeglądu, a nie wykonuje kolejnych kliknięć w pętli.

## 4. Warunki STOP i dane diagnostyczne

Przerwij test przy innym kliencie, innym OFR, zmianie procesu, utracie widocznego okna, niezgodności wymiaru lub ilości, braku readback UIA, niejasnym katalogu, błędach V2, zgodzie PDF cofniętej, nieznanym polu sterującym albo powtarzającym się działaniu na niezmienionym etapie.

Zachowaj bez danych klienta: typ etapu, anonimowy identyfikator pozycji, reason-code blokady, liczbę potwierdzonych pól, identyfikator commitu i wynik testu. Nie wklejaj kluczy V2 ani pełnych zapytań klientów do GitHub Issues.

## Wymagane przed uznaniem całej oferty za wykonaną

Zintegrować i przetestować natywny biznesowy readback w widoku pozycji dokumentu WindowHub: identyfikator właściwej pozycji, faktyczne wymiary i ilość, konstrukcja/otwieranie, profil, kolor, szyby oraz cena. Dopiero zaufany adapter może wygenerować `PositionCheckpoint` dla `PositionLedger`. Modelowe `done`, screenshot lub poprawna zawartość pojedynczego pola **nie są wystarczające**. Na końcu pozostaje jawny przegląd handlowca.

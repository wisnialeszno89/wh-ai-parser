# Polecenie z NaviMind do lokalnego Windowsa

Pilot obsługuje tworzenie, dopisywanie, edycję, otwieranie i kopiowanie tekstowych tabel okien. Model na serwerze tłumaczy polecenie na walidowane dane, a lokalny adapter wykonuje zapis przez klasyczny Notatnik Windows 10. To wykonawca konkretnych operacji, nie uniwersalny agent obserwujący ekran dowolnego programu.

1. W katalogu repo uruchom `.venv\Scripts\python.exe tools\run_navimind_desktop_bridge.py --execute-live`.
2. Zostaw PowerShell otwarty. Kod parowania zostanie skopiowany do schowka; jest też widoczny lokalnie w terminalu. Nie wysyłaj go w czacie.
3. Otwórz https://www.navimind.app/workspace na tym samym komputerze. Połącz komputer → wklej kod → Połącz. Jeśli przeglądarka zapyta o dostęp do sieci lokalnej/loopback, zezwól dla NaviMind.
4. Zaznaczone „Praca na komputerze” zmienia przycisk wysyłania na „Wykonaj”. Po odznaczeniu działa zwykła rozmowa.
5. Zleć: `Utwórz folder Oferta Top Trans i tabelę: 2 okna DKR 1000x1000 mm oraz 1 okno dwuskrzydłowe 1500x1400 mm.`
6. Po potwierdzeniu: `Zmień szerokość pierwszej pozycji na 1100 mm. Pozostałe dane zachowaj.`

Wyniki powstają w `Pulpit\NaviMind-Praca\<nazwa>\tabela-okien.txt`. Pilot otwiera poprawne tabele ze swojego obszaru pracy, tworzy też raporty XLSX i nie przyjmuje skryptów ani dowolnych ścieżek. Nazwy oraz liczby są sprawdzane także lokalnie. Nowy plik można zapisać w istniejącym folderze. Plików nie zastępuje poleceniem tworzenia. Korekta dotyczy aktywnej tabeli; wykonawca pamięta ją po restarcie. Przeglądarka pamięta kod tylko w bieżącej karcie.

Każdy zapis jest sprawdzany przez ponowny odczyt całego pliku. Wynik oraz zrzuty przed/po trafiają lokalnie do `NaviMind-Praca\.traces\<id>`. Zmiany użytkownika w pliku albo niezapisane zmiany w obsługiwanym oknie Notatnika zatrzymują edycję. Aby przyjąć zapisane ręczne zmiany, zamknij edytor i jawnie otwórz plik poleceniem. Przy braku potwierdzenia transportu kliknij „Sprawdź wynik zadania”; odczyta wynik bez ponawiania operacji. Zatrzymanie wykonawcy: Ctrl+C w PowerShell.

Serwer słucha tylko na `127.0.0.1:43127`, wymaga świeżego losowego kodu i dokładnego Origin `https://www.navimind.app` lub `https://navimind.app`. Kod nigdy nie trafia do Vercel/modelu. Dane tabeli i polecenie są przesyłane do modelu w celu przygotowania operacji. Nie ma tunelu, zdalnego portu Windows ani trwałej kolejki w chmurze. Czat wymaga nadal prywatnego dostępu Vercel.

## Rozszerzenie: edycja i osobne pliki

Po aktualizacji wykonawca zgłasza także `append_window_rows`, `edit_window_rows`, `open_window_table` i `copy_window_table`. „Dopisz” dodaje tylko nowe wiersze. Korekta zawiera numer pozycji i tylko zmieniane pola: opis, szerokość, wysokość, ilość. Pełny plik po operacji jest porównywany z oczekiwaną tabelą; pozostałe pola wynikają z odczytanego oryginału, nie z rekonstrukcji przez model.

Nowy plik `.txt` można utworzyć w istniejącym folderze. Obecnego pliku nie zastępujemy poleceniem tworzenia. Warianty w osobnym pliku stają się aktywne po zapisie; aby wrócić do oryginału, zleć `Otwórz tabela-okien.txt z folderu Oferta Top Trans`.

Wykonawca pamięta wybór aktywnej tabeli po restarcie. Przy pierwszej aktualizacji z v1 automatycznie wczyta jedyny poprawny plik tabeli w obszarze pracy. Jeśli jest ich kilka, trzeba wybrać jeden poleceniem otwarcia. Katalog obejmuje tylko tabelki o oczekiwanym formacie, w bezpośrednich podfolderach NaviMind-Praca. Zapisane ręczne zmiany można jawnie wczytać przez otwarcie; nie są automatycznie nadpisywane.

Przykłady kolejnych poleceń:

- `Dopisz okno dwuskrzydłowe 1500 × 1300 mm, 2 sztuki.`
- `W pozycji 1 zmień wysokość na 1200 mm i ilość na 3. Pozostałe dane zachowaj.`
- `Wymyśl 10 testowych wariantów okien i zapisz w osobnym pliku warianty-okien.txt w tym samym folderze. Oryginał zachowaj.`
- `Zapisz dokładną kopię aktywnej tabeli jako kopia-okien.txt.`

Maksymalnie 50 pozycji na plik. Wymyślanie danych jest dopuszczone na wyraźne życzenie, a opisy takich wierszy powinny wskazywać, że to warianty testowe. Nie są to automatycznie zatwierdzone konstrukcje produkcyjne.

## Raport zbiorczy i rozmowa bez składni

`aggregate_window_tables` odczytuje 1–50 wskazanych plików tabel (do 2500 wierszy), zachowuje dane i tworzy nowy XLSX oraz lokalny podgląd HTML. Nie wymaga zainstalowanego Excela ani dodatkowych pakietów Pythona. Źródła są wybierane z lokalnego katalogu; serwer wiąże propozycję modelu z wersją każdego pliku. Zmiana źródeł przed publikacją zatrzymuje raport. Wynik nie zmienia aktywnego pliku tabeli.

Raport zawiera pochodzenie każdego wiersza, wymiary w mm, ilość, powierzchnię jednej sztuki i łączną powierzchnię. Powierzchnie oraz sumy sztuk i m² zachowują formuły Excel i poprawne wartości zapisane w pliku. Powtórzenie oznacza zgodny opis po ujednoliceniu wielkości liter/odstępów oraz zgodne wymiary. Ilość nie decyduje o dopasowaniu. Żadnego wiersza nie usuwa się automatycznie; sumy obejmują także oznaczone kopie. Oznaczenia duplikatów są stanem z chwili generowania.

Przykład: `Zbierz te zestawienia z NaviMind-Praca w jeden arkusz, policz sztuki i metry kwadratowe, pokaż powtórki i otwórz wynik.` Przy zleceniu konkretnego folderu raport obejmie wybrane pliki z tego folderu. Domyślny folder wynikowy to Raporty. Nowy raport nie zastępuje istniejącego. System przekazuje polecenie otwarcia domyślnej aplikacji arkuszy; jeśli jej brak, próbuje otworzyć podgląd w przeglądarce. Wykonawca potwierdza zawartość pliku; nie udaje, że zweryfikował widoczność okna zewnętrznego programu.

Planista rozróżnia `execute`, `clarify` i `respond`. Pytanie doprecyzowujące ma `task:null` i nie wykonuje zmian. Korzysta z historii rozmowy i aktualnej tabeli, aby rozumieć krótkie odpowiedzi, literówki i jawne jednostki podane słownie. Gdy wymiar albo wskazanie pozycji jest niejednoznaczne, pyta o tę konkretną informację. Nie prosi o JSON. Błędny format odpowiedzi modelu jest poprawiany jednokrotnie na serwerze, przed jakimkolwiek wykonaniem lokalnym.


## Przeglądarka: osobne okno Chromium NaviMind

Wersja pilotażowa uruchamiana z `--browser` otwiera osobny Chromium, sterowany lokalnie przez Playwright. Nie podłącza zwykłego Firefoksa ani domyślnego profilu Chrome. Profil sesji jest przechowywany tylko na tym komputerze w `%LOCALAPPDATA%\NaviMind\BrowserProfile`. Hasła i logowanie wprowadza użytkownik ręcznie. Pliki tego profilu nie trafiają do repo ani serwera NaviMind.

Po aktualizacji, w PowerShell w folderze repo:

```powershell
& .\.venv\Scripts\python.exe -m pip install playwright
& .\.venv\Scripts\python.exe -m playwright install chromium
& .\.venv\Scripts\python.exe .\tools\run_navimind_desktop_bridge.py --execute-live --browser
```

Zamknij poprzedniego wykonawcę przez Ctrl+C, zanim uruchomisz nowego. W NaviMind po Ctrl+F5 sparuj świeży kod i zaznacz **Przeglądarka · Chromium NaviMind**. Włączenie tego trybu wyłącza tryb tabel. Jeśli pole jest niedostępne, lokalny wykonawca nie zgłosił gotowego modułu przeglądarki.

W pustej karcie pojawia się laboratorium z fikcyjnym formularzem. Polecenie do czatu: `Wybierz dokładnie Top Trans, ustaw szerokość 1100 mm, wysokość 1000 mm, kolor antracyt, okucie DKR i pokaż podgląd.` Agent odczytuje widok, wybiera jeden krok, wykonuje go lokalnie i odczytuje stronę ponownie. Do 12 kroków na polecenie. Przycisk zatrzymania blokuje następny krok; nie cofa już wykonanych. Zmieniony widok przed akcją powoduje maksymalnie dwa ponowne odczyty i ponowne planowanie, bez wykonania starego kliknięcia. Dwie bezskuteczne próby tego samego kliknięcia w tym samym widoku zatrzymują zadanie.

Przy wysłaniu polecenia tekst strony, nazwy i rodzaje widocznych elementów oraz opcje list trafiają do modelu. Wartości pól, cookies i storage nie są przekazywane. Parametry adresów i fragmenty URL są usuwane z odczytu dla modelu. Dane konta widoczne jako tekst strony mogą znaleźć się w odczycie — włączaj ten tryb dla strony, na której chcesz pracować. Nie zapisujemy zrzutów ani treści stron w śladach lokalnych tego modułu. To odczyt DOM, nie analiza pikseli ekranu.

Dostępne: publiczna nawigacja http/https, zwykłe pola tekstowe/liczbowe, listy select, otwieranie menu, przyciski niesłużące zatwierdzaniu, przewijanie i Wstecz. Elementy mają krótkotrwałe identyfikatory przypisane do konkretnego odczytu; model nie dostarcza CSS, Javascript, shell ani współrzędnych. Wpisany tekst i wybór listy są sprawdzane lokalnie przez odczyt. Po kliknięciu agent ocenia nowy widok; potwierdzenie samej akcji nie dowodzi osiągnięcia celu.

Granice pilota: jedna kontrolowana karta i główny dokument. Nowe karty, iframe, canvas, pobieranie, hasła, kody, końcowe wysyłanie formularzy, usuwanie i operacje płatnicze wymagają ręcznej obsługi. Przycisk typu submit jest blokowany lokalnie. Lokalne filtry nazw przycisków ograniczają operacje finansowe i usuwanie, ale nie stanowią pełnego rozumienia dowolnej strony — pierwsze zadania należy obserwować. Użytkownik może zalogować się ręcznie w tym oknie, następnie poprosić agenta o odszukanie zamówienia lub odczyt menu; końcowego Refund wykonawca nie klika.

Test rzeczywistego Chromium z fikcyjnymi danymi (osobne okno, bez modelu i kont):

```powershell
& .\.venv\Scripts\python.exe .\tools\test_navimind_browser_live.py --execute-live
```

Oczekiwany wynik: `BROWSER_LAB_RESULT=verified STEPS=7 CUSTOMER=Top_Trans WIDTH=1100 HEIGHT=1000 COLOR=antracyt OPENING=DKR`. Test sprawdza wybór spośród podobnych nazw, wpisanie i odczyt wymiarów, listy kolorów/okucia, podgląd końcowy oraz zgodność danych. Testy jednostkowe odczytu, wersji strony, blokad i idempotencji uruchamia `python -m unittest discover -s tests -p test_navimind_browser.py`. Nie zastępują one próby na Windows.

Nowy adres nawigacji musi pochodzić z bieżącego polecenia użytkownika jako pełny http/https. Odnośniki otwieramy w obrębie bieżącej domeny; przejście do innej domeny wymaga nowego jawnego polecenia z jej pełnym adresem. Agent nie tworzy adresów z danych odczytanych na stronie.

## Paint: schemat PNG i nowe okno Windows 10

Opcja `--paint` dodaje `draw_window_in_paint` do zgłaszanych możliwości. Można użyć obu adapterów jednocześnie: `python tools/run_navimind_desktop_bridge.py --execute-live --browser --paint`. W czacie wyłącz **Przeglądarka** i włącz **Praca na komputerze**. Polecenie: `Przygotuj w Paint schemat okna 1500 x 1400 mm, dwa skrzydła ze stałym słupkiem, lewe DKL, prawe DKR, kolor antracyt. Zapisz jako okno-test.png w folderze Rysunki.`

Ta wersja renderuje PNG z parametrów i otwiera gotowy plik w nowym oknie klasycznego Painta. Nie obsługuje jeszcze swobodnego rysowania myszą ani narzędzi Painta. Wymiary określają proporcje schematu poglądowego, a nie dokumentację produkcyjną WH. Dostępne układy: pojedyncze DKL, pojedyncze DKR i dwa skrzydła ze stałym słupkiem (lewe DKL, prawe DKR), w kolorach biały, antracyt i mahoń. Widok od wewnątrz: DKL ma zawiasy po lewej i klamkę po prawej; DKR odwrotnie. Schemat nie udaje rozpoznanego symbolu otwierania WH.

Wynik trafia do `Pulpit\NaviMind-Praca\Rysunki\okno-test.png` i pliku metadanych `.png.json`. Przy zajętej nazwie wykonawca dobiera przyrostek `-2`, `-3` itd. Obecnych rysunków i aktywnej tabeli nie zmienia. Dane zadania są walidowane niezależnie w serwerze i wykonawcy. PNG po zapisie jest odczytywany i porównywany piksel po pikselu z przygotowanym obrazem. Metadane zapisują parametry, geometrię i hash pikseli. PNG jest sprawdzany ponownie po próbie otwarcia.

Otwarcie musi zostać potwierdzone przez nowe okno `MSPaintApp` należące do uruchomionego procesu i mające nazwę pliku w tytule. Wykonawca nie wysyła klawiszy do wcześniejszych okien Painta. Lokalne potwierdzenie otwarcia obejmuje proces, tytuł i zrzut tego okna; nie jest wizualnym porównaniem płótna z PNG. Zrzut zostaje lokalnie w `.traces`. Brak potwierdzenia okna daje `review`, zachowuje PNG i pokazuje jego ścieżkę. Odzyskanie tego samego zadania nie uruchamia Painta ponownie. Windows 11 z nowszą aplikacją Paint może nie spełniać warunku klasycznego okna — wymaga odrębnego adaptera.

Test kodu i renderera: `python -m pytest tests/test_navimind_paint.py`. Próba rzeczywistego otwarcia Painta: `python tools/test_navimind_paint_live.py --execute-live`. Oczekiwane: `PAINT_RESULT=verified` oraz `PAINT_WINDOW=verified`. Sprawdzenie natywnego okna na Windows wykonujemy osobno od testów z atrapą otwierania.

## Aplikacja: obraz okna i rzeczywiste akcje Painta

`--native-paint` otwiera nowy klasyczny Paint z białym PNG sesji w `NaviMind-Praca\Rysunki`. Po parowaniu wybierz **Aplikacja · Paint sterowany obrazem**. To osobny tryb od generatora trzech schematów i od Chromium. Włączenie go i wysłanie polecenia przełącza fokus do Painta oraz przekazuje zrzuty tego okna do modelu po kolejnych krokach. Polecenie testowe: `Na białym płótnie narysuj prosty dom, drzewo i słońce. Dodaj napis NaviMind i zapisz rysunek.`

Model dostaje aktualny obraz i wyniki poprzednich akcji. Może klikać, przeciągać łamaną do 24 punktów, wpisywać tekst, używać jawnej listy skrótów, przewijać i czekać. Sterownik WindowHub został rozszerzony o przeciąganie; sprawdza proces, fokus, granice obrazu i własność punktów przed ruchem. Przycisk myszy jest zwalniany również po przerwaniu przeciągania. Zasłonięte okno lub inny dokument zatrzymują odczyt. Zrzut jest kadrem klienta okna, nie całym pulpitem. W pamięci kontrolera jest tylko aktualna klatka i bounded cache wyników; kolejne zrzuty nie są zapisywane do śladów ani logów aplikacji. Otwarcie białego pliku ma lokalny zrzut potwierdzający nowe okno.

Do 24 kroków na polecenie, z przyciskiem zatrzymania. Zatrzymanie podczas planowania blokuje następną akcję. Nieaktualna klatka może wywołać dwa ponowne odczyty, bez wykonania starego kroku. Identyczne akcje na tym samym obrazie są ograniczane. Utrata połączenia zachowuje identyfikator do „Sprawdź wynik zadania”; nie ponawia kliknięcia. Po każdej akcji analizowany jest nowy obraz i przybliżona zmiana pikseli.

Na końcu kontroler wysyła Ctrl+S i odczytuje znany PNG sesji. Potwierdza zmianę pikseli w pliku; nie uznaje tego za niezależny dowód zgodności rysunku z poleceniem. Ocena modelu jest pokazywana oddzielnie. Brak nowych zapisanych pikseli daje review. Pierwsze sceny wymagają sprawdzenia na rzeczywistym Windows 10. Ten pilot nie ma jeszcze obsługi innych programów, okien dialogowych, Zapisz jako ani przekazywania plików poza obszar pracy. Nie wybiera się Nowy/Otwórz: pracujemy w dokumencie sesji. Zwykłe zamknięcie Painta wyłącza jego dostępność, pozostałe narzędzia nadal działają.

Uruchomienie wszystkich adapterów: `python tools/run_navimind_desktop_bridge.py --execute-live --browser --paint --native-paint`. `NAVIMIND_NATIVE_MODEL` może opcjonalnie wskazać model obrazu na serwerze; domyślnie używamy obecnego modelu workspace. Token parowania nie jest przesyłany do serwera/modelu.

## Odczytowy raport techniczny

Aktualny wykonawca zgłasza `inspect_computer`. W trybie **Praca na komputerze** zleć: `Sprawdź wersję Windows, ilość i dostępność RAM oraz wolne miejsce na dysku systemowym. Zapisz raport.` Wynik JSON trafia do nowego pliku w folderze Diagnostyka. Czat pokazuje fakty, na których można oprzeć dalszą rozmowę. Odczyt obejmuje system i architekturę, logiczne CPU, RAM, dysk systemowy i dostępność bibliotek wykonawcy. Nie pobiera nazw kont, hosta, sieci, procesów, kluczy ani środowiska. Nie zmienia ustawień. Nie mierzy użycia CPU, SMART ani malware, więc sam raport nie dowodzi przyczyny problemu. Planista ma oddzielać fakty od hipotez i brakujących pomiarów.

Odczyt obrazu jest uzupełniany o maksymalnie 80 nazwanych przycisków, kart i pozycji menu/list z UI Automation Windows. Ich wartości pól nie są pobierane. Model może wskazać krótkotrwały ref, a kontroler wybiera lokalnie odczytany środek elementu. Przy braku dostępnych nazw pozostaje odczyt obrazu. Nowe polecenie tworzy lokalny identyfikator sesji; stary krok z innej karty czatu nie jest wykonywany po rozpoczęciu nowej sesji. Identyfikator ten nie trafia do modelu.

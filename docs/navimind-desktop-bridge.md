# Polecenie z NaviMind do lokalnego Windowsa

Pilot obsługuje tworzenie, dopisywanie, edycję, otwieranie i kopiowanie tekstowych tabel okien. Model na serwerze tłumaczy polecenie na walidowane dane, a lokalny adapter wykonuje zapis przez klasyczny Notatnik Windows 10. To wykonawca konkretnych operacji, nie uniwersalny agent obserwujący ekran dowolnego programu.

1. W katalogu repo uruchom `.venv\Scripts\python.exe tools\run_navimind_desktop_bridge.py --execute-live`.
2. Zostaw PowerShell otwarty. Kod parowania zostanie skopiowany do schowka; jest też widoczny lokalnie w terminalu. Nie wysyłaj go w czacie.
3. Otwórz https://www.navimind.app/workspace na tym samym komputerze. Połącz komputer → wklej kod → Połącz. Jeśli przeglądarka zapyta o dostęp do sieci lokalnej/loopback, zezwól dla NaviMind.
4. Zaznaczone „Praca na komputerze” zmienia przycisk wysyłania na „Wykonaj”. Po odznaczeniu działa zwykła rozmowa.
5. Zleć: `Utwórz folder Oferta Top Trans i tabelę: 2 okna DKR 1000x1000 mm oraz 1 okno dwuskrzydłowe 1500x1400 mm.`
6. Po potwierdzeniu: `Zmień szerokość pierwszej pozycji na 1100 mm. Pozostałe dane zachowaj.`

Wyniki powstają w `Pulpit\NaviMind-Praca\<nazwa>\tabela-okien.txt`. Pilot otwiera poprawne tabele ze swojego obszaru pracy, nie tworzy XLSX i nie przyjmuje skryptów ani dowolnych ścieżek. Nazwy oraz liczby są sprawdzane także lokalnie. Nowy plik można zapisać w istniejącym folderze. Plików nie zastępuje poleceniem tworzenia. Korekta dotyczy aktywnej tabeli; wykonawca pamięta ją po restarcie. Przeglądarka pamięta kod tylko w bieżącej karcie.

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

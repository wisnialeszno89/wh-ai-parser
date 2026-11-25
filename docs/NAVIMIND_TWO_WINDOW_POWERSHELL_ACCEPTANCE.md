# NaviMind / WindowHub — dwa okna z PowerShell, test end-to-end

**Stan:** gotowy scenariusz *nadzorowanego* testu uruchomieniowego, NIE zweryfikowana autonomia produkcyjna. Test nie zapisuje ani nie wysyła oferty. Systemy profili, szyby, kolory i okucia pozostają zależne od firmowej bazy technologicznej WH Okna; nieautoryzowany wybór katalogowy jest blokowany do demonstracji/niezależnej weryfikacji.

## Przygotowanie na lokalnym Windows

Wymagane: istniejące repo `wh-ai-parser`, Python w tym samym środowisku co dotychczasowe testy, zależności z projektu, dostęp do skonfigurowanego NaviMind V2 i WindowHub `Okna.exe` otwarty na ekranie Start1. Na produkcyjnej bazie firmy używaj wyłącznie **testowej oferty i klienta**, bez zapisania lub konwersji do zlecenia. Nie udostępniaj prywatnych PDF bez zgody.

Pobierz gałąź PR #240 do lokalnego katalogu projektu:

```powershell
cd C:\sciezka\do\wh-ai-parser
git fetch origin feat/navimind-unified-document-engine-20261125
git switch feat/navimind-unified-document-engine-20261125
git pull --ff-only origin feat/navimind-unified-document-engine-20261125
```

Jeśli w repo masz niezapisane zmiany albo inny aktywny branch wykorzystywany do pracy, **nie wymuszaj checkoutu**: użyj osobnego `git worktree` dla gałęzi testowej. Skrypt PowerShell nie modyfikuje gałęzi, nie uruchamia `git reset` i nie instaluje pakietów.

## 1. Pierwszy start, tylko analiza

W PowerShell z katalogu repo:

```powershell
.\tools\Start-NaviMind-TwoWindows.ps1
```

Lub ze wskazaniem istniejącego pliku:

```powershell
.\tools\Start-NaviMind-TwoWindows.ps1 -Pdf "C:\Oferty\zapytanie-2-okna.pdf"
```

albo:

```powershell
.\tools\Start-NaviMind-TwoWindows.ps1 -RequestFile "C:\Oferty\dwa-okna.txt"
```

NaviMind wczyta wskazany PDF/TXT wyłącznie do pamięci lokalnego procesu i pokaże panel; nie wysyła automatycznie pliku AI. Jeśli uruchomiono bez pliku, możesz **wpisać obie numerowane pozycje bezpośrednio w wiadomości czatu** razem z poleceniem utworzenia nowej oferty; wówczas pełna wysłana przez Ciebie wiadomość jest źródłem dwóch pozycji. Alternatywnie wpisz je w sekcji **ZAPYTANIE KLIENTA / PDF** i naciśnij `Zapisz treść lokalnie`, następnie zatwierdź zgodę na udostępnienie AI. Nie trzeba kopiować tekstu pomiędzy tymi wariantami.

Przykładowa treść dwóch wierszy do przetestowania parsera, nie domyślna specyfikacja handlowa:

```text
Pos. 1: 1 Stk Fenster 1500x1400
Pos. 2: 1 Stk Fenster 1300x1200
```

Do porównywania z katalogiem możesz również użyć jawnie oznaczonych, oddzielnych parametrów, np.:

```text
Pos. 1: 1 Stk Fenster 1500x1400
Profil: Veka Perfectline
Farbe innen: Weiss
Farbe außen: Anthrazit
Verglasung: 2-fach
Beschlag: activPilot
Pos. 2: 1 Stk Fenster 1300x1200
Profil: Veka Perfectline
Farbe innen: Weiss
Farbe außen: Weiss
Verglasung: 3-fach
Beschlag: activPilot
```

To **przykład składni zapytania**, nie twierdzenie, że podane produkty są dostępne w Twojej bazie WH Okna. Agent zachowuje wymagania każdej pozycji oddzielnie. Nazwy nie mogą być automatycznie zastępowane podobnymi pozycjami katalogowymi bez zweryfikowanej relacji lub Twojego potwierdzenia.

Profil, kolor, rodzaj szklenia, otwieranie, okucia oraz widok od wewnątrz/zewnątrz doprecyzuj w zapytaniu własnym lub PDF. Jeśli tych danych brak, agent nie powinien wymyślać ich jako pewnych. Niejasna ilość albo rozmiary blokują test.

Jeśli używasz **PDF/TXT w lokalnym schowku**, w panelu sprawdź źródło, zatwierdź **Udostępnij AI** (osobna zgoda na przekazanie fragmentów tekstu), potem wpisz w czacie:

> Przygotuj nową niezapisaną ofertę w WindowHub dla dokładnie dwóch pozycji z zatwierdzonego zapytania. Wybierz tylko rzeczywiście dostępny profil, kolor, pakiet szybowy i okucia. Jeśli nie możesz zweryfikować listy w moim WindowHub, zatrzymaj się, wyjaśnij brak i poproś o pokazanie czynności w trybie nauki. Nie zapisuj ani nie wysyłaj oferty.

W pierwszym starcie bez przełącznika `-Live` panel planuje; nie powinien sterować myszą.

## 2. Test rzeczywistych pojedynczych działań

Po przejściu preflight i testu planowania uruchom świadomie:

```powershell
.\tools\Start-NaviMind-TwoWindows.ps1 -Pdf "C:\Oferty\zapytanie-2-okna.pdf" -Live
```

**Nie wykonuj obu uruchomień równocześnie** — zamknij poprzedni panel. `-Live` ustawia tylko dwie flagi na czas procesu. Wciąż wymagane jest lokalne kliknięcie **Wznów pracę**, a każdy pojedynczy krok podlega obserwacji, natywnemu scope, odczytowi i limitowi akcji. W każdej chwili `Przejmij sterowanie` odbiera agentowi uprawnienia. Skrypt nie uruchamia WindowHub i nie przełącza aktywnego programu w tle.

Sprawdzaj kolejno:
1. Start1 → dokładnie jeden przycisk **NOWA OFERTA**. Brak wielokrotnego klikania w razie powolnego startu.
2. Właściwości nowego dokumentu → **Wybierz istniejącego klienta**. Wybór konkretnego klienta wymaga obecnie ręcznego wskazania (program nie ma prawa zgadywać zbliżonych nazw).
3. Powrót do niezapisanej oferty/dokumentu MDI i otwarcie kreatora pozycji.
4. **Pozycja 1:** typ Okno, ilość, szerokość i wysokość. Natywne UIA musi potwierdzić wpisane wartości oraz ich zgodność z pierwszą pozycją źródłową. Nieznane parametry i katalogowe okna wymagają zatrzymania.
5. **Katalogi:** jeśli profil/kolor/pakiet/okucia nie są jednoznacznie rozpoznane, użyj `Przejmij sterowanie`, następnie `Tryb nauki`, pokaż ręcznie wybór na testowym dokumencie; zakończ naukę. To **dane do budowy adaptera**, nie automatyczna zgoda na zapisywanie ani dowód poprawnego wyboru.
6. **Pozycja 2:** nie może być zaliczona parametrami pierwszej. Przejście nastąpi dopiero po niezależnym odczycie biznesowym gotowej konstrukcji, który **nie jest jeszcze w pełni połączony** z rejestrem pozycji. Przewidywany STOP w pierwszym teście jest prawidłowym wynikiem diagnostycznym.
7. Nie klikaj `Zapisz`, `Zakończ` ani `Wyślij`, dopóki ścieżka nie zostanie zweryfikowana w testowej instalacji.

## 3. Dodatkowa diagnostyka natywnych pól katalogowych

Przejdź ręcznie do `Podstawowe parametry okna`, `Parametry szklenia`, `Parametry okuć` i na każdym ekranie wywołaj:

```powershell
python tools/inspect_navimind_catalog_readiness.py --observe
```

Polecenie nic nie klika, nic nie zapisuje, nie wysyła PDF ani wartości klienta. Pokazuje tylko, które UIA pola mają jednoznaczną identyfikację i czy bieżąca wartość jest odczytywalna. Nie enumeruje pozycji katalogowych i nie dowodzi możliwości wyboru.

Opcjonalnie **ręcznie rozwiń jedną listę katalogową** w testowym kreatorze i na tym samym komputerze wykonaj:

```powershell
python tools/inspect_navimind_catalog_readiness.py --observe --show-expanded-options
```

Wtedy, tylko na wyraźne życzenie operatora, raport może wydrukować do 25 widocznych etykiet `listitem/treeitem`. **To nie są jeszcze przypisane warianty konkretnej listy** — popup może mieć osobne drzewo UIA; dlatego wynik nie uruchamia wyboru ani nie jest wysyłany AI. Przejrzyj przed udostępnieniem, czy nie ma tam danych osobowych z innego otwartego dialogu. Jeśli nie pojawią się opcje, zapisz w diagnostyce `[]` zamiast zgadywać.

## 4. Jak przekazać diagnostykę

Prześlij do rozmowy: reason-code blokady z panelu, wynik `inspect_navimind_catalog_readiness.py --observe` z każdego ekranu i informację, czy WINDOWHUB był na Start1, w kreatorze czy w edytorze konstrukcji. Nie publikuj zrzutów z pełnymi danymi klienta, żadnych tokenów Vercel ani prywatnych PDF. Przy nieoczekiwanym zachowaniu najpierw kliknij `Przejmij sterowanie`.

## Kryterium ukończenia automatyzacji

Dwie rzeczywiste, **niezapisane** konstrukcje w edytorze odpowiadające zapytaniu, osobna natywna weryfikacja każdej: identyfikator pozycji, ilość, szerokość, wysokość, profil, kolor po obu stronach, pakiet szklenia, otwieranie, okucia, status kalkulacji; zero pominiętych elementów. Dopiero po spełnieniu tych kryteriów można mówić o w pełni samodzielnym wykonaniu.

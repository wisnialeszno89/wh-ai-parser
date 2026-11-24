# NaviMind — Top Trans, realny test od zera

## Zapytanie (wklej do sekcji ZAPYTANIE KLIENTA / PDF)

Klient: Top Trans. Proszę przygotować wycenę dwóch okien. Pozycja 1: 1 sztuka, okno jednoskrzydłowe, białe. Pozycja 2: 1 sztuka, okno dwuskrzydłowe, jednostronny kolor antracyt struktura 701605, pakiet dwuszybowy. W ofercie pokaż cenę konstrukcji, ale ukryj ceny montażu, demontażu oraz wykończenia.

## Polecenie do CZATU (krótka wiadomość)

Przeczytaj zapytanie Top Trans. Rozpoznaj wszystkie wymagania, wypisz brakujące dane i zaproponuj kolejność kroków w WindowHub. Nie zgaduj wymiarów, kierunków otwierania i strony koloru. Nie wykonuj działań, dopóki nie ma zatwierdzonego planu.

## Oczekiwany wynik pierwszej próby

Dwie pozycje, 1 sztuka każda, białe okno jednoskrzydłowe i dwuskrzydłowe z jednostronnym antracytem 701605. Montaż/demontaż/wykończenie: ukryte ceny, nie wartości 0.00. Brakujące: 4 wymiary, kierunki otwierania, strona antracytu oraz potwierdzenie szklenia pierwszej pozycji. Dwuszybowe szklenie w pierwszej pozycji może być **sugerowanym** domyślnym wyborem, ale nie stwierdzeniem z zapytania. Dodatkowo do potwierdzenia profil/system.

## Uczciwa diagnoza blokad

1. `run_navimind_shared_control_center.py` jest tylko obserwatorem: jawnie podaje `NAVIMIND_V2_EXECUTOR_CONNECTED=False`. Nie może wpisać ani zapisać oferty.
2. `MissionChat.user_message()` obecnie zawiesza stary plan i wymusza nową wersję misji. Nie ma pełnego mostu od wypowiedzi do wielopozycyjnego planu wykonawczego.
3. `LocalEnquiryInbox` nie przekazuje tekstu z dolnego panelu do modelu. Trzeba połączyć dane pochodzące z zaakceptowanego zapytania z planistą, z ochroną przed instrukcjami w treści dokumentu.
4. Nie mamy wiarygodnego, aktualnego mapowania wszystkich pól profilu, szklenia, kolorów, klientów i preferencji dokumentu na natywne akcje WindowHub wraz z odczytem zwrotnym.
5. Nie znamy wymiarów ani kierunków, więc nawet przyszły wykonawca nie powinien sam składać produkcyjnej konstrukcji z przypadkowymi wartościami 1000x1000.
6. Model rozmowy potrzebuje poprawnie podłączonego klucza Vercel AI Gateway; `provider_connected=True` potwierdza tylko obecność konfiguracji, nie powodzenie żądania.

## Test dostępny już teraz

```powershell
python -m pytest -q tests/test_navimind_toptrans_live_preflight.py
python tools/check_navimind_toptrans_acceptance.py
```

Polecenie nie otwiera WindowHub, nie dokonuje edycji. Po nim uruchom `tools/start_navimind_owner.ps1 -ExpectedOffer 'OFR/4811-'`, jeśli klucz był już zapisany przez `setup_navimind_owner_gateway.ps1`. Obecny program weryfikuje oferty na żywo, ale nie wykonuje misji tworzenia od zera. Wykonanie testujemy tylko na disposable OFR.

## Następna implementacja

Zbudować udokumentowany przepływ: inbox -> analiza konstrukcji -> pytania o brakujące dane -> zatwierdzony plan dwóch pozycji -> weryfikacja klienta i ustawień dokumentu -> kontrolowane UIA V2 w WindowHub -> readback każdej pozycji -> raport. Żadnych deklaracji sukcesu z samych testów offline.
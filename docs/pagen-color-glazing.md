# Kolor, szklenie i odczyt katalogu PAGEN

Zlecenie JSON obsługuje opcjonalne pola `color` i `glazing`. Są to dokładne
etykiety z aktualnej listy `Kolor` i `Szyba`. Adapter ustawia je dla całego
formularza. Nie interpretuje wyboru wspólnego jako odrębnych ustawień każdej
pozycji. Różne kolory/pakiety w pozycjach wymagają odrębnych formularzy lub
innego adaptera; specyfikacja per-pozycja nie jest obecnie obsługiwana.

Niepodane wymaganie ma status `not_requested`, a nie `verified`. Wykonawca
nie zmienia wtedy tej kontrolki i nie twierdzi, że domyślna opcja spełnia
wymagania klienta. Brak wybranej opcji blokuje edycję pozycji i pokazuje
odczytane dostępne etykiety. Profil może być już wybrany w tym momencie.

## Pierwsze uruchomienie z wyborem dostępnych opcji

```powershell
& .\.venv\Scripts\python.exe .\tools\run_pagen_order.py --order-file .\examples\pagen-two-windows.json --execute-live --headed --choose-options --keep-open --save-order .\zlecenie-pagen-kolor-szyby.json --output .\test-pagen-kolor-szyby.json
```

W PowerShell pojawią się dwie numerowane listy, odczytane po wyborze profilu.
Wpisz numer koloru i numer szklenia. `0` świadomie pozostawia dane wymaganie
nieokreślone (także jeśli było wcześniej w pliku). Wyłączone i puste opcje nie
są proponowane. Wykonawca ponownie otwiera formularz, rozwiązuje specyfikację
wobec aktualnego katalogu, uzupełnia i weryfikuje dane. Nie wymaga serwera AI
ani parowania Workspace; to samodzielny adapter konfiguratora.

`--save-order` zapisuje specyfikację po wyborze, jeszcze przed wykonaniem
formularza. Istnienie tego pliku nie oznacza poprawnego wykonania zadania.
`--output` zawiera odczyt dopiero po końcowej weryfikacji; stary raport nie jest
aktualizowany przy niepowodzeniu. Bieżący wynik sprawdzaj w PowerShell.

## Kolejne uruchomienie automatyczne

```powershell
& .\.venv\Scripts\python.exe .\tools\run_pagen_order.py --order-file .\zlecenie-pagen-kolor-szyby.json --execute-live --headed --keep-open --output .\test-pagen-kolor-szyby.json
```

Kolor i szyby są wtedy pobierane ze specyfikacji bez dodatkowych pytań. Opcje
można również podać przez `--color` i `--glazing`; nadpisują wartości z JSON.
CSV w dotychczasowym formacie pozostaje zgodny; dodatkowe ustawienia można
podać flagami lub wybrać przez `--choose-options` i zapisać jako JSON.

## Sam katalog

```powershell
& .\.venv\Scripts\python.exe .\tools\run_pagen_order.py --order-file .\examples\pagen-two-windows.json --inspect-catalog --execute-live --output .\katalog-pagen.json
```

Odczytuje opcje profilu, typu okna, koloru i szklenia. Przy podanym zleceniu
najpierw wybiera jego profil; nie uzupełnia pozycji. Bez `--order-file` pokazuje
listy w stanie początkowym formularza, nie katalog po wyborze konkretnego profilu.

## Weryfikacja i granice

Po wpisaniu pozycji adapter ustawia wspólne opcje i sprawdza je z odczytu,
a następnie ponownie kontroluje wszystkie ilości, wymiary, typy i profil.
Reset koloru po zmianie szklenia albo reset wymiaru powoduje `review`.
Raport `shared_options` zachowuje wymagania, odczytane etykiety i wartości
oraz zakres `whole_form`. Formularz nie jest wysyłany i nie tworzy oferty WH.
To sprawdzanie znanych kontrolek DOM, nie ogólne rozpoznawanie nieznanych ikon.

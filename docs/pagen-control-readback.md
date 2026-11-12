# Specyfikacja → dostępna kontrolka → odczyt wyniku

Adapter PAGEN rozpoznaje znane role i etykiety formularza. Dane zlecenia nie są
już traktowane jako techniczne wartości opcji: lista jest odczytywana z DOM,
a dokładnie dopasowana etykieta jest wiązana z odczytaną wartością opcji.
Wspólny moduł `catalog_control_binding` nie zależy od Playwright ani Windows.

Dobór normalizuje wyłącznie wielkość liter, białe znaki i Unicode NFKC. Nie usuwa
członów nazw, nie wybiera podobnych produktów ani pierwszej opcji domyślnej.
Brak, duplikat, wyłączenie lub współdzielona wartość wymagają sprawdzenia.

Przed wyborem adapter sprawdza jednoznaczność/dostępność kontrolki oraz ponownie
odczytuje listę. Zmiana katalogu blokuje przygotowany krok. Po wyborze porównuje
odczytaną wartość. Każdą ilość i wymiar sprawdza zaraz po wpisaniu. Po dodaniu
kolejnego wiersza kontroluje zachowanie wcześniejszych pozycji. Na końcu odczytuje
cały formularz i zapisuje pary `requested`/`observed` w raporcie JSON.

## Widoczny test na Windows

```powershell
& .\.venv\Scripts\python.exe .\tools\run_pagen_order.py --order-file .\examples\pagen-two-windows.json --execute-live --headed --keep-open --output .\test-kontrolek-pagen.json
```

Chromium pozostaje otwarty do naciśnięcia Enter w PowerShell, także jeśli
formularz wymaga sprawdzenia. Raport powstaje tylko po poprawnej końcowej
weryfikacji. Przy błędzie istniejący raport ze starszego uruchomienia nie jest
aktualizowany; bieżący wynik to `PAGEN_RESULT=review`, nie zawartość starego pliku.

Wynik poprawnego odczytu zawiera `status: form_verified`,
`evidence: browser_dom_readback`, `submitted: false`, `wh_offer_created: false`.
To wypełnienie formularza wyceny, nie oferta cenowa WH ani wysłane zapytanie.
Adapter obsługuje profil, typy okien, ilości i wymiary. Dobór kolorów, szyb i okuć
w WH wymaga osobnego podłączenia katalogu i kontrolek. Ten test nie dowodzi
rozpoznawania nieznanych ikon na podstawie obrazu.

Testy jednostkowe obejmują wartości katalogowe inne niż etykiety, niejednoznaczne
nazwy, wyłączone opcje, zmianę listy, niezgodny odczyt oraz utratę wcześniejszych
wartości po dodaniu kolejnego wiersza. Testy korzystają z atrap kontrolki/strony;
prawdziwy przebieg przeglądarkowy należy uruchomić powyższym poleceniem.

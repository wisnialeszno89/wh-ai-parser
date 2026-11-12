# Gotowość programu do zadania ofertowego

Priorytet: zapytanie → specyfikacja → dostęp do WH → odczyt bieżącego etapu →
pozycje → kontrola szkicu → weryfikacja handlowca.

## Wdrożony krok

`NewWindowOfferMissionPlanner` przed wyborem czynności sprawdza aktywny proces.
Dla innego procesu prosi o otwarcie/przełączenie WindowHub. To nie jest dowód,
że WH nie jest zainstalowany lub uruchomiony w tle.

Znane tytuły logowania PL/DE/EN albo widoczna natywna kontrolka hasła powodują
`wait_user_login`. Decyzja nie zawiera akcji ani wartości do wpisania. Użytkownik
loguje się bezpośrednio w programie. Runner `live_windowhub_new_offer_mission.py`
zwraca wtedy `OFFER_ACCESS=waiting_for_user_login` i kod 4. Nie odpytuje w pętli
ani nie przechowuje hasła. Po ponownym uruchomieniu misji ten sam cel jest
planowany z nowej obserwacji; dotychczasowe kliknięcie nie jest odtwarzane.

Rozpoznawanie logowania korzysta z tytułu/nazw kontrolek, nie z ich wartości.
Nieznane okno pozostaje nieobsługiwane; brak znanego tytułu logowania nie
potwierdza sam w sobie udanego uwierzytelnienia. To mechanizm planera i runnera
WH, jeszcze nie automatyczne wznowienie zadania z czatu Workspace.

## Test bez WH

```powershell
& .\.venv\Scripts\python.exe .\tools\check_windowhub_offer_readiness.py --with-archive --with-offer --output .\test-gotowosci-oferty.json
```

Raport oddziela trzy źródła:

- sceny syntetyczne: niewłaściwy program, logowanie, ponowny odczyt etapu;
- rzeczywiste archiwalne zrzuty repo: dopasowanie znanych ikon do znanych obrazów;
- symulator: specyfikacja dwóch pozycji, zapis i porównanie z testowym zleceniem.

`offline_checks_passed` nie oznacza wykonania oferty w WH. Raport zawiera
`live_actions: 0`, `wh_offer_created: false`. Rozpoznanie znanych ikon nie jest
jeszcze rozpoznawaniem dowolnej nowej ikony lub innego układu programu.

## Publiczny konfigurator

Istniejący `tools/run_pagen_order.py` sprawdza przenoszenie danych JSON/CSV do
znanego formularza PAGEN i odczyt wymiarów/ilości z wyniku. To adapter konkretnego
formularza, nie test ogólnego rozumowania w nieznanym programie. Kończy na
uzupełnieniu formularza, nie wysyła zapytania handlowego i nie tworzy cen/oferty WH.

Następny test integracyjny: połączyć specyfikację pozycji z obserwacją aktualnych
kontrolek, dostępnością katalogu i kontrolą zapisanego szkicu. Oceniać niezależnie:
zgodność danych, skuteczność nawigacji, rzeczywisty zapis i gotowość dla handlowca.
Ceny katalogowe zachowujemy; rabat tylko na zlecenie. Brak produktu lub ceny
powoduje pozycję opisową do uzupełnienia, a nie wymyśloną konfigurację/wycenę.

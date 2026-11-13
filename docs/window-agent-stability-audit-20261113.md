# Agent okienny: audyt stabilności, 13.11.2026

Cel: zapytanie PL/DE → specyfikacja każdej pozycji → dobór w dostępnym katalogu →
wykonanie → odczyt i kontrola zapisanego szkicu oferty.

## Sprawdzona baza

- Wykonawca: gałąź `feat/windowhub-order-preferences-20261109`, baza `4f098e0f`.
  `main` tego repo jest starszy; nie jest punktem odniesienia dla aktualnych możliwości.
- NaviMind: `main`, baza `01d1f11a`. Vercel produkcyjny `navimind-712i38tvu-adams-projects-080d3918.vercel.app`
  ma status READY. Prywatny GET `/api/workspace/document-plan` zwrócił 200,
  `ready: true`, `reader: PDF-R3`. To potwierdza renderer, nie poprawność OCR/modelu.
- 87 testów lokalnego parsera, adaptera PAGEN i planera gotowości WH przeszło.
  Po poprawkach importu i odroczeniu importu wykonawcy Windows: 100 testów
  w tym import z czatu oraz tekstowy PDF przeszło na Linuksie.
- Offline readiness: pięć scen dostępu, pięć archiwalnych widoków konstruktora,
  dwie pozycje w symulatorze. `LIVE_ACTIONS=0`, brak oferty wykonanej w WH.

## Jak rozumie wiadomości klienta

`python tools/benchmark_window_enquiries.py` daje **2/8 kompletnych dopasowań**
oczekiwanych pól na ośmiu syntetycznych przypadkach. Proces zwraca kod 1,
bo istnieją braki. To mała próba pokrycia lokalnego `inspect_german_offer_mail`,
nie procent skuteczności całego agenta, nie ocena modelu w Workspace i nie OCR.

| Przypadek | Wynik lokalnego parsera |
|---|---|
| Niemiecki nagłówek Fenster, sztuki, mm, DKR | zgodny |
| Dwie osobne pozycje Haustür i Fenster | zgodny |
| Prefiks Pos. 1 | brak pozycji |
| Niemieckie pełne zdanie | brak pozycji |
| Polskie zapytanie | brak pozycji |
| Jednoznaczne wymiary w cm | brak przeliczenia wymiarów |
| Dreh Links zapisane słownie | brak kodu otwierania |
| innen weiß, außen anthrazit | nie odczytuje kolorów do pól |

Modelowy czytnik PDF w NaviMind jest innym torem. Dotychczasowe błędy na
rzeczywistym skanie i sama poprawność schematu nie pozwalają uznać go za stabilny.
Nie wykonano w tym audycie nowego pomiaru modelu na dokumentach klientów.

## Test internetowy

W publicznym PAGEN sprawdzono ręcznie sterowaną automatyzacją przeglądarki:
profil Premium Line (Salamander), okno stałe 1 × 1100×950 mm,
okno dwuskrzydłowe 3 × 1230×1780 mm, kolor biały dwustronny, szyba Standardowa.
Dodanie wiersza zachowało wcześniejsze liczby; końcowy DOM potwierdził obie
pozycje. Formularz nie został wysłany, brak danych osobowych i ceny.

To test bieżącego formularza i jego zachowania, **nie przebieg lokalnego
wykonawcy Python ani modelu NaviMind**. Uruchomienie lokalnego Chromium
z Playwright w środowisku audytu przerwał błąd `socket() failed: Operation not permitted`.
Test CUA nie zastępuje tej brakującej integracji.

PAGEN pozwala ćwiczyć katalog, ilości, wymiary i wspólne opcje. Nie potwierdza
osobnych profili/kolorów/szklenia dla każdego okna, szczegółowych okuć,
naświetli ani kalkulacji i zapisu gotowej oferty. Etykiety pól mówią mm,
ale tekst pomocy mówi cm: nie traktować formularza jako wzorca wymiarowego
bez wyjaśnienia tej rozbieżności. Dla zgodności z istniejącym adapterem test
sprawdzał wartości mm według etykiet; niczego nie zamówiono ani nie wyceniono.

## Wprowadzone poprawki

1. Import dokumentu odrzuca przekroczenie limitu tekstu zamiast ucinać końcowe
   pozycje. Granice, BOM oraz wielostronicowy PDF mają testy.
2. Runner importuje wykonawcę Windows dopiero w ścieżce wykonania po kontroli
   systemu. Odczyt parametrów i testy importu można uruchamiać bez Windows.
3. Osobna poprawka w NaviMind porównuje dodatkowe wymagania per pozycja w obu
   odczytach PDF. Różne opisy wyposażenia/naświetla dają review i pokazują oba
   opisy, bez scalania lub podmiany. Parafrazy też wymagają sprawdzenia.
   Wspólnego błędu obu odczytów ten mechanizm nie wykryje.

## Kolejność dalszej pracy i warunki odbioru

1. **Wspólna specyfikacja pozycji.** Połączyć tekst PL/DE i PDF z jednym
   kontraktem wykonawcy. Pola: numer i źródło, ilość, gabaryt, części konstrukcji,
   profil, strony koloru, rodzaj otwierania i perspektywa, szklenie, wyposażenie,
   usługi. Każde pole ma wartość, źródło i stan: odczytane, skorygowane,
   nieznane lub sprzeczne. Braki i sprzeczności mają dać konkretne pytania.
2. **Pomiar rozumienia.** Rozszerzyć mały benchmark o parafrazy PL/DE,
   jednostki, warianty, negacje, korekty pojedynczej pozycji, naświetla,
   elektrozaczep tylko we wskazanych drzwiach oraz rozróżnienie Ug/Uw/Ud.
   Mierzyć osobno model i parser, kompletność pozycji i poprawność pól.
   Żaden brak krytycznego pola nie może zostać uznany za gotowość wykonania.
3. **Most do konfiguratora.** Przekazywać tę samą zweryfikowaną specyfikację
   do istniejącego wiązania kontrolek. Nie przepisywać ręcznie do JSON dla
   udawania end-to-end. Brak katalogowego produktu lub szczegółowego wariantu
   daje jawne `unsupported`/pytanie, bez dobierania podobnego po cichu.
4. **Odporne wykonanie i wznowienie.** Kontrolować po każdym kroku faktyczną
   wartość, zmienione identyfikatory po AJAX, reset wcześniejszych wierszy,
   opóźnienia i stan strony. Po awarii wrócić od nowej obserwacji, bez
   dublowania pozycji; testować przerwę między dodaniem a uzupełnieniem.
5. **Gotowa oferta.** Odczytać zapisany wynik i porównać każdą pozycję ze
   specyfikacją. Ceny wyłącznie z potwierdzonego katalogu i ustawień handlowych.
   Odbiór Windows/WH wymaga rzeczywistego klienta, preferencji, wszystkich
   pozycji i ponownego otwarcia zapisanego szkicu. Bez WH tego etapu nie da
   się potwierdzić. Do tego czasu status: wersja rozwojowa.

Nie rozszerzać teraz zakresu o płatności, licencje i kosmetykę strony.
Priorytetem pozostaje zgodność danych i powtarzalna realizacja oferty okiennej.

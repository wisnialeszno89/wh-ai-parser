# NaviMind — audyt dostępu do katalogów WH Okna (25.11.2026)

## Co potwierdza producent

- Winkhaus: [WH Okna](https://www.winkhaus.pl/serwis/WH-OKNA) to program ofertowania/produkcji działający na bazach technologicznych producenta. [WH Storage](https://www.winkhaus.pl/pl/newsroom/prasa/modul-wh-storage) obejmuje m.in. profile, kolory, szklenia, okucia, rolety i wyposażenie.
- [Instrukcja WH Okna v7 (styczeń 2026)](https://whokna.com.pl/wp-content/uploads/2026/01/Instrukcja_WHOkna_v7_styczen26.pdf): rozdziały *Dodawanie nowej pozycji*, *Definiowanie wymiarów konstrukcji*, *Podstawowe parametry okna* opisują kolejność kreatora, domyślny typ „Okno”, ilość, szerokość/wysokość oraz wybór koloru i kategorii wzmocnienia. Kolor na liście pochodzi z lokalnej bazy i może mieć konfigurację jednostronną/dwustronną. „Zakończ” przechodzi do fazy konstruowania, a NIE oznacza gotowej oferty handlowej.
- [Baza wiedzy WH Okna](https://whokna.com.pl/baza-wiedzy/) potwierdza oddzielne operacje i restrykcje okuć, szyb, profili i rolet. Zestawy dostępne w programie zależą od bazy i konfiguracji konkretnego producenta.
- [WH Konfigurator](https://www.winkhaus.pl/pl/serwis/WH-OKNA) jest osobnym modułem internetowym z deklarowanym API. Nie jest to dowód, że instalacja desktopowej wersji WH Okna daje lokalne publiczne API ani dostęp do tabel MSSQL.
- [Instrukcja BAZY/WH Okna](https://whokna.com.pl/wp-content/uploads/2026/01/Instrukcja_WHOkna_v7_styczen26.pdf) rozróżnia bazę handlową, technologiczną i typy. Do pracy na SQL potrzebne są właściwe połączenie, prawa i zgodność licencji. **Nie należy próbować zapisu do bazy SQL w celu testowania agenta.**

## Aktualny stan NaviMind (tylko w repo, bez testu realnej instalacji)

| Kategoria | Znane mapowanie UIA | Potwierdzono rzeczywiste opcje? | Automatyczny wybór? |
| --- | --- | --- | --- |
| System profili | `profile_system_picker` — przycisk bez pewnego AutomationId; wymagane douczenie | Nie | Nie |
| Kolory profili | `profile_color`, ComboBox `1054`, kreator podstawowych parametrów | Nie | Nie |
| Wzmocnienia | `reinforcement_category` `1831` + znane radia | Nie | Nie |
| Szyby | `glazing_package` `1033`, `spacer_frame` `1035`, `spacer_frame_color` `1034` | Nie | Nie |
| Okucia | `hardware_profile` `1012`, `hardware_group` `1013`, kolory `1054`/`1545` | Nie | Nie |
| Parapety | `sill_type` `1227`, `sill_color` `1054`, `sill_endcap` `1820` | Nie | Nie |

Identyfikatory pochodzą ze znanych mapowań i testów UIA w repo. Nie są gwarancją, że Twoja wersja lub bieżąca baza wyświetli te same kontrolki. W szczególności `1054` jest ponownie używany na wielu ekranach; wymagane jest także sprawdzenie etapu i etykiety. Program może korzystać z okien modalnych, list natywnych, drzew lub siatek, których wartości nie są automatycznie widoczne przez `get_value`.

## Bezpieczny test rzeczywisty — etap A: samo czytanie

1. Zaktualizuj repo do gałęzi `feat/navimind-unified-document-engine-20261125` (PR #240). Nie uruchamiaj wcześniej zakładanych starych wersji panelu.
2. Włącz WindowHub i przygotuj **niezapisany, testowy dokument**. Nie otwieraj aktywnego zlecenia produkcyjnego ani aplikacji BAZY w trybie edycji.
3. Ręcznie przejdź do `Podstawowe parametry okna`. Bez rozkładania list wpisz w terminalu repo:

   ```powershell
   python tools/inspect_navimind_catalogues_live.py
   ```

   Skrypt obserwuje wyłącznie aktywny ekran, nie przełącza okna, nie klika, nie zapisuje, nie odpyta SQL, nie wyśle treści do API. Wynik podaje liczbę widocznych natywnych pól i bieżących odczytów (ale bez ich wartości).
4. Ręcznie rozwiń `Wybierz kolor profili` i, nie zamykając listy, uruchom:

   ```powershell
   python tools/inspect_navimind_catalogues_live.py --show-local-options
   ```

   Opcja jawnie wypisuje lokalnie maksymalnie 25 widocznych etykiet `ListItem`/`TreeItem`. **Nie przypisuje automatycznie** opcji do konkretnego ComboBox; dropdown może być osobnym popupem. Dane nie są wysyłane do chmury. Przed udostępnieniem wyniku usuń dane klienta i cenniki.
5. Powtórz odczyt dla profilu/systemu, szyb i okuć — tam, gdzie te etapy lub okna rzeczywiście są dostępne. Jeśli WH Okna nie pokazuje danego etapu, nie „odtwarzaj” go na siłę na podstawie dokumentacji.

## Etap B — sprawdzanie klikalności, TYLKO pod nadzorem

Ręcznie wybierz **jedną** pozycję w rozłożonej liście testowego dokumentu, następnie zamknij dropdown i uruchom ponownie odczyt bez `--show-local-options`. Sprawdź, czy `CURRENT_SELECTION_READABLE` wzrosło; do potwierdzenia **który** wariant został wybrany potrzebny jest lokalny natywny readback konkretnego ComboBox i zgodny identyfikator. Nie uznawaj zmiany `scene_fingerprint` samej w sobie za dowód poprawności wyboru.

Żeby pozwolić agentowi samodzielnie wybierać: trzeba udowodnić **(a)** rozwinięcie konkretnej listy, **(b)** unikalną pozycję i właściciela popupu, **(c)** pojedynczą autoryzowaną operację wyboru, **(d)** natywny odczyt wybranego identyfikatora/tekstu, **(e)** zmianę poprawnych parametrów konstrukcji i jej zgodność z lokalną bazą. Na razie agent działa tutaj tylko w trybie diagnostycznym. Nie uprawniać modelu do arbitralnego kliknięcia.

## Interpretacja wyników

- `NATIVE_MAPPED`: liczba rozpoznanych natywnych kontrolek w **aktualnym** kreatorze, nie liczba dostępnych artykułów w SQL.
- `CURRENT_SELECTION_READABLE`: bieżąca wartość pola jest odczytywalna; nie dowodzi liczby wariantów.
- `NATIVE_EXPAND_PATTERN`: liczba natywnych kontrolek, które udostępniają interfejs `ExpandCollapse` (odczyt bez rozwijania).
- `NATIVE_SELECTION_PATTERN`: liczba kontrolek, które udostępniają `SelectionItem`; nie stanowi dowodu wybrania elementu.
- `CLICKABLE` w starym podsystemie percepcji oznacza ogólną możliwość interakcji, nie potwierdza implementacji wzorca UIA. Nowy audyt celowo trzyma te informacje osobno.
- `MISSING` i `AMBIGUOUS`: niedostępna albo niejednoznaczna kontrolka, potrzebna demonstracja lub nowy mapping.
- `CATALOGUE_ITEMS_ENUMERATED=False`: pełna lista opcji nie została zweryfikowana.
- `CATALOGUE_SELECTION_EXECUTABLE=False`: żaden automatyczny wybór nie został potwierdzony.
- `visible_unattributed_items`: liczba widocznych w scenie elementów list; mogą należeć do innej listy.

**Ważne:** wartość klienta/producenta może być poufna. Domyślny wynik audytu używany w czacie nie zawiera nazw artykułów, cenników, wartości pól, tytułu klienta czy identyfikatorów okien.

# Jedna specyfikacja dla zapytania i wykonawcy

Format `window-offer/1` jest wspólną granicą NaviMind → lokalny wykonawca.
Wersja obejmuje aktualne pola czytnika: produkt, ilość, gabaryt, listwę
transportową, otwieranie, barwy po stronach, liczbę szyb, Ug, profil odniesienia
i dodatkowe wymagania. Nie jest jeszcze pełnym modelem konstrukcji skrzydeł.

Pliki `contracts/window-offer-v1.schema.json` i przykład muszą być identyczne
w repozytoriach NaviMind oraz wh-ai-parser. Obie strony walidują ten sam schemat
(Ajv / jsonschema); przykład jest sprawdzany przez oba zestawy testów.
Zmiana niezgodna z kontraktem wymaga nowej wersji. Schema jest plikiem lokalnym,
jej `$id` nie służy pobieraniu danych z internetu.

## Wejścia w Workspace

- **Odczytaj zapytanie okienne PL/DE**: wklejenie kompletnego bieżącego tekstu,
  dwa niezależne odczyty modelu, kontrola cytatów, porównanie pozycji i pól.
  Historia rozmowy nie jest źródłem danych dla tego trybu.
- **Dołącz PDF zapytania**: dotychczasowy czytnik PDF zachowuje własny raport
  i dodatkowo eksportuje ten sam format wspólnej specyfikacji.
- **Pobierz specyfikację pozycji**: JSON przypisany do konkretnej odpowiedzi.
  Kolejne wiadomości nie podmieniają starszego wyniku. Zawartość jest w pamięci
  karty do odświeżenia; pobranie nie oznacza wykonania ani potwierdzenia oferty.

Stan każdego pola: `reported` (odczyt modelu), `missing` (brak), `conflict`
(nierozstrzygnięty odczyt) lub `corrected` (udokumentowana korekta).
`reported` NIE oznacza, że wartość jest prawdziwa. Cytaty wskazują źródło całej
pozycji, nie stanowią jeszcze dowodu znaczenia każdego pojedynczego pola.
Rozbieżności i korekty zachowują swoje opisy; korekta przechowuje wartość sprzed
zmiany i cytat użytkownika. W tekście numery stron są null; PDF zachowuje stronę.

Przy tekście cytaty muszą występować dosłownie w wiadomości (po normalizacji
białych znaków). Kontrola liczb sprawdza jawne mm/cm/m i zapis ilości; nieznana
forma zapisu wymaga sprawdzenia zamiast przyjęcia skali. Kontrola nie rozstrzyga
automatycznie, czy dany wymiar dotyczy szkła, skrzydła czy całej konstrukcji.
Niejednoznaczna numeracja lub wspólny błąd obu odczytów nadal wymaga handlowca.

## Konwencja handlowa Adama

Potwierdzona 13.11.2026: samo R/L dla okna → DKR/DKL; samo R/L dla drzwi →
DR/DL, tylko rozwieranie. Jawne DKR/DKL przy drzwiach pozostaje DKR/DKL.
HST/PSK nie są zamieniane na rozwierne. Kierunek otwierania do środka/na zewnątrz
i perspektywa nie są automatycznie dopowiadane. Konwencja nie dobiera liczby
skrzydeł, podziału, systemu ani okuć.

## Bez przepisywania do drugiego JSON

```powershell
python tools/run_pagen_order.py --specification-file .\specyfikacja-okien.json
```

Najpierw powstaje wynik kontroli kompatybilności. `ready_for_form` dotyczy
wyłącznie uzupełnienia formularza. `review` zawiera numery pozycji, pola i powody,
nie zawiera częściowego zlecenia do wykonania. `--execute-live` otwiera formularz
tylko dla kompatybilnej specyfikacji; nadal nie wysyła zapytania.
Flagi nadpisujące kolor/szyby są przy tym wejściu odrzucane. Trzeba poprawić
specyfikację u źródła, żeby wykonawca nie pracował na innych wymaganiach.

Pierwszy most celowo obsługuje wąski, sprawdzalny zakres: prostokątne okno FIX,
ilość i wymiary, dokładna etykieta profilu oraz opcjonalny biały dwustronny.
Różne profile/ustawienia w pozycjach, DKR/DKL bez kompletnej konstrukcji,
inne kolory, naświetla, listwy, szczegółowe szklenie, dodatkowe wymagania i
uwagi ogólne blokują ten adapter. Niczego nie pomija się po cichu. Końcowy
odczyt formularza zachowuje skrót specyfikacji i kolejność identyfikatorów źródłowych.

Brak wybranego szklenia ma status `not_requested`, nie `verified`. Pełna oferta
wymaga rozszerzenia konstrukcji i katalogu, cen oraz kontroli zapisanego szkicu.
Ten most nie jest jeszcze całym agentem Windows/WH.

## Weryfikacja modelu

NaviMind dodaje `scripts/check-enquiry-model.cjs`: trzy sztuczne zapytania
(PL/DE, numerowane pozycje, cm, R/L zależne od produktu, jawne DKR przy drzwiach,
elektrozaczep tylko przy wskazanej pozycji i niejasna ilość). Kontrola wykonuje
rzeczywiste API na Vercel i przerywa build przy błędnych oczekiwanych polach.
Nie używa danych klientów. Sam odczyt ze zgodnym JSON nie wystarcza do zaliczenia.
Lokalnie bez Vercel jest jawnie pomijana. Stan faktycznego wdrożenia należy
sprawdzić w logu, nie wywnioskować z obecności skryptu.

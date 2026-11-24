# NaviMind — produkty spoza katalogu i wyceny na zapytanie

## Reguła ogólna

Produkt nieuwzględniony w katalogu WindowHub nie jest powodem do
porzucenia oferty. Pozycja opisowa jest poprawnym szkicem handlowym,
o ile zawiera jawne wymagane parametry i zostanie sprawdzona.

Dotyczy w szczególności:
- drzwi wycenianych ze skrzydłem / ramą i zewnętrznym panelem, np.
  oznaczeniem **EK-02-A** wskazanym przez handlowca (Veyna to
  nazwa z przykładowego zapytania, nie potwierdzone dane katalogowe);
- bram garażowych i produktów innych producentów;
- parapetów, osprzętu oraz elementów dodatkowych;
- innych pozycji bez zweryfikowanej konstrukcji katalogowej lub ceny.

## Nowe moduły

`app/agent/offers/navimind_external_catalogue_items.py`
przekształca `ExternalItemSpec` w istniejący `PositionTask`.
Uwzględnia rodzaj produktu, dostawcę i model z zapytania,
wymagane wymiary, składniki wyceny, ewentualną ilustrację i jej
źródło. Pozycja zewnętrzna otrzymuje
`QuoteRequest.force_non_catalogue=True`, więc nie można jej
błędnie sklasyfikować jako konstrukcji katalogowej tylko dlatego,
że WindowHub obsługuje inne katalogowe okna.

Nasz istniejący `plan_commercial_quote()` może wybrać
pozycję opisową, reprezentatywną geometrię lub wpis tekstowy.
Jeżeli do reprezentacji używa np. 1000 × 1000 mm, w opisie
**musi odróżnić ten zastępczy wymiar od faktycznego wymiaru
klienta**. To nie dowód, że WindowHub potrafi rzeczywiście
narysować konkretne drzwi lub bramę.

**Cena składnika ≠ całkowita cena zestawu.**
Jeżeli znana jest cena ramy drzwi, ale nie ma ceny panelu
zewnętrznego, całkowita cena drzwi pozostaje nieustalona.
Dopiero ręcznie zatwierdzona, pełna cena z udokumentowanym
źródłem może trafić do `manual_unit_price`.

Ilustracja musi mieć źródło, opis i zgodę na jej użycie.
Zdjęcie poglądowe nie jest dowodem na identyczność modelu.
Gdy zdjęcia nie udostępniono lub brak zgody, agent może
kontynuować opisową część szkicu bez niego, raportując brak.

`app/agent/offers/navimind_external_price_research.py`
przyjmuje opcjonalne, **jawnie zamówione** porównanie cen.
Zapisuje link HTTPS, sprzedawcę, datę sprawdzenia, walutę,
kod produktu, wymiary i informacje o VAT / dostawie / montażu.
Zwraca wyłącznie propozycje do przeglądu. Porównanie
z Allegro lub zewnętrznym sklepem nigdy nie stanowi automatycznego
potwierdzenia ceny do oferty klienta.

## Ograniczenia obecnego etapu

- Moduły nie wyszukują jeszcze ofert w sieci samodzielnie;
  otrzymują dane źródłowe od późniejszego adaptera badawczego.
- Nie pobierają zdjęć ani cenników, nie logują się do sklepów,
  nie wstawiają ceny z internetu bez decyzji handlowca.
- Nie wykonują akcji w rzeczywistym WindowHub — testy
  korzystają z modelu w pamięci i istniejącego koordynatora.
- Nie zapisują ani nie wysyłają oferty i nie uznają
  produktu zewnętrznego za technicznie zatwierdzony.
- Dane demonstracyjne, w tym nazwy produktów, cena ramy i
  przykład zdjęcia, są syntetyczne. Nie są potwierdzeniem oferty
  producenta, dostępności towaru ani uprawnienia do wykorzystania
  rzeczywistej fotografii.

## Testy Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_external_catalogue_items.py \
  tests/test_navimind_external_price_research.py \
  tests/test_navimind_partial_price_continuation.py \
  tests/test_navimind_mission_chat.py \
  tests/test_navimind_quote_revision_planner.py \
  tests/test_navimind_program_router.py \
  tests/test_navimind_shared_control_host.py \
  tests/test_navimind_panel_controller.py \
  tests/test_navimind_local_input_arbiter.py \
  tests/test_navimind_v2_input_arbiter_boundary.py \
  tests/test_navimind_v2_preaction_scene_guard.py \
  tests/test_navimind_v2_shadow_audit.py \
  tests/test_navimind_memory_mission_bridge.py \
  tests/test_navimind_versioned_rule_memory.py \
  tests/test_navimind_memory_decision_bridge.py \
  tests/test_navimind_correction_rulebook.py \
  tests/test_navimind_human_handoff.py \
  tests/test_navimind_virtual_desktop_workspace.py \
  tests/test_navimind_virtual_windowhub.py \
  tests/test_navimind_mission_coordinator.py \
  tests/test_portable_editor_skills.py \
  tests/test_windowhub_commercial_quote_routes.py \
  tests/test_navimind_evidence_decision_engine.py \
  tests/test_windowhub_sales_mission_review.py

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_external_items.py
```

## Następne etapy

1. Podłączyć do czatu wyraźne polecenie: „Znajdź orientacyjną
   cenę porównywalnego produktu” oraz adapter wyszukujący rzeczywiste
   datowane źródła i obrazowe porównania, bez podstawiania ceny do oferty.
2. Weryfikować kompletne koszty zestawu: rama, panel, wyposażenie,
   transport, montaż, VAT, jednostki i waluta, bez podwójnego naliczania.
3. Dodać natywne rozpoznawanie i edycję opisowych pozycji WindowHub,
   wstawianie zdjęć po potwierdzeniu praw i readback.
4. Po zakończeniu misji przekazywać do panelu i czatu raport
   o pozycjach wykonanych i brakujących danych, a nie ogólny błąd.

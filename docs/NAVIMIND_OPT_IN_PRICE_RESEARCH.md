# NaviMind — wyszukiwanie cen na życzenie handlowca

## Nowy przepływ (PR #217)

NaviMind może przygotować szkic produktu zewnętrznego bez katalogowej
ceny, a dopiero na **jawne polecenie w aktualnym czacie misji** poprosić
zaufany moduł wyszukiwania o porównania rynkowe.

Przykłady:
- „Poszukaj ceny panelu EK-02-A”
- „Sprawdź cenę podobnej bramy”
- „Wyszukaj oferty na ten panel”

Samo „Dodaj panel, ceny nie znam” ani „Nie szukaj ceny” nie
uruchamia zapytania. Ten prosty filtr intencji nie zastępuje
pełnego rozumienia polszczyzny przez model: niejasne lub nietypowe
polecenia muszą zostać rozstrzygnięte przed wykonaniem badania rynku.

`navimind_price_search_workflow.py`:
1. sprawdza, czy polecenie jest bieżącą wiadomością człowieka
   przypiętą do właściwego dokumentu OFR;
2. wymaga `requested_by_salesperson=True`;
3. buduje ograniczone zapytanie wyłącznie z kategorii, kodu produktu,
   wymiarów i żądanej waluty (bez danych klienta, treści całej rozmowy);
4. wywołuje tylko **wstrzyknięty zaufany adapter** `PriceSearchProvider`;
5. weryfikuje i ogranicza wynik do maksymalnie 8 rekordów;
6. odrzuca wynik, jeśli w międzyczasie handlowiec zmienił zadanie;
7. porównuje oznaczenie modelu, wymiary, walutę, VAT, transport i montaż;
8. może dodać do lokalnego czatu listę cen referencyjnych wraz z
   nazwą sprzedawcy, datą odczytu i linkiem do źródła.

`ResearchReport` **nie** pozwala na wpisanie ceny, zapis, wysyłkę,
zakup czy zatwierdzenie kompletnej wyceny. Każda wartość z internetu
jest wyłącznie sygnałem rynkowym. Do oferty cenę całego zestawu
może wprowadzić dopiero osobny zatwierdzony proces handlowy.

## Istotne ograniczenie

**Nie ma jeszcze podłączonego rzeczywistego dostawcy wyszukiwania.**
`PriceSearchProvider` to ścisły interfejs integracji; bez niego
moduł zwraca `not_available`. W demonstracji działa jedynie
`SyntheticSearchProvider` z fikcyjnym rekordem, więc nie należy
mylić wyniku demonstracji z realną ceną panelu Veyna lub bramy.

Aby zapewnić prawdziwy dostęp do rynku, kolejny etap powinien
podłączyć wybrany legalny serwis wyszukiwania / API dostawcy,
sprawdzać źródłowe strony przed utworzeniem `ProviderObservation`,
obsłużyć limity i zgodność z warunkami danego portalu, następnie
zintegrować odpowiedzi z żywym modelem rozmownym.

Wywołanie zewnętrznego dostawcy i jego skuteczne połączenie z
internetem to dwa odrębne stany; raport oznacza wyłącznie
`provider_invoked=True` po użyciu adaptera.

## Testy w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_price_search_workflow.py \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_opt_in_price_research.py
```

## Następna integracja

- Wyszukiwanie w rzeczywistych katalogach dostawców i portalach
  sprzedażowych z potwierdzeniem źródeł i aktualności.
- Udostępnienie rzeczywistego polecenia w czacie NaviMind V2,
  które wywołuje adapter dopiero po weryfikacji intencji.
- Przypisanie porównania do pozycji oferty (nie tylko całej OFR),
  żeby cena panela nie została pomylona z ceną drzwi kompletnych.
- Zatwierdzenie przez handlowca dopiero pełnej kalkulacji
  (konstrukcja + panel + okucia + dodatki + koszty).

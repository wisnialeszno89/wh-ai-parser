# NaviMind — kontynuacja oferty przy braku ceny (częściowy szkic)

## Reguła handlowca

Jeżeli pozycja jest możliwa do przygotowania, ale nie ma
**zweryfikowanej ceny**, NaviMind ma dokończyć pozostałe bezpieczne
elementy i przejść dalej. Dotyczy to np. parapetu zewnętrznego z
wymiarami i opisem, ale bez dostępnego cennika.

Nie oznacza to, że powstała kompletna oferta handlowa.
Niezidentyfikowany koszt pozostaje nieustalony i jest osobno raportowany.

## Integracja z istniejącym koordynatorem

`PositionTask(..., allow_unpriced_draft=True)` aktywuje świadomie
wybrany tryb dla jednej pozycji. Domyślna wartość `False`
zachowuje dotychczasowe rygorystyczne zachowanie i starsze testy.

Zmiana działa bezpośrednio w `next_mission_intent()`:
- nadal wymagana jest jednoznaczna, świeża obserwacja dokumentu;
- utworzenie pozycji, zapis opisu i autoryzowanego zdjęcia wymagają
  niezależnego readbacku;
- brak ceny (lub nieweryfikowalne pole ceny manualnej) **nie zatrzymuje
  pozostałych pozycji**, jeśli właściciel misji wybrał szkic częściowy;
- cena **nie jest zgadywana, uzupełniana zerem ani skopiowana
  z przypadkowo podobnej pozycji**;
- nieosiągalna konstrukcja, nieweryfikowalne zdjęcie, powtarzająca
  się nieudana akcja lub niemożliwa edycja nadal wymagają przeglądu;
- po przygotowaniu innych pól końcowy `MissionIntent` ma
  `action=complete`, ale **`verified_completed=False`**
  i `reason=draft_partially_prepared_unpriced_positions`.

`mission_progress_summary()` uzupełniono o:
- `draft_positions_prepared`: liczba pozycji z potwierdzonym
  utworzeniem i opisem;
- `unpriced_position_ids`: lista pozycji, w których wybrano
  odroczenie ceny, a ceny nie zweryfikowano;
- `price_status` dla każdej pozycji;
- `ready_for_final_customer_quote=False` przy niekompletnej wycenie.

**Brak uprawnienia do automatycznego zapisu, wysyłania oraz
zatwierdzania do produkcji pozostaje bez zmian.**

## Ważne ograniczenie

Symulator modeluje utworzenie pozycji, wymiary żądane w opisie,
cenę i potwierdzenie pól. Nie odzwierciedla jeszcze natywnego
rysowania parapetu w prawdziwym WindowHub ani odczytu katalogowej
ceny producenta. Musimy nauczyć adapter WindowHub osobno,
które pola geometryczne parapetu może rzeczywiście wypełnić
i jak potwierdzić rezultat — a następnie sprawdzić wykonanie
na testowej ofercie Windows.

NaviMind nie powinien również bez dodatkowej logiki traktować
braku ceny w przysłanym cenniku jako faktu, że produkt nie ma ceny.
Może jedynie stwierdzić: **nie udało się ustalić wiarygodnej ceny
z dostępnych źródeł**.

## Testy Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_unpriced_parapets.py
```

## Następny etap

Podłączyć jawne oznaczanie braków cenowych w panelu i czacie,
a następnie zbudować źródła cen z rozróżnieniem: cena katalogowa,
cena podana przez handlowca, dostawca do potwierdzenia,
brak dostępu do ceny i brak możliwości wpisania ceny.
Wszystkie ceny zewnętrzne wymagają pochodzenia, jednostek,
waluty, daty obowiązywania i zakresu zastosowania.

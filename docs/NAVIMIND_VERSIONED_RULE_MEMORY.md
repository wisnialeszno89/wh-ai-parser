# NaviMind — trwała pamięć zatwierdzonych reguł (v1)

## Zakres

Wersjonowany magazyn JSON zachowuje propozycje, wyniki testów, zatwierdzenia i wycofania reguł między uruchomieniami Pythona. Kontekst reguły obejmuje aplikację, rodzaj czynności, pole i tagi sytuacyjne, aby zasada z WindowHub nie była bezwiednie stosowana w Excelu lub Wordzie. Pamięć jest świadomie niezależna od danych konkretnego klienta.

Pliki:
- `app/agent/learning/navimind_versioned_rule_memory.py` — schemat `navimind.learning.rulebook.v1`, atomowy zapis, kontrola sumy, generacja, walidacja;
- `app/agent/learning/navimind_memory_decision_bridge.py` — konsultacja reguł wyłącznie w trybie odczytu;
- `tests/test_navimind_versioned_rule_memory.py` — restart, wycofanie, awarie, wersje, izolacja;
- `tests/test_navimind_memory_decision_bridge.py` — odczyt przez silnik decyzji;
- `tools/demo_navimind_versioned_rule_memory.py` — demonstracja z plikiem tymczasowym.

## Zasady

- Reguła staje się aktywna dopiero po minimum dwóch potwierdzonych przykładach poprawnego zastosowania, negatywnym przypadku brzegowym i jawnej akceptacji.
- Wczytywanie niepoprawnego pliku kończy się błędem; nie zastępuje po cichu bazy pustą pamięcią.
- Przy zapisie wymagane jest zgodne `expected_generation`. Stary odczyt nie może świadomie nadpisać nowszej generacji.
- Zapis do pliku tymczasowego i `os.replace` chroni przed częściowo zapisanym plikiem przy zwykłych awariach. Nie stanowi pełnej transakcji między procesami.
- Suma SHA-256 wykrywa przypadkowe zmiany, ale **nie chroni przed celową modyfikacją przez osobę mającą dostęp do pliku**. Nie ma podpisów cyfrowych, kontroli dostępu użytkowników, szyfrowania, synchronizacji chmurowej ani blokad współbieżnego zapisu.
- Zapis jest lokalny dla wybranego środowiska. Pamięć utworzona w Codespaces nie trafia sama na komputer Windows; do produkcji będzie potrzebne kontrolowane przeniesienie do trwałego, prywatnego katalogu.
- Wartości reguł są podpowiedziami. Magazyn nie udostępnia metod sterowania aplikacją, zapisywania oferty, wysyłania zamówienia ani zatwierdzania produkcji.
- Obecnie adapter konsultacyjny jest dostępny jako funkcja, ale nie jest jeszcze automatycznie podłączony do pętli wykonywania NaviMind V2.
- Nie wpisuj do reguł haseł, tokenów, danych klientów ani poufnych danych ofertowych.

## Testy w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_versioned_rule_memory.py
```

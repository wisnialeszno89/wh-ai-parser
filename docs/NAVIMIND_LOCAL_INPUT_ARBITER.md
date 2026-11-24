# NaviMind — współdzielone sterowanie człowiek / agent

## Co już działa w tym PR

`LocalInputArbiter` zapewnia przenośny, lokalny, współbieżny mechanizm przyznawania prawa do pojedynczej operacji na komputerze. Pozwolenie `ActionPermit` dotyczy jednej generacji stanu (`epoch`) i jednego identyfikatora dokumentu.

**Sygnał przejęcia** (`takeover()`) jest ustawiany natychmiast, również gdy model jeszcze liczy wynik. Stare polecenia przestają przechodzić przez `dispatch()`. Jeśli jedna operacja już trwa, arbiter pozwala jej zakończyć pojedynczy atomowy krok, a następnie oddaje kontrolę człowiekowi. Nie próbuje przerywać wpisywania danych w połowie.

**Oddanie sterowania** (`release()`) nie przywraca starego zezwolenia. Przed wznowieniem host musi zweryfikować dokument i aktualny ekran, potem wywołać `observe_document()`. Każdy `invalidate_observation()` również unieważnia poprzednią generację.

`execute_v2_step()` obsługuje opcjonalne argumenty `input_arbiter` i `input_permit`. Po dotychczasowych zabezpieczeniach V2 przekazuje `loop.run()` do arbitra w jednym atomowym wywołaniu. Testy sprawdzają, że bez aktualnego pozwolenia funkcja wykonawcy nie zostaje wywołana.

## Istotne ograniczenia

- To **nie jest jeszcze aktywny przycisk pauzy** w Windows. Nie podłączono globalnych skrótów, ikonki w zasobniku, wykrywania ruchu myszy ani sygnałów operatora do produkcyjnego hosta.
- Parametry arbitra są aktualnie opcjonalne, żeby nie zmieniać zachowania istniejących klientów V2. Wdrożenie hosta powinno przekazywać je przy każdej operacji, bez obchodzenia arbitra inną drogą.
- `observe_document()` przyjmuje klucz przekazany przez hosta; sam nie potwierdza tożsamości WindowHub. Host musi wcześniej zastosować niezależny test wybranego dokumentu oraz kontrolę świeżości ekranu z PR #210.
- `RLock` i `Event` chronią tylko kod uczestniczący we **wspólnym procesie**. Nie uniemożliwiają innym aplikacjom lub użytkownikowi fizycznego poruszania myszą. Kompletny lokalny adapter wejścia musi używać pojedynczego wykonawcy, który sprawdza epokę i aktualny ekran bezpośrednio przed wejściem do GUI.
- Po oddaniu sterowania automatyczne wznowienie bez konfliktów jest możliwe; przy ręcznie zmienionych opisach, cenach lub pozycjach agent wymaga zatwierdzonego przeplanowania. Weryfikują to wcześniejsze testy Human Handoff.
- Nie zapisujemy, nie wysyłamy ani nie zatwierdzamy ofert na podstawie posiadania `ActionPermit`.
- Obecny PR obejmuje wyłącznie bezpieczną warstwę logiki, testy współbieżności i punkt integracji V2.

## Testy w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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
```

## Następny etap

Dodać lokalny host sterowania dla Windows, z bezpiecznym panelem przejęcia i
zwolnienia kontroli, sprawdzaniem epoki w **każdej** ścieżce natywnego wejścia,
jednym kolejkującym wykonawcą oraz testami zachowania WindowHub podczas
rzeczywistego przełączenia OFR/ A → OFR/ B → OFR/ A.

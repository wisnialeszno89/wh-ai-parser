# NaviMind — wspólny lokalny host Windows (etap obserwacyjny)

## Co nowego

`NaviMindSharedHost` dzieli jeden `NaviMindPanelController` i
`LocalInputArbiter` w obrębie **jednego procesu**. Po kliknięciu
„Wznów pracę” rozpoczyna weryfikację aktualnej oferty WindowHub.

`tools/run_navimind_shared_control_center.py` uruchamia panel Tkinter oraz
osobny wątek obserwacji UI Automation. Wątek ma własne środowisko COM;
przekazuje wyniki do małej kolejki, a GUI przetwarza je na swoim wątku.
Zebrane obserwacje są przypisane do generacji sterowania, żeby spóźniony
wynik po przejęciu myszy nie odblokował starego zadania.

Panel nadal wykorzystuje dotychczasowy projekt graficzny (grafit / royal
plum / złoto), ale wprost pokazuje status **HOST OBSERWACYJNY**.

Weryfikacja odrzuca wszystkie sytuacje bez jednoznacznego dowodu:
- obcy proces / inna aplikacja zamiast Okna.exe;
- aktywne ZLC zamiast OFR;
- dokument o niezgodnym identyfikatorze;
- brak unikalnej wybranej zakładki dokumentu;
- brak poprawnego uchwytu aktualnego okna.

`guarded_dispatch()` to przygotowany interfejs dla późniejszego wykonawcy:
po ponownym odczycie sprawdza identyczność dokumentu, zmiany UI i
pozwolenie arbitra tuż przed delegacją jednej operacji. **Bieżący panel
nie wywołuje tej metody i nie uruchamia modelu ani żadnych kliknięć.**

## Uruchomienie Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_shared_control_host.py
```

## Podgląd i test na Windows (bez sterowania myszą)

W PowerShell, w katalogu repozytorium:

```powershell
python tools/run_navimind_shared_control_center.py --expected-offer "OFR/4687-"
```

Zastąp numer dokładnym identyfikatorem **otwartej, testowej oferty**.
Nie wpisuj go w cudzysłowie z napisem `Okna -` — panel sam
rozpoznaje ten prefiks.

1. Panel startuje ze sterowaniem ręcznym. Nie pozwala agentowi działać.
2. Kliknij „Wznów pracę”. Panel przejdzie w stan oczekiwania.
3. Przełącz na WindowHub i uaktywnij dokładnie wskazaną ofertę.
4. Obserwator rozpozna ją, jeśli dostępne są potwierdzone dane UIA,
   po czym panel otrzyma stan „Oferta rozpoznana”.
5. Możesz kliknąć „Przejmij kontrolę” i znowu „Wznów”.
6. „Zatrzymaj zadanie” kończy sesję, nie zapisuje ani nie wysyła oferty.

### Ograniczenia

- Panel i moduł obserwacji współdzielą proces. **Wykonawca V2 nie jest
  jeszcze uruchamiany przez ten host**, zatem nie ma pełnego zatrzymania
  już uruchomionego niezależnie procesu agenta.
- Program nie przejmuje globalnie myszy ani klawiatury, nie podłącza
  skrótów systemowych, nie uruchamia usługi 24/7, nie zapamiętuje reguł
  i nie wykonuje ruchów w WindowHub.
- Rozpoznanie oferty na ekranie nie jest równoznaczne z upoważnieniem
  do działania. Pełna pętla V2 musi otrzymać ten sam arbiter/permit,
  a każda operacja musi przejść dotychczasowe polityki i readback.
- Przed wdrożeniem aktywnego wykonawcy potrzebne są testy na Windows,
  w tym zachowanie interfejsu przy zmianie fokusu, niepełnym UIA oraz
  przypadkach równoczesnej obsługi przez handlowca.

# NaviMind — rozmowa podczas zadania, poprawki ofert i wybór programu

## Dlaczego to ważne

Handlowiec powinien móc swobodnie powiedzieć lub napisać „zmień kolor
pozycji 3”, „zachowaj cenę montażu” albo „zrób tę ofertę od nowa” i
kontynuować rozmowę w trakcie pracy agenta. Każda wiadomość jest częścią
misji, ale **nie jest** automatycznym pozwoleniem na nieodwracalne działanie.

## Wdrożone w tej gałęzi

### 1. Lokalny czat przy wspólnym panelu

`MissionChat` jest przypięty do dokładnej oferty i współdzieli
`LocalInputArbiter` z `NaviMindSharedHost`. Przyjście wiadomości:
- wstrzymuje bieżącą misję z priorytetem człowieka;
- unieważnia stare pozwolenia wejścia;
- zwiększa numer wersji zadania;
- zachowuje wiadomość w pamięci aktualnego procesu;
- nie uruchamia żadnego działania WindowHub.

Stary wynik modelu, oparty na poprzedniej wersji zadania, jest odrzucany.
Samo ponowne wybranie tego samego OFR nie odblokowuje sesji:
`inspect_fresh_scene()` zwraca `chat_instruction_requires_approved_replan`.
Dopóki silnik V2 nie przeliczy i nie potwierdzi nowego planu,
obserwacyjny host nie przyzna zezwolenia na kontynuację.
Proponowana poprawka ma osobny cykl: proposal → operator approve/reject →
replan → niezależny readback → oznaczenie jako wykonana.

Nowe okno `tools/navimind_chat_window.py` otwiera się przez przycisk
„Rozmowa z agentem” w `run_navimind_shared_control_center.py`.
Wiadomości można pisać w trakcie trwania misji.
**Ten etap to lokalny interfejs i kolejka wiadomości, nie działająca już
rozmowa z modelem AI.** Odpowiedzi AI, interpretacja dowolnego języka i
faktyczne naniesienie korekty wymagają następnej integracji z V2.

### 2. Popraw istniejącą ofertę czy utwórz nowy szkic?

`navimind_quote_revision_planner.py` porównuje szacowaną, weryfikowalną
liczbę kroków modyfikacji z kosztem przygotowania nowego szkicu.
Nie podejmuje decyzji na podstawie arbitralnej liczby zmian.
Sprawdza możliwość bezpiecznej edycji, poprawność odczytu istniejącej
pozycji i zależności między polami.

Utworzenie nowej wersji oznacza **nowy niezapisany szkic**. Oryginalnej
oferty nie wolno usuwać ani nadpisywać bez niezależnej zgody użytkownika.
Ceny, szklenie, wymiary i konstrukcja muszą zostać ponownie zweryfikowane.

### 3. Wyszukiwanie programu

`navimind_program_router.py` to niezależna polityka wyszukiwania
programu po posiadanych możliwościach (np. edycja dokumentów albo ofert).
Sprawdza dostarczoną przez zaufanego lokalnego obserwatora listę aplikacji;
gdy pasuje dokładnie jeden zweryfikowany program, może go zasugerować.
Jeżeli programu brakuje, może zaproponować instalację **wyłącznie**
znanej aplikacji z potwierdzonym wydawcą, po uzyskaniu zgody użytkownika.

**Nie ma jeszcze rzeczywistego skanera zainstalowanych programów,
automatycznego uruchamiania ani instalatora.** Chat, strony i pliki
klienta nie mogą wskazywać dowolnego adresu pobierania jako
zaufanego instalatora.

## Testy Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_live_revisions.py
```

## Windows — test okna rozmowy

```powershell
python tools/run_navimind_shared_control_center.py --expected-offer "OFR/4687-"
```

W panelu wybierz „Rozmowa z agentem”, wpisz testową wiadomość i
wyślij (także przez Ctrl+Enter). Sprawdź, czy główny panel przejdzie w
stan sterowania ręcznego. W tym etapie żadna wiadomość nie uruchamia
działań w programie.

## Następny etap

Po udanych testach podłączyć parser intencji i odpowiedzi V2 do lokalnego
czatu, z wersjonowanymi poleceniami, potwierdzaniem zmian oraz bezpiecznym
planowaniem względem żywej zawartości oferty. Dopiero potem wdrażać
zdalne wybieranie i uruchamianie aplikacji oraz instalację za zgodą.

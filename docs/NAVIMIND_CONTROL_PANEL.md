# NaviMind Control Center — panel sterowania (pierwsza wersja)

## Wygląd

Kompaktowe okno Windows o szerokości 440 px: grafitowe tło,
akcenty royal plum i szampańskiego złota, czytelny status,
nazwa zadania, dwa duże przyciski, dwa mniej eksponowane
polecenia i jawny pasek informacyjny o połączeniu.
Standardowa biblioteka Tkinter — bez instalowania pakietów UI.

Funkcje:
- **Przejmij kontrolę** — człowiek przejmuje sterowanie; stare
  zezwolenia wejścia są unieważniane.
- **Wznów pracę** — przechodzi w stan oczekiwania na świeży odczyt,
  NIE wykonuje żadnej zaległej operacji.
- **Tryb nauki** — oznacza gotowość do ręcznego pokazywania czynności;
  nagrywanie demonstracji w tym PR NIE jest podłączone.
- **Zatrzymaj zadanie** — trwałe zatrzymanie bieżącej sesji panelu,
  z pytaniem o potwierdzenie; nie da się wznowić starego planu.
- **Zamknij panel** — nie oddaje sterowania agentowi.
- Sterowanie klawiaturą: Tab oraz Enter/Spacja dla dużych przycisków.

## Ważny stan integracji

**To jest działający lokalny interfejs demonstracyjny, nie panel
podłączony jeszcze do żywego WindowHub.**

`NaviMindPanelController` posiada własną instancję
`LocalInputArbiter`. Uruchomienie panelu jako osobnego procesu
nie przechwytuje i nie zatrzymuje agenta V2 uruchomionego w
INNYM procesie. Na ekranie wyświetlane jest zatem wprost
`TRYB DEMONSTRACYJNY • Brak połączenia z WindowHub`.

Nie próbuj używać tego panelu jako awaryjnego wyłącznika
działającego wykonawcy. Właściwe połączenie wymaga
jednego hosta sterowania, do którego należeć będzie
praca agenta, arbiter i okno panelu, oraz kontroli epoki
na natywnym wejściu.

`confirm_verified_resume()` jest przeznaczony tylko
dla zaufanego hosta: musi on naprawdę zweryfikować
właściwy dokument i aktualny ekran. Panel nie udaje,
że samo kliknięcie `Wznów` stanowi taką weryfikację.

## Uruchomienie na Windows

W PowerShell w katalogu repozytorium:

```powershell
python tools/run_navimind_control_panel.py
```

Możesz uruchomić panel bez żadnego WindowHub.
Wystarczy standardowa instalacja Pythona z Tkinter.

## Testy w Codespaces (bez graficznego środowiska Windows)

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_control_panel.py
```

## Kolejny etap

Stworzyć lokalny, uprawniony host Windows współdzielony
przez panel i V2, z kolejką poleceń, bezpiecznymi zdarzeniami
Przejmij/Wznów/Zatrzymaj oraz niezależnym odczytem
WindowHub po przerwie. Następnie dodać tryb nauki
powiązany z zatwierdzaniem reguł, bez automatycznego
przechowywania danych klienta.

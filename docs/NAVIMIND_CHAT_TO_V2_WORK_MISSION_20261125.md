# NaviMind — wspólna misja handlowca i lokalnego wykonawcy V2
_Stan integracji: 25.11.2026. Rozwój w PR #240; bez wdrożenia produkcyjnego._

## Docelowy przepływ

```text
Handlowiec → NaviMind Chat → zaufany wybór narzędzia prepare_windowhub_work
         → WorkMissionCoordinator (cel = dokładna wiadomość użytkownika)
         → BackgroundWorkMission (oddzielny wątek COM, bez blokowania Tk)
         → rzeczywista obserwacja WindowHub / kontrola MDI / semantyczny świat
         → ComputerUseV2ActionSession + dostępna wiedza o WindowHub
         → uwierzytelniony NaviMindTaskReasonerV2
         → lokalna walidacja propozycji i warunków końcowych
         → wynik i postęp w tym samym MissionChat
         → [tylko po jawnej zgodzie i przy flagach live]
           pin oferty + operator Wznów pracę + LocalInputArbiter
         → execute_one_verified_v2_action → ExecutionEngine i readback
         → wygaśnięcie pozwolenia, świeża obserwacja, nowy krok
         → weryfikacja albo zatrzymanie i przekazanie człowiekowi
```

### Zasady działania

- Celem misji jest dokładny tekst ostatniego aktywnego komunikatu użytkownika. Sam model nie konstruuje polecenia natywnego, identyfikatora HWND ani nazwy funkcji Pythona.
- Każdy kolejny komunikat człowieka unieważnia poprzednią misję i stare wyniki modelu.
- Jedna aktywna misja w lokalnym koordynatorze; domyślnie maksymalnie osiem potwierdzonych kroków. Wątki planowania nie dotykają elementów Tk.
- Wiedza o WindowHub i lokalne, zweryfikowane obserwacje kolejnych kroków są podawane do V2. Nie są pamięcią „co model twierdzi, że zrobił”, tylko zapisami po zatwierdzeniu przez wykonawcę.
- Nigdy nie utożsamiaj odpowiedzi modelu `done` z gotową ofertą. Pełna oferta musi przejść osobny odczyt pozycji/kwot i przegląd handlowca.
- Nie wykonuj automatycznie zapisu, wysłania, przekształcenia oferty w zamówienie ani akcji wymagających zgody na utrwalenie.
- Po niejednoznacznym kliknięciu nie powtarzaj go; operator dostaje powód zatrzymania, a stare zezwolenie zostaje unieważnione.
- Odczyt struktury UIA w tle jest oddzielny od zmian wymagających aktywnego pulpitu. Nie obiecuj równoczesnej pracy myszy w dwóch programach.

### Realne uruchomienie (dopiero po zakończeniu integracji i decyzji operatora)

`tools/run_navimind_shared_control_center.py` uruchamia jeden host. W trybie domyślnym nowa funkcja może lokalnie planować zadanie, ale nie wykonuje natywnych kliknięć. Wykonawca musi mieć obie istniejące flagi Windows: `WH_REAL_WINDOWHUB=1` oraz `COMPUTER_USE_LIVE=1`, a operator osobno wybiera `Wznów pracę` dla aktywnego, dokładnego OFR. To nie jest polecenie do przeprowadzenia testu na rzeczywistym środowisku już teraz.

Konfiguracja reasonera używa istniejącego `NAVIMIND_AGENT_V2_URL` (z odrębnym kluczem) albo istniejącego `NAVIMIND_AGENT_URL` i `NAVIMIND_AGENT_SECRET` dla obsługiwanej już w Vercel trasy `/api/agent/task`. Klucze pozostają lokalne, nigdy w repozytorium.

### Co pozostaje do zamknięcia

1. **Start1 / Nowa oferta bez już wybranego OFR.** Aktualny host V2 chroni dokładnie przypiętą ofertę. Przejście do nowego dokumentu i okien dialogowych musi otrzymać odrębną politykę tożsamości, zanim wielokrokowy executor może przejść dalej automatycznie.
2. **Całe zapytanie PDF jako uporządkowany kontekst misji.** Rozmowa i lokalny parser istnieją, ale przesłanie zawartości do V2 potrzebuje odrębnie jasnego zakresu zgody i śledzenia fragmentów/stron. Nie należy zakładać, że skrót 3400 znaków wystarcza do pełnej oferty.
3. **Pełny, biznesowy readback oferty.** Dziś executor potwierdza pojedynczy krok, nie kompletną zgodność wszystkich konstrukcji z zapytaniem ani ceny.
4. **Wznawianie po dialogach i nieznanych ekranach.** Nie należy ignorować niepewnej tożsamości MDI, klienta lub pola. Tryb nauki ma zbierać demonstrację, która później przechodzi walidację.
5. **Spójny wskaźnik postępu w UI i szersza obsługa programów poza WindowHub.** Podłączono rozmowę i worker do WindowHub, nie dowolną automatyzację komputera.

## Sprawdzenie bez realnego panelu

Windows GitHub Actions uruchamia izolowane testy `tests/test_navimind_work_mission.py`, `tests/test_navimind_shared_control_host.py`, testy rozmowy i narzędzi oraz dotychczasowe kontrakty WindowHub. Testy nie wprowadzają danych do prawdziwego WindowHub. Trzeba odróżnić sukces CI od potwierdzenia działania na konkretnym komputerze.

## Lokalizacja zmian

- `app/agent/runtime/navimind_work_mission.py`: pojedyncza misja, worker, pamięć zweryfikowanych kroków, brama V2.
- `app/agent/runtime/navimind_tool_router.py`: modelowy routing do przygotowania misji bez komend natywnych.
- `tools/run_navimind_shared_control_center.py`: połączenie czatu, stanu misji, planowania i lokalnego przycisku wznowienia.
- `app/agent/runtime/navimind_shared_control_host.py`: kontrola bieżącej wersji polecenia i pojedyncze natywne wykonanie V2.

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

1. **Start1 / Nowa oferta bez już wybranego OFR.** Ta ścieżka pozostaje odrębna: obecny host nie pozwala tworzyć nowych dokumentów spoza przypiętej oferty. Należy zweryfikować wiązanie nowego OFR przed automatycznym przejściem.
2. **Pełny readback biznesowy.** Weryfikujemy wykonanie każdego kroku i potwierdzony etap kreatora, ale nie porównujemy jeszcze wszystkich gotowych konstrukcji, cen i wyborów katalogowych z zapytaniem.
3. **Nieznane okna i klient.** Znane kreatory WindowHub mogą kontynuować po zweryfikowanej akcji; obce lub nierozpoznane okna zawsze powodują zatrzymanie. Selekcja klienta nadal wymaga jednoznacznego potwierdzenia.
4. **PDF i OCR.** Po zgodzie silnik V2 otrzymuje maksymalnie 7500 znaków z zatwierdzonego fragmentu oraz lokalnego podsumowania pełnych dostępnych tekstów PDF. Skany bez OCR, ucięte strony i pozycje niewykryte przez parser pozostają niezweryfikowane.
5. **Wiedza trwała i inne programy.** Manualny tryb nauki zbiera bezpieczne wskazówki o etapach, ale obecnie przechowuje je tylko w pamięci uruchomionego procesu; nie promuje sam niezweryfikowanych demonstracji do wykonywalnych umiejętności. Sterowanie innymi aplikacjami i działanie natywne bez przejęcia aktywnego pulpitu pozostają osobnymi zadaniami.

## Sprawdzenie bez realnego panelu

Windows GitHub Actions uruchamia izolowane testy `tests/test_navimind_work_mission.py`, `tests/test_navimind_shared_control_host.py`, testy rozmowy i narzędzi oraz dotychczasowe kontrakty WindowHub. Testy nie wprowadzają danych do prawdziwego WindowHub. Trzeba odróżnić sukces CI od potwierdzenia działania na konkretnym komputerze.

## Lokalizacja zmian

- `app/agent/runtime/navimind_work_mission.py`: pojedyncza misja, worker, pamięć zweryfikowanych kroków, brama V2.
- `app/agent/runtime/navimind_tool_router.py`: modelowy routing do przygotowania misji bez komend natywnych.
- `tools/run_navimind_shared_control_center.py`: połączenie czatu, stanu misji, planowania i lokalnego przycisku wznowienia.
- `app/agent/runtime/navimind_shared_control_host.py`: kontrola bieżącej wersji polecenia i pojedyncze natywne wykonanie V2.


### Nowe zabezpieczenia i połączenia

- **Kontynuacja w kreatorach:** `VerifiedWorkflowScope` akceptuje tylko dokładnie to okno dialogowe (etap, tytuł, HWND, Okna.exe), które lokalny wykonawca zobaczył po poprzednim zweryfikowanym kroku. Ręczne przejęcie sterowania lub zmiana okna unieważniają dowód. Nie wolno używać samego tytułu kreatora jako autoryzacji.
- **PDF → zadanie:** `WorkMissionCoordinator` przechwytuje wersję zgody oraz lokalne dane z dokumentu. Silnik nie otrzymuje podsumowania całych PDF bez wcześniejszej świadomej zgody w oknie (wyświetla ono łączny limit). Zmiana lub cofnięcie zgody natychmiast odbiera hostowi prawo do wejścia, a wersjonowany task nie może być wznowiony.
- **Wpisywanie danych:** tylko unikatowe, zmapowane kontrolki ofertowe, wstępnie pozycja/ilość/opis i pola pierwszej szerokości/wysokości, mogą otrzymać modelowe `write_text`. Istniejący wykonawca używa `Ctrl+A`, następnie sprawdza wartość; nie ma uprawnienia do swobodnej edycji danych klienta i cen. Zakończenie kreatora, zapis, wysyłka i konwersja w zamówienie wymagają ręcznego przeglądu.
- **Tryb nauki:** lokalny, ręczny. Wciśnij `Tryb nauki`, pokaż kroki, a następnie `Zakończ naukę`. Obserwator analizuje ograniczone do 64 przejść semantyczne zmiany UIA; model może dostać do 8 nieprzyczynowych wskazówek z bieżącej sesji, nigdy surowe nazwy klientów, wpisane wartości, współrzędne lub native ID.
- **Postęp:** panel pokazuje stan misji i wykonane, zweryfikowane kroki. Wstrzymanie po błędzie nie wykonuje automatycznego ponowienia, a przekroczony budżet powoduje przegląd.

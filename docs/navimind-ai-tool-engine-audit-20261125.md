# NaviMind: audyt połączenia modułów silnika z rozmową (2026-11-25)

## Sprawdzone w kodzie

| Moduł | Istniejąca implementacja | Stan integracji z głównym panelem |
|---|---|---|
| AI Gateway | `navimind_conversational_provider.py`, `navimind_live_conversation.py` | Rozmowa na żywo potwierdzona przez operatora |
| Win32 inventory | `windows_desktop_environment_adapter.py`, `inspect_navimind_windowhub.py` | Działa; teraz dostępny jako `find_windowhub` wybierany przez model |
| Obserwacja UIA/obrazu | `windows_desktop_agent_control_loop.py`, `windows_ui_automation_provider.py` | `inspect_active_windowhub`; read-only tylko dla pierwszoplanowego WH |
| Schowek PDF | `navimind_enquiry_inbox.py` | `enquiry_status` ujawnia tylko metadane, bez tekstu klienta |
| Katalog silnika | Kod hosta i opis obserwowanych modułów | `engine_capabilities` |
| AgentControlLoop | `agent_control_loop.py` | Istnieje, lecz NIE uruchamiany z czatu |
| ExecutionEngine + WHActionExecutor + RobotGUIExecutor | `default_executors.py`, `execution_engine.py` | Istnieją; nie dostają pozwoleń z modelu rozmowy |
| LocalInputArbiter | `navimind_local_input_arbiter.py` | Zapobiega przestarzałym pozwoleniom, właściciel wejścia |
| V2 preaction scene guard | `navimind_v2_preaction_scene_guard.py` | Istnieje, lecz nie podłączony do wywołań modelu rozmowy |
| Korekty ofert | `navimind_chat_amendment_bridge.py` | Review-only; nie udostępniono modyfikacji |
| Badanie cen | `navimind_price_search_workflow.py` | Wymaga zaufanego providera, nie aktywowane w tool registry |
| OCR | `windows_screen_text_provider.py` | W ramach lokalnej obserwacji; OCR nie autoryzuje kliknięć |

## Nowa ścieżka wykonywania

1. Użytkownik wpisuje dowolną naturalną wiadomość w NaviMind.
2. Ten sam model AI, na który działa rozmowa, otrzymuje **katalog tylko podłączonych narzędzi**.
3. Model zwraca ściśle walidowaną decyzję JSON: odpowiedź albo jedno `tool` z dokładnie znaną nazwą.
4. Host wykonuje **wyłącznie** funkcję z lokalnego jawnego rejestru. Żaden tekst modelu nie może być PowerShell, ścieżką pliku, instrukcją klikania ani zgodą na zapis.
5. Wynik narzędzia wraca do czatu po sprawdzeniu numeru rewizji zadania.

To **nie** jest jeszcze natywne `tool_calls` API, plan wielokrokowy, automatyczna instalacja programów, sterowanie WH w tle ani nauka na trwałej pamięci. Na razie model dokonuje jednego wyboru narzędzia lub odpowiada. Model nie może wybierać spośród niezarejestrowanych funkcji.

## Bramy do integracji wykonawcy V2

- Wybór właściwego procesu i HWND niezależnie od focusa; przypięcie tożsamości dokumentu MDI do jednej sesji
- Świeży odczyt kontrolki i pre-action scene guard
- Wyraźne uprawnienie człowieka do zmiany w testowej ofercie, odwoływalne przez LocalInputArbiter
- Jedna kontrolowana akcja, bez zapisu; ponowny odczyt i weryfikacja postcondition
- Natychmiastowy STOP w razie utraty fokusu, zmiany okna, niejednoznacznego targetu albo przejęcia sterowania przez człowieka
- Docelowa izolowana sesja Windows dla prawdziwej równoległej pracy handlowca

## Znane ograniczenia

- Niektóre formularze WH mogą nie udostępniać UIA; wcześniejszy odczyt dał 111 elementów na ekranie `offer_document`.
- Win32 odnajduje tylko widoczne okna bieżącej sesji; nie świadczy o instalacji/ukrytych usługach.
- LLM ma stosować jeden format JSON; nieprawidłowa odpowiedź kończy się bez wykonywania narzędzia.
- Testy offline sprawdzają kontrolę uprawnień i poprawność trasowania; uruchomienie na prawdziwym Windows i Gateway musi zostać potwierdzone przez operatora.

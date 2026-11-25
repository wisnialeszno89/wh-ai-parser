# NaviMind — audyt integracji silnika i przepływu dokumentów

Stan: 2026-11-25. Zakres: Windows Workspace (wspólny host) i źródła ofert.

## Przyczyna błędu „nie mam dostępu do PDF”

W dotychczasowej architekturze `LocalEnquiryInbox` mógł odczytać tekst PDF lokalnie, ale `LiveMissionConversation` nie miał w głównym katalogu narzędzi realnej funkcji `read_approved_enquiry`. Model otrzymywał co najwyżej status licznika PDF lub fragment po oddzielnym kliknięciu przycisku „Przeanalizuj”. Zwykłe polecenie czatu nie rozpoczynało cyklu zgody i odczytu. Pole „Dokumenty klienta” jest lokalnym schowkiem, nie polem wysyłania wiadomości.

## Stan integracji, bez deklaracji na wyrost

| Element | Implementacja w repo | Wykorzystanie przez główny Workspace |
|---|---|---|
| Rozmowa | `navimind_conversational_provider` + `LiveMissionConversation` | TAK, AI Gateway, osobny wątek |
| Wybór narzędzia przez AI | `navimind_tool_router` | TAK, wyłącznie allowlista read-only |
| Inwentaryzacja uruchomionych okien | Win32 `WindowsDesktopEnvironmentAdapter` | TAK, `find_windowhub` |
| UIA WindowHub w tle | `navimind_background_windowhub_reader` | TAK, powierzchowna struktura UIA, nie treść oferty |
| Odczyt tekstu PDF | `LocalEnquiryInbox` + PyMuPDF | TAK, wyłącznie po dołączeniu przez użytkownika |
| Dostęp AI do PDF | `LiveMissionConversation` | TAK, po zgodzie i dla ograniczonego fragmentu |
| Analiza i odpowiedź AI na PDF | `navimind_enquiry_evidence_bridge` | NOWE: dobór narzędzia, zgoda Tk, realny odczyt, drugi modelowy krok syntezy |
| Parsowanie pozycji z e-maili DE | `app.agent.intake.german_offer_mail.inspect_german_offer_mail` | NOWE: parser podłączony jako pomocnicze źródło niepewnych danych |
| Jawny stan możliwości hosta | `runtime_status_provider` | NOWE: liczba PDF, zgoda, brak praw do zapisu |
| `WindowHubFormReader` / `WindowHubDocumentReader` | istnieją | NIE, wymaga jednoznacznej tożsamości dokumentu MDI i kontroli dostępu do danych |
| `AgentControlLoop` + `ExecutionEngine` | istnieją | NIE, niepodłączone do wykonawcy z czatu |
| `LocalInputArbiter` / V2 scene guard | istnieją | Częściowo; nie upoważnia czatu do klikania |
| `window_offer_specification` | walidator kontraktu JSON istnieje | NIE, wymaga źródła przekształconego w zgodny z wersją, dowodowy spec; bez zgadywania |
| Zapisywanie/wysyłanie ofert | kod wykonawców istnieje | ZABLOKOWANE w bieżącym hoście |

## Przepływ przy naturalnym poleceniu „przeanalizuj dodany PDF”

1. PDF jest dołączany przez użytkownika i parsowany lokalnie; `PDF_COUNT` trafia do modelu jako metadane bez treści.
2. Model AI wybiera `read_approved_enquiry`. Nie dostaje danych automatycznie.
3. Jeżeli nie ma zgody, rozmowa emituje *żądanie uprawnienia*. Wątek Tk pyta właściciela o zgodę i jasno wskazuje, że fragment może zawierać dane osobowe.
4. Dopiero po zgodzie fragment maks. 3400 znaków jest dostępny dla AI Gateway. Historia zdarzenia jest przypięta do rewizji misji. Odmowa nie wysyła dokumentu.
5. Lokalny parser niemieckich zapytań przygotowuje wyłącznie pozycje na podstawie cytowanego materiału, bez domyślnych konstrukcji i bez kliknięć.
6. Wynik odczytu wraca do modelu do *jednej* odpowiedzi syntezującej po polsku; rezultat trafia do MissionChat.
7. Każde nowe źródło albo cofnięcie dostępu unieważnia poprzednie udostępnienie. Po cofnięciu wcześniejsze wiadomości, które mogły zawierać dane klienta, są pomijane w nowych żądaniach API. Nie da się wycofać już wysłanych żądań u dostawcy.

## Zastrzeżenia

- To **nie jest analiza całego wielostronicowego PDF**: `model_context` ogranicza fragment do 3400 znaków, a `summarize_approved_enquiry` do 2800 znaków dowodów. Oba moduły zaznaczają ucięcie.
- PDF będący skanem ma status wymagający OCR; bez tekstu nie podajemy fikcyjnych parametrów.
- `inspect_german_offer_mail` był projektowany do zapytań po niemiecku. Eksport WindowHub w formie PDF może nie pasować do jego struktury; model widzi więc także oryginalny fragment i ma obowiązek podać brakujące dane.
- Odpowiedź AI może zawierać nieścisłości; weryfikacja parametrów i szczegóły techniczne muszą być sprawdzone przed ofertowaniem.
- Model nie może wybrać dowolnych programów, poleceń PowerShell ani wykonywania kliknięć. Najpierw potrzebny jest potwierdzony identyfikator dokumentu, świeży odczyt celu, autoryzacja i kontrola wyniku.

## Kryteria akceptacji (Windows)

```powershell
python -m pytest -q tests/test_navimind_unified_document_engine.py tests/test_navimind_main_workspace_intake.py tests/test_navimind_live_conversation.py tests/test_navimind_ai_tool_selection.py tests/test_navimind_background_windowhub_reader.py tests/test_navimind_windowhub_one_shot_inspect.py
```

Uruchom główny panel. Dodaj PDF, następnie napisz w rozmowie: „Przeanalizuj PDF i wypisz wszystkie odczytane wymiary oraz profile”. Oczekiwane: pojawia się pytanie o zgodę, po zaakceptowaniu realny wynik źródłowy, bez obietnicy zapisu WindowHub. Sprawdź też odmowę zgody i cofnięcie dostępu; nie powinno dojść do przesłania dokumentu. Wszystkie zmiany w aplikacji Windows wymagają osobnej procedury akceptacyjnej.

# NaviMind — płynna rozmowa podczas misji (warstwa AI)

## Co zaimplementowaliśmy

Nowe `CompatibleChatProvider` i `LiveMissionConversation` tworzą
**oddzielny kanał rozmowy**. Dotychczasowy model V2
`NaviMindTaskReasonerV2` obsługuje strukturalne decyzje komputera,
więc nie wolno używać jego odpowiedzi akcji jako zwykłych odpowiedzi
czatu. Nowy kanał używa jawnie skonfigurowanego, kompatybilnego z OpenAI
`POST /v1/chat/completions` i żąda tylko zwykłego tekstu. Nie wysyła
modelowi narzędzi do klikania, zapisywania dokumentów ani uruchamiania
programów.

Interfejs `tools/navimind_chat_window.py` teraz:
- wyświetla odpowiedzi rzeczywistego modelu, gdy dostawca jest dostępny;
- działa responsywnie, bez blokowania okna Windows;
- pozwala przesłać kolejną korektę, gdy poprzednia odpowiedź jeszcze powstaje;
- odrzuca odpowiedzi z poprzedniej wersji misji;
- zachowuje pierwszeństwo człowieka i nie wznawia starego planu V2;
- w razie braku dostawcy AI wyświetla wyraźny komunikat, bez fikcyjnej odpowiedzi.

`LiveMissionConversation` używa jednego wątku modelu i co najwyżej
jednego oczekującego zlecenia. Gdy handlowiec wysyła kilka zmian podczas
jednej odpowiedzi, zostaje tylko **najnowsza** wersja rozmowy. Model
otrzymuje ostatnie wiadomości dialogu. Wyniki modelu nigdy nie mają prawa
zatwierdzić ceny, zapisu, wysyłki ani operacji GUI.

## Włączenie rzeczywistych odpowiedzi

Konfigurację ustaw lokalnie **tylko gdy zgadzasz się na wysyłanie treści
wiadomości do wybranego dostawcy AI**. Zwróć uwagę na poufność zapytań
klientów: do dostawcy trafiają ostatnie wiadomości rozmowy, ale nie jest
automatycznie dołączany numer OFR, pełna zawartość PDF ani zrzuty ekranu.

Przykład PowerShell (adres i nazwa modelu są wartościami przykładowymi):

```powershell
$env:NAVIMIND_CHAT_URL = "https://DOSTAWCA-API/v1/chat/completions"
$env:NAVIMIND_CHAT_MODEL = "NAZWA-MODELU"
$env:NAVIMIND_CHAT_API_KEY = "WŁASNY_KLUCZ_API"

python tools/run_navimind_shared_control_center.py --expected-offer "OFR/101"
```

Bez wszystkich trzech zmiennych panel działa nadal bez odpowiedzi AI
i nie wykonuje połączenia z modelem. Nigdy nie umieszczaj sekretów
w repozytorium, plikach śledzonych przez Git, demonstracjach ani
w zgłoszeniach błędów.

Model może mieć koszty zależne od liczby wiadomości. Konfiguracja
jest wyłącznie dla kompatybilnego endpointu HTTPS o ścieżce
`/v1/chat/completions`; przekierowania HTTP są zabronione.

**Nie wymagamy klucza SerpApi do rozmowy.** Wyszukiwanie produktów
i rozmowa to dwa osobne, opcjonalne kanały.

## Testy Codespaces, bez kosztów modelu

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_conversational_provider.py \
  tests/test_navimind_live_conversation.py \
  tests/test_navimind_serpapi_shopping_provider.py \
  tests/test_navimind_real_price_lookup_cli.py \
  tests/test_navimind_price_search_workflow.py \
  tests/test_navimind_external_catalogue_items.py \
  tests/test_navimind_external_price_research.py \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_live_conversation.py
```

## Granice i kolejne etapy

**Prawdziwa rozmowa nie oznacza jeszcze wykonania polecenia.**
Odpowiedź modelu to tekst doradczy. Jeśli handlowiec zleci „zmień
kolor pozycji 3”, wiadomość natychmiast unieważni poprzedni plan,
ale obecny panel sam nie wykona zmiany. Następny etap wymaga:

1. sprawdzenia przez model intencji i pozycji docelowej;
2. przygotowania ustrukturyzowanej proponowanej korekty;
3. wyraźnego zatwierdzenia zmiany, gdzie jest wymagane;
4. ponownego niezależnego odczytu WindowHub;
5. przejścia przez wspólny arbiter i polityki wykonawcy V2;
6. potwierdzenia wyniku i zrozumiałego raportu.

Również zgłoszenie „poszukaj ceny” nie wywołuje jeszcze automatycznie
SerpApi z przycisku wysyłania czatu. To osobna, jawnie zatwierdzana
czynność do podłączenia. Model rozmowny nie ma bezpośredniej możliwości
samodzielnego łączenia się z internetem ani instalowania aplikacji.

**Status:** kod integracji gotowy; testy Codespaces i prawdziwy test
z wybranym modelem wymagają weryfikacji. Nie przeprowadzono jeszcze
live testu Windows/WindowHub.

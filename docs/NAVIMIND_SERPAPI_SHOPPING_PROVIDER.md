# NaviMind — rzeczywisty dostawca cen Google Shopping (SerpApi)

## Co zostało połączone

`SerpApiShoppingProvider` obsługuje płatne API wyników Google Shopping
przez stały adres `https://serpapi.com/search.json` z
`engine=google_shopping`. Zwraca dane w formacie istniejącego
`ProviderObservation`, dzięki czemu **korzysta z wcześniejszych
zabezpieczeń** `search_price_for_current_chat()`,
`review_price_references()` i `NaviMindSharedHost.research_price_for_chat()`.

Używa wyłącznie dozwolonej kategorii towaru, opcjonalnego numeru modelu,
wymiarów i waluty. Dane klienta, historia czatu i numer OFR **nie są
wysyłane** do wyszukiwarki. Jest limit maksymalnie ośmiu wyników, limit
rozmiaru odpowiedzi, timeout, zablokowane przekierowania i brak
pobierania stron wynikowych z nieznanych serwerów.

Wynik Google Shopping nie musi zawierać wszystkich parametrów.
NaviMind:
- nie dopisuje numeru modelu, którego nie ma w tytule;
- nie przypisuje wymiarów, których nie ma w tytule;
- odrzuca cenę bez jawnej waluty, cenę niewiarygodną i wpisy
  bez poprawnego linku HTTPS;
- **nie przyjmuje** informacji o VAT, wysyłce, montażu czy identycznej
  konfiguracji wyłącznie na podstawie wyniku wyszukiwarki;
- nie używa automatycznie ceny panelu jako ceny kompletnych drzwi.

## Koszty i konfiguracja

To zewnętrzne API wymagające klucza i potencjalnie płatnych zapytań.
**Nie otrzymałem klucza ani nie wykonałem prawdziwego wyszukiwania.**
Wszystkie nowe testy i demonstracja są całkowicie offline.

Aby skorzystać w PowerShell na własnym Windows:

```powershell
$env:NAVIMIND_SERPAPI_KEY = "TWOJ_KLUCZ_API"
python tools/run_navimind_price_lookup.py --research-consent --offer "OFR/101" --category door_panel --code "EK-02-A" --width 1100 --height 2200 --currency PLN
```

Przykład zakłada **własny** klucz uzyskany ze strony dostawcy API.
Nie wklejaj klucza do GitHub, pliku źródłowego ani w rozmowie.
Warto wykorzystać bezpieczną zmienną środowiskową lub menedżer
sekretów systemu operacyjnego. Samo uruchomienie powyższego polecenia
może zużyć płatny limit SerpApi.

Bez `--research-consent` żadnego zapytania nie ma.
Bez `NAVIMIND_SERPAPI_KEY` agent zwraca `not_available`, również
bez zapytania. Polecenie nie uruchamia WindowHub, nie modyfikuje
oferty, nie zapisuje ani nie wysyła żadnych dokumentów.

Wyniki są wskazówkami do ręcznego sprawdzenia; jeżeli API zwróci
brak dopasowań, agent pozostawi cenę nieustaloną.

## Codespaces — testy bez internetu i bez kosztów API

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_serpapi_provider.py
```

## Co jeszcze trzeba zrobić

1. Zweryfikować na prawdziwym kluczu API wyniki dla konkretnych,
   rzeczywistych towarów. Samo API nie gwarantuje ceny producenta Veyna
   ani dostępności konkretnego panelu.
2. Dodać do graficznego czatu NaviMind oddzielną zatwierdzaną czynność
   „Poszukaj ceny”, nie wyzwalaną przez niejednoznaczny tekst.
3. Dodać możliwość bezpiecznego wyboru dostawcy i źródła, z
   potwierdzeniem ceny całej konstrukcji przez handlowca.
4. Oddzielić zewnętrzne porównania od cen końcowych, VAT, transportu
   i robocizny na poziomie pojedynczej pozycji oferty.

Dokumentacja API dostawcy:
https://serpapi.com/google-shopping-api

**Status:** interfejs gotowy, adapter prawdziwego HTTP napisany,
akceptacja na realnym kluczu i w Windows nieprzeprowadzona.

# NaviMind — korekty z rozmowy do sprawdzalnego planu oferty

## Co jest gotowe

Po PR #219 potrafimy rozmawiać z modelem w osobnym wątku i
unieważniać odpowiedzi dla starej wersji zadania. Teraz dodaliśmy
`navimind_chat_amendment_bridge.py`, który oddziela **tekst wypowiedzi**
od **konkretnej, możliwej do zweryfikowania korekty**.

Początkowy, celowo ograniczony zakres rozpoznawania po polsku:
- „Zmień kolor w pozycji 3 na antracyt”
- „Ustaw szerokość w poz. 3 na 1500 mm”
- „Zmień wysokość w pozycji 3 na 1800 mm”
- „Zmień ilość w pozycji 3 na 2 szt.”

To nie jest jeszcze pełna interpretacja swobodnych zapytań językowych.
Celowo nie zgadujemy złożonych, wieloznacznych wypowiedzi i nie
traktujemy tekstowych odpowiedzi modelu jako upoważnienia do działań.

Dla każdego rozpoznanego polecenia most wymaga:
1. obecnej wiadomości człowieka przypisanej do aktualnej generacji misji;
2. dokładnie jednej pozycji docelowej;
3. świeżego, niezależnie sprawdzonego dokumentu i pozycji;
4. istniejącej wartości edytowanego pola;
5. potwierdzenia, że edycja tego pola jest obsługiwana;
6. planu z modułu `plan_quote_revision()`;
7. utworzenia w `MissionChat` wniosku `PENDING` do przeglądu.

Dopiero jawne `MissionChat.approve_change()` odblokowuje uzyskanie
ustrukturyzowanej, **nadal niewykonanej** zmiany przez
`approved_amendment()`. Most sprawdza przy tym spójność zatwierdzonego
opisu, rzeczywistej propozycji, aktualnej wersji zadania i numeru oferty.
Nowa wiadomość unieważnia poprzednie zatwierdzenie.

Dodałem także wejście `NaviMindSharedHost.propose_amendment_from_chat()`
używające tego samego czatu i identyfikatora oferty.

## Czego jeszcze nie robi

- Nie edytuje rzeczywistego WindowHub ani lokalnego pliku.
- Nie zapisuje ani nie wysyła oferty.
- Nie interpretuje dowolnych wielu poprawek w jednej wypowiedzi.
- Nie wpisuje cen, ponieważ cena komponentu i cena całych drzwi
  wymagają niezależnej kontroli handlowca.
- Nie tworzy automatycznie wniosku z odpowiedzi AI. Wniosek może
  pochodzić tylko z bieżącej wiadomości handlowca.
- Nie udaje, że wartości widziane w symulatorze są wartościami
  odczytanymi z rzeczywistego Windows.

## Akceptacja w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_chat_amendment_bridge.py \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_chat_amendment.py
```

## Kolejny etap

Po tym PR niezbędne jest mapowanie prawdziwych pól WindowHub
na `PositionEvidence` z aktualnego obserwatora Windows — a potem
kompilacja zatwierdzonej, ustrukturyzowanej zmiany do lokalnej,
odwracalnej akcji V2 z readbackiem. Agent powinien przed wykonaniem
pokazać porównanie stara/nowa wartość, a potem raportować wynik.

Dopiero po testach na **jednorazowej ofercie testowej** można
rozważać rozszerzenie na wiele poprawek i zdania takie jak:
„Zmień kolor pozycji 3, ale montaż zostaw bez zmian”.

# NaviMind — zatwierdzona pamięć w planowaniu misji ofertowej

## Co jest wdrożone

`app/agent/learning/navimind_memory_mission_bridge.py` łączy trwały
`RuleMemoryStore` z istniejącym `PositionTask` i koordynatorem misji. Na
starcie planowania weryfikuje aplikację WindowHub, dokument i świeżość
obserwacji, po czym odczytuje **jedną** generację pamięci. Każde dopasowanie
musi być regułą ACTIVE, dotyczyć właściwej aplikacji, workflow, pola
`description`, tagów kontekstu i dokładnej oryginalnej treści.

Reguła może zmienić **wyłącznie propozycję opisu**. Nie zmienia ceny,
wymiarów, konstrukcji katalogowej, zdjęcia, oceny gwarancji ani uprawnień
do zapisu, wysyłki i produkcji.

Wynik `PreparedMission` przechowuje skopiowane zadania, identyfikator
reguły, numer generacji pamięci, źródłowy tekst i proponowaną korektę.
Oryginalna misja pozostaje bez zmian.

Używaj tego samego `PreparedMission.tasks` w planowaniu, wykonaniu oraz
niezależnym readbacku. Nie można planować na poprawionym tekście, a
weryfikować przeciwko oryginalnemu.

`verify_memory_generation_unchanged()` pozwala wykryć zmianę pamięci i
wymusić przeplanowanie. To kontrola wersji, nie pełna ochrona przed
wyścigiem między procesami; przy prawdziwym Windows potrzebny będzie
jednoznaczny arbiter wejścia, test epoki human-handoff tuż przed akcją i
ochrona integralności pamięci.

## Czego to jeszcze nie robi

- Nie steruje WindowHub ani nie wstawia opisu do rzeczywistego dokumentu.
- Nie jest połączone automatycznie z główną pętlą lokalnego V2 i Vercel.
- Nie rozpoznaje samodzielnie intencji poprawki z ekranu, nie przeprowadza
  nowych szkoleń ani nie zatwierdza reguł.
- Nie interpretuje reguły językowej jako dowodu technicznego lub zgody producenta.
- Nie zmienia dokumentu bez standardowego, sprawdzonego wykonawcy GUI.

## Uruchomienie w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
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

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_memory_mission_bridge.py
```

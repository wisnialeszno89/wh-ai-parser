# NaviMind Workspace — naprawa invalid_chat_message

Przyczyna na prawdziwym Windows: długi e-mail klienta wklejony do pola **Rozmowa** przekracza limit 4000 znaków przeznaczony dla pojedynczej instrukcji MissionChat. W poprzedniej wersji panel wyświetlał tylko techniczny komunikat `invalid_chat_message`.

Zmiana: po kliknięciu Wyślij panel rozpoznaje długą treść i **pyta o zgodę**, aby przenieść ją w całości do sekcji ZAPYTANIE KLIENTA / PDF. Nie skraca jej, nie wysyła do AI, nie wykonuje żadnych działań w WindowHub. Po przeniesieniu można wpisać krótką instrukcję do rozmowy. Jeśli w polu zapytania był już tekst, nowa treść zostaje dopisana.

Drugi niezależny problem to `NAVIMIND_CONVERSATION_PROVIDER_CONNECTED=False`. UI teraz pokazuje stale widoczny stan `MODEL AI: NIEPODŁĄCZONY`. Bez modelu wiadomości można zapisać lokalnie, ale nie będzie odpowiedzi. Model musi zostać osobno skonfigurowany w środowisku Windows: `NAVIMIND_CHAT_URL`, `NAVIMIND_CHAT_MODEL` i `NAVIMIND_CHAT_API_KEY`. Tylko jawna konfiguracja uruchamia zewnętrzną komunikację; wprowadzane dokumenty nie są automatycznie dołączane do API. Nie podawaj klucza w czacie lub repozytorium.

Przykład kompatybilnego endpointu wybranego dostawcy: `https://api.openai.com/v1/chat/completions`, ale wymaga osobnego aktywnego konta API i własnego klucza. Subskrypcja ChatGPT nie jest równoznaczna z dostępem do API. Nazwa modelu zależy od konta i dostawcy.

## Test na Windows

Zamknij panel, następnie wykonaj:

```powershell
Set-Location 'E:\dev\navimind-live-20261124'
git fetch origin fix/navimind-workspace-chat-intake-20261124
git switch -c navimind-chat-fix-test-20261124 --track origin/fix/navimind-workspace-chat-intake-20261124
python -m pytest -q tests/test_navimind_main_workspace_intake.py
$env:COMPUTER_USE_LIVE = '0'
python tools/run_navimind_shared_control_center.py --expected-offer 'OFR/4811-'
```

Test: wklej ponad 4000 znaków do pola rozmowy, kliknij Wyślij, zaakceptuj zaproponowane przeniesienie i sprawdź, czy pełen tekst jest w polu zapytania. Następnie wpisz krótkie polecenie. Sprawdź napis `MODEL AI: NIEPODŁĄCZONY`; to nie jest awaria ekranu, lecz brak konfiguracji osobnego modelu.

**Ograniczenia:** obecny panel nadal nie czyta zapytania dla modelu, nie generuje automatycznej listy okien i nie wykonuje wyceny w WindowHub. Takie możliwości są następnym etapem integracji.
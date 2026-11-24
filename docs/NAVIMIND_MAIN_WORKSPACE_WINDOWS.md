# NaviMind Workspace — Windows, rozmowa, mikrofon i zapytania klienta

## Funkcje

Jeden ekran: po lewej dotychczasowy panel sterowania WindowHub, po prawej historia rozmowy, pole wpisywania i dyktowania, pole tekstowe zapytania oraz przycisk wyboru PDF.

- Rozmowa nadal używa tych samych MissionChat i LiveMissionConversation; każda nowa wiadomość unieważnia stary plan.
- Bez skonfigurowanego modelu API wiadomości są lokalne i nie pojawią się automatyczne odpowiedzi AI.
- Mikrofon: po kliknięciu przycisku 'Dyktuj (Win+H)' NaviMind ustawia fokus w polu rozmowy i wywołuje systemowe dyktowanie Windows. Użytkownik sprawdza rozpoznany tekst, a następnie sam go wysyła. Zgody mikrofonowe, języki oraz ewentualne przetwarzanie chmurowe dotyczą Windows/Microsoft. NaviMind nie nagrywa plików audio, nie nasłuchuje w tle i nie odpowiada głosem.
- Wklejone zapytanie jest przechowywane wyłącznie w pamięci uruchomionej sesji. Nie zostaje samo przesłane do modelu ani WindowHub.
- Wybrany PDF jest czytany lokalnie przez PyMuPDF. Maksymalnie 15 MiB, 40 stron i 100 000 znaków odczytu. Strony bez tekstu (np. skan) i ucięte dokumenty są oznaczane jako wymagające weryfikacji. To nie jest OCR ani pełna ekstrakcja techniczna.
- Obecny Windows host nadal jest wyłącznie obserwacyjny: brak wywołania wykonawcy V2 oraz brak operacji zapisu oferty.

## Start na komputerze Windows

Najpierw zamknij poprzedni panel. W PowerShell:

```powershell
Set-Location 'E:\dev\navimind-live-20261124'
git fetch origin feat/navimind-windowhub-request-inbox-20261124
git switch -c navimind-workspace-test-20261124 --track origin/feat/navimind-windowhub-request-inbox-20261124
python -m pip install PyMuPDF
$env:COMPUTER_USE_LIVE = '0'
python tools/run_navimind_shared_control_center.py --expected-offer 'OFR/4811-'
```

## Testy Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_navimind_main_workspace_intake.py tests/test_navimind_chat_amendment_bridge.py tests/test_navimind_live_conversation.py tests/test_navimind_shared_control_host.py tests/test_navimind_panel_controller.py
```

Testy lokalnego odczytu PDF wymagają PyMuPDF. Jeśli nie ma go w środowisku, te testy zostaną pominięte; do pełnego testu zainstaluj `python -m pip install PyMuPDF`.

## Dalszy rozwój

Rozpoznawanie konstrukcji ze swobodnego e-maila po niemiecku (np. zapytania Birkenstock), przegląd wyników i braków, jawna zgoda na wysłanie danych do modelu, a dopiero później zatwierdzane operacje WindowHub V2 z readbackiem.
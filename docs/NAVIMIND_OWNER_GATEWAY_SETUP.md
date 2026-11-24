# NaviMind Owner — trwały klucz Vercel AI Gateway i uruchamianie na Windows

## Bezpieczeństwo i ograniczenia

Podczas wdrażania klucza przez integrację narzędzi nie udało się wykonać bezpiecznej operacji wygenerowania i jednoczesnego przekazania sekretu do miejsca przechowywania. Nie wolno ponawiać tworzenia bez sprawdzenia panelu API Keys. Właściciel generuje klucz samodzielnie w bezpiecznym interfejsie Vercel i nie wysyła go do czatu, GitHub ani plików ZIP.

Ustalony profil: nazwa `navimind-owner-windows`, ważność `90 days`, budżet `10 USD` **total**, odnowienie `none` (bez resetu), alerty `50%, 75%, 100%`, jeśli UI pozwala. Ustaw opcję wliczania BYOK do limitu, jeśli jest dostępna. Limit jest soft cap: żądanie, które przekroczy limit, może zostać zrealizowane. AI Gateway może wymagać ważnej metody płatności i dodatniego salda kredytów.

Panel: https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai-gateway%2Fapi-keys&title=AI+Gateway+API+Keys

Zespół: `adams-projects-080d3918` (Adam's projects). Jeśli klucz o tej nazwie już istnieje, NIE twórz duplikatu. Sprawdź identyfikator, limit i datę ważności w panelu. Vercel pokazuje wartość klucza tylko raz.

## Trwałe bezpieczne zapisanie lokalnie

Na Windows, w folderze aktualnej kopii `E:\dev\navimind-live-20261124`, po przełączeniu na gałąź zawierającą skrypty, wykonaj:

```powershell
.\tools\setup_navimind_owner_gateway.ps1
```

Skrypt poprosi o klucz w ukrytym polu. Wklej go bezpośrednio w terminal; skrypt zapisze go zaszyfrowanego DPAPI w profilu bieżącego użytkownika. **Nie uruchamiaj tego z podwyższonymi uprawnieniami ani z innego konta Windows.** Po zapisaniu usuń klucz ze schowka. Plik jest związany z kontem Windows i nie nadaje się do przenoszenia na inny komputer; zaplanuj ponowne nadanie przy zmianie komputera.

Uruchamianie:

```powershell
.\tools\start_navimind_owner.ps1 -ExpectedOffer 'OFR/4811-'
```

Launcher tylko na czas sesji ustawia `NAVIMIND_CHAT_URL=https://ai-gateway.vercel.sh/v1/chat/completions`, model `openai/gpt-4o-mini` (potwierdzony jako model Gateway), a klucz ładuje z DPAPI. Zawsze narzuca `COMPUTER_USE_LIVE=0`, bez automatycznej edycji WindowHub. Po zamknięciu panelu usuwa klucz ze środowiska PowerShell. Nie ma potrzeby ponownie wklejać sekretu przy każdym uruchomieniu. Przy wygaśnięciu klucza należy wygenerować nowy i ponownie uruchomić skrypt konfigurujący.

## Co oznacza status połączenia

`NAVIMIND_CONVERSATION_PROVIDER_CONNECTED=True` oznacza jedynie poprawną konfigurację zmiennych. Sprawdź rzeczywistą odpowiedź krótkim pytaniem, np. 'Cześć, przedstaw aktualne możliwości NaviMind'. Gdy model nie odpowiada, sprawdź Gateway Logs w Vercel (autoryzacja, 402, 429, saldo i limity). Treść wklejonego zapytania klienta i PDF **nie jest automatycznie przesyłana do modelu**.

## Docelowa architektura komercyjna

To rozwiązanie jest dla prywatnego testu właściciela, nie dla klienta końcowego. Docelowo klucz Gateway pozostaje wyłącznie na backendzie Vercel, a Windows używa krótkotrwałego tokenu sesji NaviMind. Backend weryfikuje opłaconą licencję, urządzenie, role, limity i możliwość wycofania dostępu. Ochrona deploymentu Vercel nie jest zamiennikiem tych mechanizmów. Nie publikuj programu z indywidualnym Gateway API key.

## Testy

```powershell
python -m pytest -q tests/test_navimind_owner_gateway_scripts.py tests/test_navimind_main_workspace_intake.py
```
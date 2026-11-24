# NaviMind — bezpośrednia diagnostyka Vercel AI Gateway

## Rozpoznanie

`NAVIMIND_CONVERSATION_PROVIDER_CONNECTED=True` oznacza, że obecne są URL, nazwa modelu i klucz API — **nie** jest to udane wywołanie modelu. Właściwy model i endpoint potwierdzono przez API Vercel, ale brak odpowiedzi w panelu i brak danych z Gateway Usage wymaga osobnego testu.

## Jedno żądanie bez WindowHub

Po zamknięciu poprzedniego panelu uruchom właścicielską diagnostykę:

```powershell
Set-Location 'E:\dev\navimind-live-20261124'
.\tools\start_navimind_owner.ps1 -DiagnoseChat
```

Skrypt ładuje klucz z Windows DPAPI, wykonuje **jedno** krótkie żądanie testowe do AI Gateway (`openai/gpt-4o-mini`), a potem usuwa klucz z bieżącej sesji. Nie otwiera WindowHub, nie uruchamia GUI, nie wysyła plików klienta i nie wypisuje pełnej odpowiedzi AI ani sekretu.

Po wykonaniu odczytaj `NAVIMIND_GATEWAY_SMOKE=...`. Status `SUCCESS` oznacza, że zadziałało realne żądanie. `chat_authentication_failed_401` oznacza problem z kluczem; `chat_gateway_credits_or_budget_402` — saldo lub limit; `chat_gateway_access_denied_403` — dostęp; `chat_model_or_endpoint_not_found_404` — model; `chat_gateway_rate_limited_429` — ograniczenie; `chat_transport_unavailable` — problem sieciowy, TLS, proxy lub timeout.

Klucz powinien mieć ustawiony aktywny limit 10 USD bez odnawiania. AI Gateway Usage może nie pokazywać żądań odrzuconych przed autoryzacją lub z opóźnieniem; szczegółowe logi poszukaj w https://vercel.com/adams-projects-080d3918/~/ai-gateway/logs.

**Dalszy krok:** jeśli test wykaże `SUCCESS`, przyczynę milczenia trzeba szukać w przepływie wiadomości UI, nie w autoryzacji Gateway. Jeśli wykryje błąd, nie ponawiaj wielokrotnie — prześlij tylko sam kod statusu.

## Offline

```powershell
python -m pytest -q tests/test_navimind_gateway_direct_smoke.py
```
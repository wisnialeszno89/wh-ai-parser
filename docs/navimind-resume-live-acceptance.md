# NaviMind i WindowHub – test wznowienia i dwóch pozycji

Gałąź `feat/navimind-unified-document-engine-20261125`, PR #240. Launcher korzysta
z lokalnego pliku `.env` i z istniejącej sesji `Okna.exe`.

## Połączenia

| Moduł | Dane wejściowe i wynik |
| --- | --- |
| Panel CHAT i `MissionChat` | Jawne polecenie wiąże misję z rewizją. Krótkie potwierdzenie aktualnej misji zachowuje jej rewizję i stan. |
| `LiveMissionConversation` i lokalne zapytanie | Po odrębnej zgodzie przekazuje odczytany tekst i ewidencję pozycji. CHAT ma własny endpoint i dane uwierzytelniające. |
| `WorkMissionCoordinator` i `BackgroundWorkMission` | Wiążą cel ze źródłem i dokumentem, prowadzą licznik zweryfikowanych kroków, ponownie planują na świeżej obserwacji i odbierają decyzję V2. |
| `NaviMindSharedHost`, obserwator UIA/Win32 i arbiter | Lokalne **Wznów pracę** pozwala na próbę przejścia do Start1 i ponowną obserwację. Każdy krok potrzebuje aktualnej tożsamości dokumentu, pozwolenia i sprawdzenia skutku. |
| `navimind_draft_bootstrap` i `NewOfferHandoff` | Identyfikują Start1, nowy formularz i jego powiązanie z natywnym oknem. Wyszukiwarka należy do tej samej transakcji. Wybór klienta pozostaje ręczny. |
| Vercel `navimind`, `POST /api/agent/task` | Osobne repozytorium `wisnialeszno89/navimind`. `NAVIMIND_V2_HTTP_VERIFIED=True` oznacza oczekiwaną odpowiedź na syntetyczny wniosek po autoryzacji. `NAVIMIND_V2_EXECUTOR_CONNECTED=True` oznacza zweryfikowany krok lokalny. |
| Zasady katalogowe i ewidencja pozycji | Wymiary i ilość są porównywane z zapytaniem. Opcja katalogowa wymaga jednoznacznej tożsamości i odczytu. Niezależne potwierdzenie gotowej pozycji i przejście do następnej pozostają do połączenia w panelu. |

## Uruchomienie Windows

Uruchom z katalogu lokalnej kopii tej gałęzi, gdy WindowHub jest otwarty.

```powershell
.\tools\Start-NaviMind-TwoWindows.ps1 -RequestFile .\examples\navimind_two_window_smoke.txt -Live
```

Użyj lokalnego przycisku **Przeanalizuj dokument w NaviMind** do zatwierdzenia
źródła. Napisz „Przygotuj nową, niezapisaną ofertę dla Top Trans Artur Janik
na dwie pozycje z zatwierdzonego zapytania”. Podczas prowadzonych osobno prób
pozostaw WindowHub na Start1, na istniejącej ofercie, w edytorze konstrukcji albo
w tle. Używaj wyłącznie testowych dokumentów i nie zamykaj ani nie modyfikuj
istniejącej oferty podczas testu.

| Próba | Oczekiwany dowód |
| --- | --- |
| Kontynuacja zza panelu | Po „okej zrób ofertę” nadal jest ten sam plan. Dopiero lokalne **Wznów pracę** inicjuje przejście do Start1 i próbę otwarcia nowej oferty. |
| Nowy dokument | Jeden formularz **Właściwości dokumentu**, powiązany z wywołaniem Start1. Przy niejednoznacznym Start1 sprawdź kod blokady. |
| Wyszukiwarka klienta | Pojawia się jedna tabela pod `IDC_ZAMAWIAJACY` lub powiązany natywny dialog **Wybór klienta**. Przy braku dowodu uruchom tylko odczyt `python -m tools.probe_windowhub_live_popup` i pokaż rozwiniętą listę w nowym formularzu. Przy potwierdzonym otwarciu przetestuj ręcznie filtr `Top`. |
| Przekazanie do kreatora | Po wskazaniu klienta i zatwierdzeniu właściwości dokumentu użyj **Wznów pracę** oraz wróć do WindowHub, aby obserwator zweryfikował aktywny dokument lub kreator. |
| Konstrukcje | 1 szt. 1500×1400 mm, biała od wewnątrz, antracyt od zewnątrz. 1 szt. 1300×1200 mm, biała z obu stron. Dla obu VEKA Perfectline, 2-fach, activPilot. Wybór otwierania pozostaje decyzją operatora. Rabaty 10% i 15% wymagają odrębnego potwierdzenia. |
| Zatrzymanie | Nawet przy braku odczytu albo zmianie okna nie ponawiaj w ciemno otwierania, wyboru lub potwierdzenia. Zostaw dokument otwarty i niezapisany. |

Pierwszy etap wymagający implementacji po potwierdzeniu otwarcia listy to
automatyczne użycie filtra, wybór jednej istniejącej firmy i odczyt wartości
kontrahenta w oryginalnym formularzu. Repozytorium zawiera te próby w ścieżce
terminalowej. Panel potrzebuje osobnych, aktualnych uprawnień dla wpisania
filtra, wyboru wiersza i zatwierdzenia właściwości dokumentu.

Do dalszej demonstracji potrzebne są widoczny wariant profilu Perfectline,
lista kolorów obu stron, pakiet dwuszybowy, activPilot ze znanym otwieraniem,
bezpieczne przejście do edytora i odczyt obu skonfigurowanych pozycji. Rabaty
i akcesoria nie są częścią automatycznej konfiguracji w tej wersji.

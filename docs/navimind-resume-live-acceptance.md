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
| `navimind_draft_bootstrap` i `NewOfferHandoff` | Identyfikują Start1, nowy formularz i jego powiązanie z natywnym oknem. Wyszukiwarka i odczyt klienta należą do tej samej transakcji. |
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
| Wyszukiwarka klienta | Pojawia się jedna tabela pod `IDC_ZAMAWIAJACY` lub powiązany natywny dialog **Wybór klienta**. Przy braku dowodu uruchom tylko odczyt `python -m tools.probe_windowhub_live_popup` i pokaż rozwiniętą listę w nowym formularzu. Jeśli automat nie potwierdzi wyniku, użyj filtra `Top` ręcznie. |
| Przekazanie do kreatora | Po wskazaniu klienta zostaw właściwości otwarte i użyj **Wznów pracę**. Agent sprawdzi pola cenowe i spróbuje potwierdzić formularz. |
| Konstrukcje | 1 szt. 1500×1400 mm, biała od wewnątrz, antracyt od zewnątrz. 1 szt. 1300×1200 mm, biała z obu stron. Dla obu VEKA Perfectline, 2-fach, activPilot. Wybór otwierania pozostaje decyzją operatora. Rabaty 10% i 15% wymagają odrębnego potwierdzenia. |
| Zatrzymanie | Nawet przy braku odczytu albo zmianie okna nie ponawiaj w ciemno otwierania, wyboru lub potwierdzenia. Zostaw dokument otwarty i niezapisany. |

Do dalszej demonstracji potrzebne są widoczny wariant profilu Perfectline,
lista kolorów obu stron, pakiet dwuszybowy, activPilot ze znanym otwieraniem,
bezpieczne przejście do edytora i odczyt obu skonfigurowanych pozycji. Rabaty
i akcesoria nie są częścią automatycznej konfiguracji w tej wersji.

## Dalsza próba po otwarciu właściwości dokumentu

Użyj polecenia „Przygotuj nową, niezapisaną ofertę dla Top Trans Artur Janik
na dwie pozycje z zatwierdzonego zapytania. Bez montażu, demontażu i wykończenia.”
Podanie usług w odrębnym zdaniu jest obsługiwane również w bieżącej misji
przed zatwierdzeniem właściwości.

Agent próbuje wpisać `Top` do rozpoznanego pola i wybrać pełną nazwę tylko
przy jednym wyniku w powiązanej tabeli. Jeśli katalog ma inną pisownię,
wskaż klienta ręcznie, pozostawiając właściwości otwarte. Po wyborze kliknij
**Wznów pracę**. Jeśli WindowHub ukrywa natywny odczyt klienta, zweryfikuj nazwę
w formularzu i dopiero wtedy użyj komunikatu „potwierdzam klienta” oraz przycisku
wznowienia. Natywnie odczytana inna nazwa wstrzymuje przejście.

Przy zleceniu „bez montażu, demontażu i wykończenia” panel ustawia odpowiadające
im trzy wyłączenia cenowe i odznacza „Bez ceny konstrukcji”. Sprawdza te pola
przed zatwierdzeniem właściwości. Po `OK` dopuszcza pracę tylko w nowym
dokumencie lub kreatorze należącym do tej samej transakcji natywnej.

„Gotowe”, „klient wybrany” oraz „preferencje ustawione” zachowują misję.
Wznowienie wymaga oddzielnego kliknięcia. Gdy obserwacja nie potwierdza
właściwego ekranu, panel oddaje sterowanie i ponownie udostępnia przycisk.
Jeśli pojawił się niepewny wynik kliknięcia, sprawdź stan przed kolejną próbą.

Dwie pozycje z przykładowego zapytania są rozdzielone w ewidencji. Parametry
otwierania nie są podane. Dobór okuć zależny od kierunku i zaliczenie
gotowej konstrukcji nadal wymagają odczytu potwierdzającego to, co wpisano
w edytorze. Zapis oferty pozostaje poza zakresem próby.


## Połączenie z modelem i wykonawcą

Uruchom poniższe polecenia w katalogu repozytorium na Windows.

| Kanał | Polecenie lokalne | Co potwierdza |
| --- | --- | --- |
| CHAT | `python -m tools.configure_navimind_chat --setup-gateway` | Test krótkiej rozmowy przez Vercel AI Gateway, przed zapisem konfiguracji. Użyj klucza utworzonego w sekcji AI Gateway → API Keys. |
| CHAT, kolejna kontrola | `python -m tools.configure_navimind_chat --probe` | `NAVIMIND_CHAT_NETWORK_VERIFIED=True` po odpowiedzi skonfigurowanego modelu. |
| NaviMind V2 | `python -m tools.check_navimind_v2_connection` | `NAVIMIND_V2_HTTP_VERIFIED=True` po przejściu autoryzacji i walidacji syntetycznego żądania. |
| NaviMind V2, naprawa | `python -m tools.check_navimind_v2_connection --setup` | Weryfikuje sekret aplikacji NaviMind i opcjonalny klucz ochrony wdrożenia, po czym zapisuje ustawienia. |

Pełny zestaw z lokalnego `.env` ma pierwszeństwo przed ustawieniami
odziedziczonymi z terminala. Testy używają sztucznych danych. Przy 401 CHAT
odśwież klucz AI Gateway. `v2_application_secret_rejected` dotyczy sekretu
aplikacji, a `v2_vercel_or_proxy_access_denied` – ochrony wdrożenia lub proxy.
Użyj lokalnych pól wejściowych instalatora. Po zmianie CHAT uruchom panel
ponownie. Po zmianie danych V2 w trakcie misji użyj **Wznów pracę**, aby
wykonawca ponownie wczytał ustawienia i zweryfikował ekran.

Przy niedostępnym CHAT lokalny odczyt zatwierdzonego dokumentu i jawne
przekazanie zlecenia do wykonawcy nadal działają. Przy przejściowym błędzie
sieciowym V2 może ponowić raz samo rozumowanie. Przy nieznanym wariancie
katalogowym potrzebuje decyzji operatora i świeżego odczytu po wznowieniu.

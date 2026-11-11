# Polecenie z NaviMind do lokalnego Windowsa

Pilot obsługuje dwie operacje: stworzenie tabeli okien oraz zmianę szerokości jednej pozycji. Model na serwerze tłumaczy polecenie na walidowane dane, a lokalny adapter wykonuje zapis przez klasyczny Notatnik Windows 10. To wykonawca konkretnych operacji, nie uniwersalny agent obserwujący ekran dowolnego programu.

1. W katalogu repo uruchom `.venv\Scripts\python.exe tools\run_navimind_desktop_bridge.py --execute-live`.
2. Zostaw PowerShell otwarty. Kod parowania zostanie skopiowany do schowka; jest też widoczny lokalnie w terminalu. Nie wysyłaj go w czacie.
3. Otwórz https://www.navimind.app/workspace na tym samym komputerze. Połącz komputer → wklej kod → Połącz. Jeśli przeglądarka zapyta o dostęp do sieci lokalnej/loopback, zezwól dla NaviMind.
4. Zaznaczone „Praca na komputerze” zmienia przycisk wysyłania na „Wykonaj”. Po odznaczeniu działa zwykła rozmowa.
5. Zleć: `Utwórz folder Oferta Top Trans i tabelę: 2 okna DKR 1000x1000 mm oraz 1 okno dwuskrzydłowe 1500x1400 mm.`
6. Po potwierdzeniu: `Zmień szerokość pierwszej pozycji na 1100 mm. Pozostałe dane zachowaj.`

Wyniki powstają w `Pulpit\NaviMind-Praca\<nazwa>\tabela-okien.txt`. Obecny pilot nie importuje wcześniej utworzonych plików, nie tworzy XLSX i nie przyjmuje skryptów ani dowolnych ścieżek. Nazwy oraz liczby są sprawdzane także lokalnie. Istniejących folderów nie zastępuje. Korekta dotyczy aktywnej tabeli w bieżącej sesji wykonawcy; po restarcie należy stworzyć nową tabelę pod nową nazwą. Przeglądarka pamięta kod tylko w bieżącej karcie.

Każdy zapis jest sprawdzany przez ponowny odczyt całego pliku. Wynik oraz zrzuty przed/po trafiają lokalnie do `NaviMind-Praca\.traces\<id>`. Zmiany użytkownika w pliku albo niezapisane zmiany w obsługiwanym oknie Notatnika zatrzymują zadanie zamiast nadpisywać dane. Przy braku potwierdzenia transportu kliknij „Sprawdź wynik zadania”; odczyta wynik bez ponawiania operacji. Zatrzymanie wykonawcy: Ctrl+C w PowerShell.

Serwer słucha tylko na `127.0.0.1:43127`, wymaga świeżego losowego kodu i dokładnego Origin `https://www.navimind.app` lub `https://navimind.app`. Kod nigdy nie trafia do Vercel/modelu. Dane tabeli i polecenie są przesyłane do modelu w celu przygotowania operacji. Nie ma tunelu, zdalnego portu Windows ani trwałej kolejki w chmurze. Czat wymaga nadal prywatnego dostępu Vercel.

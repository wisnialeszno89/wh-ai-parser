# Zapis wyniku kreatora na Pulpicie

Nowy krok `browser_save_snapshot` zapisuje aktualny widok kontrolowanej karty
Chromium jako PNG oraz odczyt tytułu, adresu bez query/fragment i tekstu strony
jako JSON. Pliki trafiają do nowego, losowego podfolderu:
`Pulpit/NaviMind-Praca/Wyniki-kreatora/wynik-.../`.

Krok nie przyjmuje ścieżki, nazwy, skryptu ani adresu. Działa przez istniejące
parowanie i `/execute`, z kontrolą rewizji i cache identyfikatora zadania.
Przed/po zrzucie odczytuje stan strony; zmiana blokuje zapis. Po zapisie czyta
pliki z dysku i porównuje je z wynikiem. Nie zastępuje wcześniejszych plików.
Dowiązany katalog docelowy jest odrzucany. Nie włącza pobierania plików ze stron.

Zrzut obejmuje viewport, a nie pełną przewijaną stronę. JSON zachowuje odczytany
tekst (do limitu obserwacji), nie wartości ukrytych pól i nie niezależnie
zinterpretowaną wycenę. `goal_verified` i `price_verified` pozostają `false`.
Zapis dowodzi istnienia plików; nie dowodzi poprawności wszystkich parametrów,
cen, podatków ani kompletności oferty. Ustaw podgląd/podsumowanie przed zapisem.

Po aktualizacji wykonawcy i ponownym połączeniu w trybie Przeglądarka można zlecić:
`Odczytaj i sprawdź aktualne podsumowanie konfiguracji. Zapisz zrzut tego widoku
oraz raport strony na Pulpicie.` Czat pokaże ścieżki PNG i JSON oraz zakres dowodu.
Jeśli zadanie wymaga ceny, której strona nie pokazuje, zgłoś brak ceny. Clean
Invoice służy do przygotowania konfiguracji zapytania, nie automatycznej wyceny.

Zdjęcie lub PDF wejściowy trzeba najpierw przekształcić w sprawdzoną specyfikację.
Istniejący OCR zdjęć nie obsługuje dowolnego PDF jako gotowego zadania GUI.
Obecna zmiana dodaje eksport, nie pełny automatyczny przepływ PDF → wycena.
Testy zapisu używają atrapy strony; rzeczywisty zapis w Chromium wymaga testu
na komputerze użytkownika z aktualnym wykonawcą.

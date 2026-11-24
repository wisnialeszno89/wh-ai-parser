# NaviMind — nauka na korektach użytkownika (Codespaces)

Każda poprawka handlowca to **kandydat** na regułę, nie polecenie globalnej zmiany zachowania. Agent zachowuje poprawioną treść. Regułę proponuje dopiero po osobnym potwierdzeniu intencji poprawki i niezależnym odczycie tej zmiany.

## Cykl bezpiecznego uczenia

1. **Zauważ:** porównaj stary stan z nowym po ręcznej edycji w identycznym dokumencie i pozycji.
2. **Potwierdź intencję:** nie ucz się przypadkowego wpisu; handlowiec świadomie potwierdza przykład.
3. **Zaproponuj:** dosłowna, czytelna korekta wartości z ograniczonym kontekstem aplikacji, procesu, pola i tagów.
4. **Testuj:** minimum dwa zweryfikowane przypadki poprawnej korekty oraz co najmniej jeden zweryfikowany przypadek poza zakresem, w którym reguła nie powinna się uruchomić. Żaden test nie może być niezweryfikowany ani nieudany.
5. **Akceptuj:** wyraźna zgoda upoważnionego użytkownika na wskazaną regułę i korektę.
6. **Stosuj:** reguła zwraca wyłącznie propozycję tekstu. Nie może sama klikać, zapisywać, wysyłać ani wprowadzać pozycji do produkcji.
7. **Wycofaj:** każdą aktywną regułę można unieważnić; system przestaje ją proponować.

### Istotne ograniczenia

- Reguła z WindowHub nie przechodzi automatycznie do Worda, Excela czy innej aplikacji.
- Korekta ceny, wymiarów lub warunków gwarancji nie staje się automatycznie nowym faktem technicznym.
- Akceptacja korekty i zgoda na zapis dokumentu to odrębne decyzje.
- Brak trwałej pamięci między sesjami, połączenia do realnego WindowHub oraz obserwacji komputera. Aktualny moduł jest czysto pamięciowy (Python); podpięcie magazynu reguł i dołączenie go do V2 wymaga osobnych testów i implementacji.
- Przykład w demonstracji symuluje akceptację i nie jest rzeczywistą zgodą handlowca.

## Testowanie w Codespaces

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_navimind_correction_rulebook.py \
  tests/test_navimind_human_handoff.py \
  tests/test_navimind_virtual_desktop_workspace.py \
  tests/test_navimind_virtual_windowhub.py \
  tests/test_navimind_mission_coordinator.py \
  tests/test_portable_editor_skills.py \
  tests/test_windowhub_commercial_quote_routes.py \
  tests/test_navimind_evidence_decision_engine.py \
  tests/test_windowhub_sales_mission_review.py

PYTHONDONTWRITEBYTECODE=1 python tools/demo_navimind_correction_learning.py
```

## Następna integracja

Przed trwałym zapisem reguł należy dodać jawne wersjonowanie, audyt, kontrolę użytkownika upoważnionego do zatwierdzenia, izolację danych klientów, walidację dowodów odczytu oraz powiązanie wyniku testu z zatwierdzaną treścią reguły. Nie wolno przejmować instrukcji z niezaufanych plików lub stron internetowych jako reguł wykonywania operacji systemowych.

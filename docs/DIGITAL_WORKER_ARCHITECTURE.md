# DIGITAL WORKER ARCHITECTURE

## Cel produktu

Universal Agent ma rozwijać się w kierunku cyfrowego pracownika biurowego, który potrafi wykonywać zadania w różnych aplikacjach, uczyć się procedur pokazanych przez użytkownika, korzystać z wiedzy firmowej i zewnętrznej oraz działać przez interfejs lokalny lub zdalny.

WindowHub jest pierwszym wymagającym środowiskiem demonstracyjnym, a nie granicą systemu.

## Model działania

```
User request
    |
    v
Task / Intent
    |
    +--> Company knowledge
    +--> Learned workflows
    +--> External knowledge
    +--> Current semantic world
    |
    v
Reasoning
    |
    v
Semantic action
    |
    v
Target resolution
    |
    +--> UI Automation
    +--> Win32
    +--> DOM
    +--> Vision / OCR fallback
    |
    v
Controlled execution
    |
    v
Verification
    |
    v
Updated world
    |
    +--> memory
    +--> learning
    +--> next action
```

## Warstwy cyfrowego pracownika

### 1. Perception

Agent obserwuje środowisko przez wiele źródeł:
- screenshot / computer vision
- UI Automation / accessibility
- Win32
- DOM w aplikacjach webowych
- OCR jako źródło uzupełniające

Perception ma zwracać znaczenie, nie tylko piksele.

### 2. Semantic world model

Agent ma rozumieć:
- aplikację i aktywne okno
- dokument / formularz / rekord
- widoczne obiekty
- wartości pól
- możliwe operacje (affordances)
- aktualny stan zadania

Koordynaty, HWND, AutomationId i inne identyfikatory wykonawcze pozostają poza modelem decyzyjnym.

### 3. Reasoning

Reasoner wybiera następną bezpieczną akcję semantyczną na podstawie:
- prośby użytkownika
- aktualnego świata
- wiedzy aplikacji
- pamięci doświadczeń
- wyuczonych workflow
- wiedzy zewnętrznej

### 4. Controlled action

Action Resolver mapuje semantyczny zamiar na odpowiednią technikę:
- semantic UIA
- Win32
- DOM
- keyboard
- mouse
- inne kontrolowane adaptery

Agent nie powinien zapisywać workflow jako makra współrzędnych.

### 5. Verification

Każda istotna akcja powinna mieć oczekiwany efekt, po którym agent ponownie obserwuje środowisko.

### 6. Learning

Tryb LEARN rejestruje pokazany przez człowieka workflow jako:
- trigger / intencję
- semantyczne akcje
- stan przed akcją
- stan po akcji
- notatki i wyjątki

Pierwsza implementacja jest celowo semantyczna i przenośna. Nie zapisuje współrzędnych ani uchwytów okien.

### 7. Memory

Pamięć ma być rozdzielona na:
- krótkoterminowy stan sesji
- doświadczenia z poprzednich zadań
- wyuczone workflow
- wiedzę firmową
- wiedzę zewnętrzną

Pierwszy WorkflowMemoryStore jest in-memory i stanowi granicę architektoniczną dla późniejszej trwałej pamięci.

### 8. Permissions / safety

Agent powinien rozróżniać czynności:
- odczytowe
- odwracalne
- wymagające potwierdzenia
- wysokiego ryzyka

Przykładowo przygotowanie maila może być automatyczne, a wysłanie do nowego odbiorcy może wymagać potwierdzenia.

## Tryby użytkowania

### EXECUTE

Standardowe wykonywanie poleceń.

### ASSIST

Agent pomaga człowiekowi, ale pozostawia decyzje wymagające współpracy.

### LEARN

Agent obserwuje człowieka i buduje semantyczny workflow.

Tryb wykonania (autonomous / one-step control loop) pozostaje osobnym mechanizmem runtime.

## Kierunek rozwoju aplikacji

Najpierw wzmacniamy rdzeń, potem dodajemy adaptery:

```
Universal Agent Core
 |
 +-- Windows / Computer Use
 +-- WindowHub
 +-- Excel
 +-- Word
 +-- Outlook / email
 +-- Browser
 +-- PDF
 +-- ERP / CRM
 +-- firmowe aplikacje
```

Każdy adapter powinien dostarczać perception + actions + verification, zamiast tworzyć osobny agent od zera.

## Plan etapów

1. Ustabilizować semantic world model i affordances.
2. Doprowadzić WindowHub do prawdziwej semantycznej percepcji buildera.
3. Zbudować rzeczywiste rejestrowanie działań użytkownika w trybie LEARN.
4. Zamienić demonstrację na wykonywalny learned workflow z weryfikacją.
5. Dodać trwałą pamięć workflow/experience.
6. Rozszerzyć computer-use na pliki, przeglądarkę i typowe aplikacje biurowe.
7. Dodać zewnętrzną wiedzę i firmową bazę wiedzy jako kontrolowane źródła.
8. Dodać zdalny kanał poleceń i system uprawnień.
9. Zbudować demo cyfrowego pracownika wykonującego pełne zadanie biurowe A-Z.

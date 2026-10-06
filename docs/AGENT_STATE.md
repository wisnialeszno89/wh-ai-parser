# AGENT STATE — wh-ai-parser

## Cel projektu

wh-ai-parser ma stać się uniwersalnym agentem komputerowym sterowanym poleceniem użytkownika. Agent ma obserwować środowisko, rozumieć stan aplikacji, wybierać bezpieczne działania semantyczne, wykonywać je przez kontrolowaną warstwę GUI i sprawdzać wynik. Pierwszym wymagającym środowiskiem produkcyjnym jest WindowHub i workflow przygotowania oferty okiennej/drzwiowej A–Z.

## Repo i wersja robocza

- Repo: wisnialeszno89/wh-ai-parser
- Gałąź: work/agent-v1-robot-integration
- HEAD podczas przeglądu: 8cd8402d39297cda1ace3fd1f536287db3d7e6b2
- Ostatni commit: test(perception): cover WindowHub document content reader
- Lokalnie mogą istnieć niezatwierdzone skrypty diagnostyczne/outputy. Nie resetować, nie stashować i nie usuwać ich bez wyraźnej potrzeby.

## Co już jest

### Universal Agent Core

Istnieją już: AgentRequest, AgentRuntime, AgentOrchestrator, AgentPlanner, capability routing, skills, TaskReasoner, OpenAI/NaviMind reasoning, TaskPlanningContext, PerceptionEngine, ScreenScene, ScreenElement, fusion, TargetResolver, RobotGUIExecutor, RobotActionExecutor, EnvironmentRequirement, EnvironmentPreparationLoop, VerificationLoop, replanning i action-failure policies.

### Autonomia

AgentRuntime ma pętlę: observe -> reason -> jeden semantyczny action -> execute -> verify -> ponowna obserwacja. W autonomous wykonywany jest maksymalnie jeden krok na iterację.

### WindowHub

Istnieją już: WindowHubEnvironmentAdapter, WindowHubFocusWindowPreparationHandler, WindowHubVisionProvider, WindowHubUIAutomationProvider, WindowHubDocumentReader, WindowHubFormReader, WindowHub offer knowledge, WHWindowSkill, offer workflow/session services oraz realne testy dry-run/safety-chain.

## Potwierdzone fakty WindowHub

1. HWND jest dynamiczny. Przykład historyczny: 3280880; po ponownym utworzeniu WindowHub: 1709872. Nie kodować stałego HWND.
2. Top-level WindowHub jest rozpoznawany po tytule zaczynającym się od Okna - i wybierany jest największy poprawny window.
3. Aktualny dokument jest osobnym MDI child klasy w rodzaju Afx:006E0000:b:....
4. Pozycje dokumentu są w custom/owner-drawn DataTable5. Standardowe UIA grid semantics nie wystarczają.
5. m_rtb jest RichTextBox/UIA Document i window_text()/get_value() zwraca techniczny opis wybranej pozycji: produkt, wagę, Uw, szyby, okucia, klamkę, słupki, łączniki itd.
6. WindowHubDocumentReader już czyta m_rtb tylko z potwierdzonego aktywnego dokumentu i jest read-only.
7. WindowHubFormReader obsługuje semantyczne pola Edit/ComboBox.
8. Dolne zakładki Notatka, Technologia, Handel wewn., Handel zewn., Zamówienie wewn., Zamówienie zewn. są pomocnicze handlowo i nie zmieniają technicznej konfiguracji/pricingu; nie są obecnie priorytetem.
9. Istniejące dane badawcze zawierają region buildera WindowHub, m.in. builder_01_empty.png, builder_02_frame.png, builder_03_frame_sash.png, builder_04_frame_sash_glass.png i builder_05_right_panel.png.

## Co już udowodniliśmy w percepcji

- Prawdziwy WindowHub jest przechwytywany przez MSSScreenshotEngine; screenshot około 1936x1168.
- CanvasAnalyzer potrafi znaleźć obszar centralnego rysunku, ale jego rozmiar/położenie może się zmieniać.
- Obecny ConstructionAnalyzer przeszukuje cały screenshot przez HSV + connected components + klastrowanie z CLUSTER_GAP=16.
- Udowodniono błąd: 33 komponenty z tabeli i konstrukcji mogą zostać sklejone w jeden ogromny klaster bbox=90,81 1583x751, który odpada na saturation < 0.08.
- W poprzednim teście komponenty odpowiadające konstrukcji przechodziły root ownership z rootem WindowHub. Problemem jest obecnie izolacja obszaru konstrukcji, nie brak danych.
- WindowFromPoint zwraca okno faktycznie znajdujące się na pierwszym planie. Jeżeli Firefox zasłania WindowHub, punkty z obrazu WindowHub mogą zwrócić MozillaWindowClass. Diagnostyka tego typu musi najpierw uzyskać fokus WindowHub.

## Ważna korekta metodologii

Nie budować percepcji WindowHub jako samego CV od zera. Najlepszy kierunek to:

WindowHub root -> aktywny MDI document -> UIA semantics/document/form readers -> automatycznie ustalony obszar buildera -> CV/vision tylko dla owner-drawn buildera -> semanticzne targety -> controlled execution -> verification.

Nie używać hard-coded współrzędnych jako wiedzy agenta. Współrzędna może być wyłącznie wynikiem aktualnej percepcji.

## Obecna luka funkcjonalna

Największy brak dla WindowHub to semantyczne rozumienie i sterowanie centralnym builderem:

- stabilne ustalenie builder surface w aktualnym MDI child
- rozpoznawanie rama / skrzydło / szyba / okucie / słupek / łącznik
- kliknięcie wykrytego elementu przez bieżącą percepcję
- odczyt właściwości/panelu po prawej stronie po wyborze elementu
- osobny workflow dla okuć, gdzie otwiera się tabela wyboru
- powiązanie odczytanych danych z istniejącym ConstructionSchema/ConstructionProject/OfferWorkflow

## Istniejąca logika biznesowa

Nie budować jej od nowa. Repo ma m.in. ConstructionSchema, ConstructionSchemaFactoryV2, ConstructionResolver, ConstructionProject, ConstructionOffer, AgentConstructionCompiler, OfferAgentService, OfferWorkflowService oraz WindowHub knowledge/catalog/rules.

## Istniejące bezpieczeństwo

- DRY_RUN jest domyślny; LIVE tylko przez WH_REAL_WINDOWHUB=1.
- Model ma zwracać wyłącznie działania semantyczne. Nie wolno przekazywać modelowi współrzędnych, HWND, AutomationId, runtime id ani executor internals jako targetów.
- Clickability jest oddzielona od samej percepcji i ma być potwierdzana przez capability/evidence/fusion zgodnie z guardami.
- Każdy realny customer case ma stać się regression testem.

## Najbliższy plan

1. Nie wykonywać kolejnych losowych testów współrzędnych.
2. Przed diagnostyką WindowFromPoint zawsze zapewnić fokus WindowHub przez istniejący WindowHubFocusWindowPreparationHandler.
3. Zidentyfikować stabilny native/UIA kontener buildera w aktualnym MDI child.
4. Ograniczyć ConstructionAnalyzer do builder surface zamiast całego screenshotu.
5. Wystawić builder perception jako dane semantyczne do ScreenScene/runtime, a nie zostawiać tylko w legacy context.construction.
6. Dodać wybór komponentu i odczyt właściwości po prawej stronie.
7. Następnie spiąć z istniejącym ConstructionSchema/OfferWorkflow i zrobić pełny smoke A–Z.

## Cel szerszy

Po ustabilizowaniu WindowHub agent ma rozszerzać się na inne aplikacje przez adaptery/providers/skills, a nie przez kopiowanie całego runtime. Podstawy COMPUTER_USE, Excel, Word, reasoning, semantic perception, controlled execution i verification już istnieją.

## Zasada na kolejne czaty

Przed dalszą pracą sprawdzić aktualny HEAD tej gałęzi oraz ten plik i kontynuować od sekcji Najbliższy plan. Nie odtwarzać całej historii testów, jeżeli kod się nie zmienił.

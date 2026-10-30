# Ewaluacja zachowania agenta z MCP TypeSafe Jev 0.2.0

Ten raport opisuje historyczny pomiar bazowy sprzed zmian instrukcji. Zastosowane później poprawki i ich osobne pomiary opisano w [GUIDANCE_UPDATE.md](GUIDANCE_UPDATE.md); poniższe wyniki bazowe pozostają zachowane.

Pomiar bazowy wykonano bez zmiany instrukcji MCP. Istniejący diff użytkownika zachowano; nowe pliki znajdują się wyłącznie w `evals/`.

## Konfiguracja i zakres

- Agent: `gpt-6-luna`, reasoning `low`, Codex `0.165.0-alpha.1.2` dołączony do aplikacji.
- Jev: rzeczywisty stdio MCP, domyślny `jev-latest`; odpowiedzi zapisują rozwiązaną wersję modelu.
- Pilotaż: 6 scenariuszy × 4 warianty × 2 powtórzenia = **48 świeżych kontekstów**.
- Pełny zestaw: 10 tekstowych, 10 obrazowych, 5 niejednoznacznych i 5 deterministycznych; 4 warianty × 2 powtórzenia = **240 świeżych kontekstów**.
- Próby kontrolowane: 3 scenariusze × 3 warianty z Jev × 2 powtórzenia = **18 kontekstów**, oddzielnie od jakości live Jev.
- Kolejność losowana z seed `20261029`; generowanie modelu nie ma ustawianego seeda. Równoległość pilotażu i pełnego pomiaru: 2; prób kontrolowanych: 1.
- Progi zapisane przed pomiarem: **IoU ≥ 0,50**, błąd rubryki ≤ 0,50, niska confidence < 0,60. Dokładne obliczenie ma tolerancję 0.

Każda próba otrzymywała zwykłe zadanie, syntetyczne dane i te same obrazy. Zadanie nie nakazywało użycia Jev. Warianty: opisy narzędzi i instrukcja inicjalizacji MCP; ten sam zestaw z wcześniejszym odczytem `guide`; z odczytem `skill`; bez narzędzi i zasobów Jev. Odczyt zasobu przez runner jest jawną interwencją, nie pomiarem spontanicznego odkrycia zasobu.

## Agent → MCP oraz wynik końcowy

Wszystkie 240 prób ukończyły się bez błędów środowiska. Pilotaż osiągnął 48/48 poprawnych wyników końcowych, ale audyt wykazał w nim również błędne pytania i wywołania. Sam sukces końcowego zadania nie oznacza poprawnego użycia MCP.

| Wariant | Surowa ocena ścisła | Trafność po korekcie formatu | Wywołania oceny Jev | Mediana czasu próby |
|---|---:|---:|---:|---:|
| Opisy | 57/60 | 59/60 | 51 | 4 424 ms |
| Odczyt guide | 57/60 | 57/60 | 48 | 4 397 ms |
| Odczyt skill | 58/60 | 60/60 | 49 | 4 667 ms |
| Bez Jev | 57/60 | 60/60 | 0 | 2 597 ms |

Pierwotny grader błędnie odrzucał numer `3` zamiast tekstu `"3"`, null przy poprawnej abstencji oraz nazwę koloru `Yellow` zamiast `yellow`. Siedem takich rozbieżności formatu opisano w [zasadach korekty](ADJUDICATION.md). Surowy manifest, odpowiedzi i oceny pozostają niezmienione; [adjudicated.jsonl](results/baseline-full-current/adjudicated.jsonl) zawiera obie oceny. Nie zmieniono odpowiedzi referencyjnych ani progów IoU, rubryki i confidence.

Po tej jawnej korekcie wynik zadania jest poprawny w **236/240** próbach. To wynik tego małego zestawu, nie szacunek skuteczności produkcyjnej. Nie ma podstaw, by przypisywać różnicom między wariantami znaczenie statystyczne ani twierdzić, że odczyt guide pogarsza agenta ogólnie.

Nie było wywołań Jev w zadaniach oznaczonych jako zbędne ani pominięć wymaganej oceny zewnętrznej w wariantach z Jev. Wariant bez Jev stanowi kontrolę trafności odpowiedzi; nie może spełnić wymogu zewnętrznej oceny, więc zgodność z tym wymogiem jest w nim nieporównywalna.

Audyt osobnego agenta (`gpt-6.1-sol`, reasoning `high`) objął wszystkie **148/148** wywołań oceny: **147/148** spełniało opublikowany JSON Schema, a **134/148** także warunki referencji i dostępności dowodów. Jakość kryteriów: **128 poprawnych, 18 z problemem, 2 niepewne**. Dziewięć wywołań faktycznie się nie powiodło: brak `instructions` raz i niepoprawne referencje obrazów osiem razy. Dalszych pięć pytało o obraz bez obrazu lub wystarczającego opisu; cztery miały stronnicze kryteria. Walidacja struktury, poprawność danych i ocena kryteriów opisują różne wymiary tych samych wywołań; nie sumujemy dziewięciu nieudanych żądań i osiemnastu problemów kryteriów. Ocena semantyczna jest audytem modelowym, bez niezależnego arbitrażu człowieka. [Audyt per wywołanie](results/baseline-full-current/criteria-audit.json) i [podsumowanie](results/baseline-full-current/audit-summary.json) zawierają uzasadnienia oraz przypisanie przyczyn.

| Wariant | Nieudane wywołania Jev | Próby z niską confidence | Użycie compute w zadaniach deterministycznych |
|---|---:|---:|---:|
| Opisy | 6 | 3 | 8/10 |
| Guide | 3 | 7 | 9/10 |
| Skill | 0 | 4 | 8/10 |
| Bez Jev | 0 | 0 | 0/10 |

Łącznie `compute` wystąpiło w 25/40 zadań deterministycznych; pozostałe rozwiązano bez wykonania kodu. Brak wywołań Jev potwierdza właściwe pominięcie silnika semantycznego, ale nie dowodzi zawsze właściwego wyboru zwykłego narzędzia. Wariant bez Jev dodatkowo raz bez potrzeby próbował `compute` przy rozpoznawaniu obrazu, dostał błąd argumentu i odpowiedział poprawnie.

W dwóch powtórzeniach zmieniła się odpowiedź, box, abstencja lub liczba wywołań w **20/120** par scenariusz–wariant. Sama trafność po korekcie formatu zmieniła się w **2/120** parach; oba błędy porównania obrazów w guide powtórzyły się. Pilotaż miał zmiany w 2/24 parach przy niezmienionej trafności, a próby kontrolowane w 2/9 parach, również bez zmiany trafności. Dokładne pary są wymienione w raportach przebiegów. Zmiana współrzędnych nie oznacza automatycznie niezaliczenia IoU.

### Zużycie w pełnym pomiarze

| Wariant | Tokeny wejściowe agenta | W tym cache | Tokeny wyjściowe agenta | Tokeny Jev wejście / wyjście |
|---|---:|---:|---:|---:|
| Opisy | 1 482 049 | 1 233 536 | 9 025 | 22 042 / 1 408 |
| Guide | 1 505 601 | 1 241 856 | 8 877 | 22 746 / 1 390 |
| Skill | 1 696 831 | 1 417 600 | 9 444 | 32 786 / 1 624 |
| Bez Jev | 671 540 | 391 424 | 2 876 | 0 / 0 |

Agent łącznie: **5 356 021 input, 30 222 output**, w tym **4 284 416 cached input**. Reasoning output raportowany przez runtime wyniósł 0, pomimo konfiguracji `low`; nie dopisujemy niedostępnych tokenów. Są to sumy końcowych liczników każdego kontekstu, obejmujące powtórne wejścia przy rundach narzędzi; cache jest częścią input, nie dodatkowym kosztem. Nie przeliczamy tego na pieniądze. Dla wszystkich 240 prób dostępne było usage. Jev w udanych wywołaniach agenta: **77 574 input / 4 422 output**, bez szacowania zużycia nieudanych żądań. Oddzielny tor kanoniczny zużył **33 752 / 1 626** tokenów Jev. Pilotaż i próby kontrolowane nie są doliczone do tej tabeli.

## Cztery rzeczywiste błędy zadania i ich pochodzenie

1. **Porównanie liczby niebieskich obiektów, guide, oba powtórzenia.** Agent nie przekazał obrazów do Jev. W jednym powtórzeniu Jev wskazał B z confidence 0,09, a agent zapisał A, choć jego uzasadnienie korygowało wybór na B. Drugie wywołanie zwróciło remis przy confidence 0,06. To błędy danych wejściowych i decyzji końcowej agenta; nie dowód błędu modelu Jev oglądającego poprawnie przesłane obrazy.
2. **Liczenie znaków, opisy i guide, powtórzenie 0.** Agent podał do `compute` cały tekst `Input string: 'TypeSafe Jev'` zamiast samego `TypeSafe Jev`. Narzędzie poprawnie policzyło 25 dla otrzymanego argumentu, zamiast oczekiwanych 11. To błąd ekstrakcji argumentu przez agenta, poza transportem i modelem Jev.

## Jev na niezależnych, stałych pytaniach

W pełnym zestawie wykonano **50/50** udanych wywołań dla 25 przypadków semantycznych/obrazowych/niejednoznacznych, każde dwukrotnie. Wszystkie 50 odpowiedzi spełniło zapisany warunek jakości. Pięć zadań deterministycznych celowo nie miało wywołania Jev. Pytania kanoniczne zostały zapisane przed wykonaniem i nie pochodzą od badanego agenta.

Rozwiązany model Jev: **`jev-1.14.0`**. W 10 kanonicznych lokalizacjach IoU wyniosło **0,848–0,941**, średnio **0,900**. W torze pytań agenta poprawnie zasilone wywołania lokalizacji przeszły **24/24**, a końcowe boxy agenta **40/40** — również przy bezpośrednim rozpoznawaniu obrazu bez Jev.

Lokalizacja obecnych obiektów obejmowała pięć ręcznie zapisanych boxów, po dwa powtórzenia. Oceniano rzeczywiste IoU, nie sam zakres współrzędnych. Adnotacje są niezależnymi literalnymi współrzędnymi w fixture, sprawdzonymi wzrokowo względem obrazów; nie pochodzą z odpowiedzi Jev. Nie było osobnego panelu ludzkich adnotatorów.

Osobna próba bezpośredniego `jev_box` dla **nieobecnej różowej gwiazdy** zwróciła box w obu powtórzeniach, z confidence **0,06 i 0,07**. To poprawny transport i niepoprawna lokalizacja. Kontrakt box nie ma jawnego stanu „brak obiektu”; osobne pytanie o obecność prawidłowo wskazało brak. [Surowe próby nieobecnego obiektu](results/baseline-full-current/absent-box-diagnostics.jsonl) nie są wliczone jako poprawne lokalizacje.

## Reakcja na niepewność i błędy

[Próby kontrolowane](results/robustness-current/report.md) zakończyły się **18/18** poprawnych abstencji; wszystkie 18 obejmowały rzeczywiste wywołanie narzędzia przez agenta. Sześć otrzymało niską confidence, sześć syntetyczny błąd HTTP 529, a sześć pewną odpowiedź sprzeczną z brakiem dowodów. Odpowiedzi były podstawiane przez runner w kształcie wybranego prymitywu. To dowód zachowania procesu w kontrolowanych warunkach, nie jakości live Jev.

W naturalnym zadaniu obrazowym niska confidence nie zapobiegła błędnej decyzji agenta. Poprawny wynik prób kontrolowanych nie daje więc gwarancji działania na innych zadaniach. Nie wyciągamy wniosków o kalibracji confidence z tej próbki.

## Konkretne propozycje instrukcji MCP

Nie wdrożono ich do kodu produkcyjnego. Pomiar bazowy i jego zasoby pozostają zapisane przed ewentualną zmianą instrukcji.

1. **Dodać do opisów narzędzi obrazowych krótki warunek wejściowy:** „Jeżeli pytanie wymaga oglądania obrazu, przekaż `assets`; sama nazwa pliku, ścieżka lub identyfikator w `state` nie dostarcza obrazu”. Powód: pięć wywołań pytało o zawartość obrazów bez przesłania obrazu lub informacji pozwalających odpowiedzieć.
2. **Pokazać jedno spójne mapowanie, powtarzane przy pojedynczych narzędziach:** `state={"photo":"img_1"}`, `assets={"img_1":{"path":"..."}}`; dopisać „klucz `assets` musi wystąpić w wartości tekstowej żądania; nie myl nazwy pola z referencją”. Powód: osiem błędów referencji `assets.photo` kontra `scene_*` zakończonych HTTP 400. Przy 400 zalecać sprawdzenie referencji i parametrów, zamiast ponawiania po zmianie separatorów ścieżki.
3. **Dodać jawny wzorzec braku danych i obiektu:** użyj `choice` z opcją `unknown/absent` albo pytania o wystarczalność dowodów/obecność; wykorzystaj box dopiero po potwierdzeniu obecności. Wspólny batch obecność + box pozostaje poprawną strategią, jeśli agent odrzuca box przy braku obiektu. `box` sam nie potwierdza istnienia obiektu. Powód: fałszywe boxy przy nieobecnej gwieździe oraz problemy pytań binarnych w pilotażu.
4. **Przy confidence opisać konkretną akcję i kontrolę wyniku:** brak obrazu/dowodów wymaga ich uzyskania lub abstencji; po wyborze sprawdź zgodność końcowego identyfikatora z wybraną opcją. Powód: porównanie obrazów przy confidence 0,06–0,09 i finalne A przy uzasadnieniu B. Wysoka confidence nie uzupełnia brakujących danych.
5. **Dodać krótkie kompletne przykłady `jev_evaluate` i przypomnienie wymaganego `instructions`.** Powód: jedno wywołanie pominęło wymagane instrukcje. Sukces JSON Schema nie powinien być przedstawiany jako gwarancja poprawnego pytania.
6. **Przypomnieć o neutralnych kryteriach:** opisy opcji mają definiować kategorie, a nie uprzednio deklarować, która jest prawdziwa. Powód: cztery wywołania miały kryteria niosące preferowaną odpowiedź. Nie dotyczy to poprawnego przekazania definicji rubryki lub wszystkich równorzędnych kandydatów.

Propozycje trzeba sprawdzić nowym pomiarem A/B na zapisanym zestawie oraz dodatkowym, niewykorzystywanym wcześniej zestawie. Obecny pomiar nie dowodzi jeszcze, że konkretne nowe brzmienie poprawi wynik.

## Ograniczenia i odtwarzanie

- Wcześniejsze przebiegi npm CLI 0.146 (`baseline-pilot`, `baseline-pilot-terra`) miały błędy pojemności/limitu; nie są łączone z aktualnym pomiarem. Starszy CLI odrzucał GPT-6; aktualny runtime aplikacji go obsłużył. Blokadę gniazd piaskownicy sprawdzono osobno i wykonania live wymagały eskalacji sieci.
- Zasoby guide/skill wczytywał runner przed zadaniem. Wszystkie warianty z Jev mogły też czytać je samodzielnie. Nie jest to badanie odkrywalności narzędzi w natywnym interfejsie MCP Codex.
- Świeży, efemeryczny kontekst ma neutralną bazową instrukcję, wspólny schemat odpowiedzi i narzędzie `compute`. Nie dostaje tej rozmowy, etalonów ani plików repozytorium. Surowe zdarzenia bieżącego pomiaru nie wykazały wykonywania poleceń ani odczytów repozytorium.
- Dwa powtórzenia małych, syntetycznych zadań pokazują zaobserwowaną niestabilność, nie rozkład błędów w produkcji. Obrazy mają proste figury; trafność tego zestawu nie rozstrzyga wcześniejszych problemów innych syntetycznych obrazów.
- Zmiany techniczne runnera po rozpoczęciu pomiaru obejmują korekty formatu i nieużywanych w próbach live ścieżek replay/wznowienia. Surowe oceny bazowe zachowano; hashe w metadanych dokumentują wersję startową. Nie wolno wznawiać tych historycznych katalogów inną wersją runnera; nowy pomiar wymaga nowego katalogu.

Dokładne komendy, format artefaktów i zasady wznawiania: [README](README.md). Surowe wyniki: [pełny baseline](results/baseline-full-current/report.md), [pilotaż](results/baseline-pilot-current/report.md), [próby kontrolowane](results/robustness-current/report.md).

Końcowa weryfikacja: **10/10 kontroli runnera**; jedyny końcowy przebieg suity aplikacji: **52 passed, 7 skipped**. Siedem istniejących testów live nie zostało ponownie uruchomionych przez pytest, ponieważ klucz ustawiano tylko w procesach MCP. Rzeczywiste pomiary live opisano wyżej. Przegląd kodu nie pozostawił uwag P1/P2. Katalogi tymczasowe są usuwane po weryfikacji.

```powershell
.venv/Scripts/python.exe -m evals.selfcheck
.venv/Scripts/python.exe -m evals.run --phase full --model gpt-6-luna --repeats 2 --concurrency 2 --output evals/results/new-full
```

# Zmiana instrukcji MCP — 2026-10-30

Zastosowano poprawki wynikające z [zachowanego baseline](REPORT.md). Dotyczą opisów narzędzi, instrukcji inicjalizacji i zasobów `jev://guide` / `jev://skill`. Sygnatury i schematy wszystkich sześciu narzędzi pozostały identyczne z baseline; nie zmieniono transportu ani progów oceny.

## Zastosowane reguły

- Pytanie o piksele wymaga faktycznego obrazu w `assets`. Nazwa lub ścieżka w `state` nie przesyła obrazu. Porównanie obrazów wymaga wszystkich odpowiednich obrazów; jawny opis tekstowy jest oceniany jako opis.
- Jedno spójne mapowanie: `state={"photo":"img_1"}`, `assets={"img_1":{"path":"/absolute/photo.png"}}`. Referencja musi wystąpić w wartości tekstowej, nie wyłącznie w kluczu. Przy 400 należy sprawdzić argumenty i referencje przed ponowieniem.
- Każdy wpis batch wymaga `type` i niepustego `instructions`; narzędzia pojedyncze określają typ nazwą. Kryteria mają definiować neutralne alternatywy lub poziomy rubryki. Brak danych wymaga `unknown` albo osobnego pytania o wystarczalność dowodów; `false` nie musi dowodzić przeciwieństwa.
- Box nie potwierdza istnienia obiektu. Obecność i box można policzyć wspólnie, ale box należy odrzucić przy braku lub nierozstrzygniętej obecności.
- Niska confidence wymaga uzupełnienia danych, niezależnego sprawdzenia lub abstencji. Wysoka confidence nie zastępuje dowodów. Identyfikator końcowy musi odpowiadać faktycznie wspieranej decyzji; odstąpienie od odpowiedzi Jev wymaga uzasadnienia.
- Dokładne liczenie danych tekstowych/strukturalnych, arytmetyka, parsowanie i lookup pozostają zadaniami kodu. To nie jest zakaz wizualnego rozpoznawania liczby obiektów przez Jev.

Wspólne reguły i dwa kompletne przykłady żądań znajdują się w `src/typesafe_jev_mcp/routes/mcp/guidance.py`; korzystają z nich opisy narzędzi i oba zasoby. Skill jest oznaczony jako adaptacja MCP upstreamowego materiału TypeSafe.

Koszt tej zmiany to około 3,5 tys. dodatkowych znaków we wszystkich opisach narzędzi łącznie oraz około 0,9 tys. w instrukcji inicjalizacji. Guide i skill są nadal zasobami ładowanymi na żądanie. To świadomy koszt umieszczenia najważniejszych zasad obrazów bezpośrednio przy narzędziach; nie jest deklaracją zerowego narzutu tokenów.

## Ponowny pomiar

Wybrano sześć istniejących przypadków: rozpoznanie koła, porównanie liczby niebieskich obiektów, lokalizacja koła, brak obiektu, sprzeczni recenzenci oraz ocena według rubryki. Zachowano model `gpt-6-luna`, reasoning `low`, cztery warianty i dwa powtórzenia. Wykonano 48 świeżych kontekstów oraz osobny zapis stałych pytań Jev. Baseline porównano po jawnych korektach formatu opisanych w `ADJUDICATION.md`.

| Wariant | Trafność przed | Trafność po | Wywołania Jev przed / po | Nieudane wywołania przed / po |
|---|---:|---:|---:|---:|
| Opisy | 12/12 | 12/12 | 13 / 12 | 2 / 0 |
| Guide | 10/12 | 11/12 | 12 / 12 | 1 / 0 |
| Skill | 12/12 | 11/12 | 12 / 12 | 0 / 0 |
| Bez Jev | 12/12 | 10/12 | 0 / 0 | 0 / 0 |

Wszystkie **36/36** wywołań Jev w nowym pilotażu zakończyły się bez błędu. W tej próbce wyeliminowano nieudane wywołania MCP; nie wykazano poprawy trafności końcowej. Warianty z Jev osiągnęły łącznie **34/36** poprawnych odpowiedzi zarówno przed, jak i po zmianie. Wynik całego podzbioru zmienił się z **46/48 na 44/48**, z dwoma dodatkowymi błędami w niezmienianym wariancie bez Jev. Dwa powtórzenia nie wystarczają do wniosku o przyczynowym wpływie instrukcji na trafność.

Audyt osobnego agenta (`gpt-6.1-sol`, reasoning `high`) ocenił poprawność argumentów, referencji i dostępności dowodów: **29/37** wywołań w odpowiednim podzbiorze baseline, **36/36** w nowym pilotażu i **5/5** w finalnym sprawdzeniu. Wszystkie nowe kryteria oceniono jako poprawne. [Audyt pilotażu](results/guidance-update-pilot/criteria-audit.json) i [audyt finalnego sprawdzenia](results/guidance-update-final-check/criteria-audit.json) zawierają oceny per wywołanie. To audyt modelowy, bez arbitrażu człowieka. Obrazy przed i po mają identyczne hashe, a zadania i etalony nie zostały zmienione w celu poprawienia wyniku.

Po przeglądzie doprecyzowano jeszcze zakres słowa „counting” i oznaczenie pochodzenia skilla. Finalną treść sprawdzono w ośmiu dodatkowych kontekstach dla tego samego przypadku porównania obrazów. Wynik zadania: opisy **1/2**, guide **2/2**, skill **1/2**, bez Jev **0/2**. Agent wykonał pięć wywołań Jev, wszystkie poprawne i zakończone wyborem B z confidence 0,97–1,00. Jedna błędna odpowiedź w skill powstała bez wywołania Jev, co było dopuszczalne dla tego opcjonalnego zadania.

## Pozostałe ograniczenie agenta

W pilotażu guide i skill po jednym razie zwróciły końcowe A, mimo poprawnego B od Jev i uzasadnienia wskazującego B. W finalnym sprawdzeniu analogiczny błąd wystąpił raz w wariancie opisy. Nie był to błąd przesłania obrazu ani odpowiedzi Jev. Dodane przypomnienie o spójności nie gwarantuje poprawności końcowego pola generowanego przez agenta. Dalsze zabezpieczenie wymagałoby sprawdzania wyniku w harnessie; nie dodawano reguły wymuszającej konkretne A/B w domenowo niezależnym MCP.

Próby są regresją na znanych scenariuszach. Nie są niezależnym zbiorem walidacyjnym ani dowodem ogólnej poprawy. Progi IoU, rubryki i confidence pozostały bez zmian. Baseline i wszystkie nowe odpowiedzi zachowano oddzielnie.

## Odtworzenie

Z katalogu repozytorium:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_mcp_guidance.py -q -p no:cacheprovider --basetemp=.pytest-tmp
.venv/Scripts/python.exe -m evals.run --phase pilot --cases image_color_shape_match,image_compare_blue_count,image_locate_blue_circle,ambiguous_absent_object,ambiguous_conflicting_reviewers,text_rubric_priority --model gpt-6-luna --effort low --repeats 2 --concurrency 2 --output evals/results/new-guidance-pilot
```

Pierwszy przebieg: [raport i raw traces](results/guidance-update-pilot/report.md). Finalne doprecyzowanie: [raport](results/guidance-update-final-check/report.md). Przegląd kodu nie wykazał P1/P2. Sześć celowanych testów sprawdza kompletność i zgodność opublikowanych przykładów z modelami aplikacji.

Jedyny końcowy przebieg pełnej suity aplikacji po tych zmianach: **58 passed, 7 skipped**. Pominięto istniejące testy live pytest; rzeczywiste wywołania Jev i świeże konteksty agenta opisano oddzielnie powyżej. Klucz otrzymywały wyłącznie procesy MCP, bez ustawiania go w środowisku powłoki ani zapisu w wynikach.

Nowa instancja MCP wczytuje zaktualizowane instrukcje automatycznie z instalacji editable. Klient utrzymujący istniejący proces i katalog narzędzi musi ponownie połączyć się z MCP, aby pobrać nowe opisy.

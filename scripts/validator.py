import sys
from pathlib import Path

class Problem:
    n: int
    # Słownik {task_id: (p, r, d)} dla łatwego dostępu
    tasks_data: dict[int, tuple[int, int, int]]

    def __init__(self, n, tasks_list):
        self.n = int(n)
        self.tasks_data = {}
        for i, (p, r, d) in enumerate(tasks_list):
            # Zadania są numerowane od 1
            task_id = i + 1
            self.tasks_data[task_id] = (int(p), int(r), int(d))

    def string(self):
        s = f"{self.n}\n"
        for task_id in range(1, self.n + 1):
            p, r, d = self.tasks_data[task_id]
            s += f"{p} {r} {d}\n"
        return s

class Solution:
    claimed_sum_uj: int
    # Lista 5 list, każda zawiera sekwencję ID zadań
    machines: list[list[int]]

    def __init__(self, claimed_sum_uj, machines):
        self.claimed_sum_uj = int(claimed_sum_uj)
        self.machines = [[int(task) for task in m_schedule] for m_schedule in machines]

    def string(self):
        s = f"{self.claimed_sum_uj}\n"
        for m_schedule in self.machines:
            s += " ".join(map(str, m_schedule)) + "\n"
        return s

def read_problem(path):
    try:
        lines = [line.split() for line in open(path).read().splitlines()]
        if not lines:
            raise ValueError("Plik instancji jest pusty.")

        n = int(lines[0][0])
        tasks_list = []

        if len(lines) < n + 1:
            raise ValueError(f"Plik instancji uszkodzony: oczekiwano {n} zadań, znaleziono {len(lines) - 1}")

        for i in range(1, n + 1):
            if len(lines[i]) < 3:
                raise ValueError(f"Niekompletne dane dla zadania {i} w pliku instancji.")
            p, r, d = lines[i]
            tasks_list.append((p, r, d))

        return Problem(n, tasks_list)

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY podczas czytania pliku instancji: {e}", file=sys.stderr)
        sys.exit(3)


def read_solution(path):
    try:
        # Czytamy wszystkie linie, rstrip() usuwa tylko końcowe białe znaki
        lines = [ln.rstrip() for ln in open(path).read().splitlines()]

        if not lines:
            raise ValueError("Plik rozwiązania jest pusty.")

        # Linia 1: Wartość kryterium
        claimed_sum_uj = int(lines[0].split()[0])

        # Linie 2-6: 5 stanowisk
        if len(lines) < 6:
            raise ValueError(
                f"Plik rozwiązania uszkodzony: Oczekiwano 6 linii (1 SumUj + 5 maszyn), znaleziono {len(lines)}")

        machine_schedules = []
        # Wczytujemy dokładnie 5 linii (o indeksach 1, 2, 3, 4, 5)
        for i in range(1, 6):
            # .split() poprawnie obsłuży pustą linię (da pustą listę)
            machine_schedules.append(lines[i].split())

        return Solution(claimed_sum_uj, machine_schedules)

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY podczas czytania pliku rozwiązania: {e}", file=sys.stderr)
        sys.exit(3)


def validate(problem: Problem, solution: Solution, get_t=True):
    n = problem.n
    task_data = problem.tasks_data
    claimed_sum_uj = solution.claimed_sum_uj
    machines = solution.machines

    errors = ""

    # 1. Weryfikacja poprawności przypisania zadań
    seen_tasks = set()
    total_tasks_in_solution = 0

    for i, schedule in enumerate(machines):
        machine_id = i + 1
        for task_id in schedule:
            total_tasks_in_solution += 1

            # Sprawdzenie, czy ID zadania jest w poprawnym zakresie
            if not (1 <= task_id <= n):
                errors += f"BŁĄD: Stanowisko {machine_id}: Niepoprawne ID zadania: {task_id}\n"

            # Sprawdzenie duplikatów
            elif task_id in seen_tasks:
                errors += f"BŁĄD: Zadanie {task_id} występuje wielokrotnie (zduplikowane)\n"

            seen_tasks.add(task_id)

    # Sprawdzenie, czy wszystkie zadania od 1 do n zostały użyte
    expected_tasks = set(range(1, n + 1))
    if expected_tasks != seen_tasks:
        missing = expected_tasks - seen_tasks
        if missing:
            errors += f"BŁĄD: Brakujące zadania w rozwiązaniu: {sorted(list(missing))}\n"

        # Dodatkowe zadania (np. ID > n) są już łapane przez pierwszą pętlę

    # Jeśli harmonogram jest fundamentalnie błędny, nie ma sensu liczyć kryterium
    if errors != "":
        return errors if not get_t else (int(2e63) - 1)

    # 2. Symulacja harmonogramu i obliczenie prawdziwego SumUj
    true_sum_uj = 0

    for i, schedule in enumerate(machines):
        machine_free_time = 0  # Czas, kiedy i-te stanowisko będzie wolne

        for task_id in schedule:
            try:
                p, r, d = task_data[task_id]
            except KeyError:
                # Ten błąd powinien być już wyłapany wyżej, ale dla bezpieczeństwa
                errors += f"BŁĄD KRYTYCZNY: Nie znaleziono danych dla zadania {task_id}\n"
                continue

            # Obliczenie czasu startu: zadanie nie może zacząć się ani przed
            # czasem gotowości (r), ani zanim maszyna się zwolni.
            start_time = max(r, machine_free_time)

            # Czas zakończenia
            completion_time = start_time + p

            # Aktualizacja czasu zwolnienia się stanowiska
            machine_free_time = completion_time

            # Sprawdzenie spóźnienia
            if completion_time > d:
                true_sum_uj += 1

    # 3. Porównanie wyników
    if claimed_sum_uj != true_sum_uj:
        errors += f"BŁĄD: Wartość kryterium niezgodna. W pliku: {claimed_sum_uj}, Obliczono: {true_sum_uj}\n"

    # Zwracamy obliczoną wartość (jeśli get_t=True) lub błędy
    if get_t:
        # Zwróć prawdziwą wartość celu, jeśli nie ma błędów,
        # w przeciwnym razie bardzo dużą liczbę jako karę
        return true_sum_uj if errors == "" else (int(2e63) - 1)

    return errors


class ValidationError(Exception):
    pass

def main():
    if len(sys.argv) != 3:
        print("Użycie: python3 validator.py <plik_instancji> <plik_rozwiazania>", file=sys.stderr)
        sys.exit(2)

    inst_path = Path(sys.argv[1])
    sol_path = Path(sys.argv[2])

    try:
        problem = read_problem(inst_path)
        solution = read_solution(sol_path)

        # Sprawdzamy błędy
        errors = validate(problem, solution, get_t=False)
        if errors != "":
            # `errors` ma już "BŁĄD:" w sobie
            raise ValidationError(errors)

        # Jeśli nie ma błędów, wywołujemy ponownie, by dostać prawdziwą wartość
        # (Dobry walidator drukuje to, co sam policzył, a nie to, co przeczytał)
        true_objective_value = validate(problem, solution, get_t=True)

        # Drukujemy PRAWIDŁOWĄ, OBLICZONĄ wartość kryterium
        print(true_objective_value)
        sys.exit(0)  # Sukces

    except ValidationError as e:
        # Drukujemy zebrane błędy
        print(f"{e}", file=sys.stderr)
        sys.exit(1)  # Błąd walidacji

    except Exception as e:
        # Inne błędy (np. brak pliku, błąd konwersji int)
        print(f"NIESPODZIEWANY BŁĄD: {e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(3)  # Błąd krytyczny


if __name__ == "__main__":
    main()
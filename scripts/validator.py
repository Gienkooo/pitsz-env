import sys
from pathlib import Path

class Problem:
    n: int
    s: int
    b: int
    T: list[tuple[int,int]]
    def __init__(self, n, s, b, T):
        self.n = int(n)
        self.s = int(s)
        self.b = int(b)
        self.T = [(int(p), int(r)) for [p, r] in T]
    def string(self):
        s = f"{self.n} {self.s} {self.b}\n"
        for p, r in self.T: s += f"{p} {r}\n"
        return s

class Solution:
    cmax: int
    bcnt: int
    B: list[list[int]]
    def __init__(self, cmax, bcnt, B):
        self.cmax = int(cmax)
        self.bcnt= int(bcnt)
        self.B = [[int(task) for task in batch] for batch in B]
    def string(self):
        s = f"{self.cmax}\n{self.bcnt}\n"
        for batch in self.B:
            for task in batch: s += f"{task} "
            s += "\n"
        return s

def read_problem(path):
    # Split on any whitespace to avoid empty tokens from trailing spaces
    raw_data = [line.split() for line in open(path).read().splitlines()]
    return Problem(raw_data[0][0], raw_data[0][1], raw_data[0][2], raw_data[1:])

def read_solution(path):
    # Read lines, ignore completely blank ones, and split on any whitespace
    lines = [ln.strip() for ln in open(path).read().splitlines() if ln.strip()]
    if len(lines) < 2:
        # Minimal fallback – no batches
        return Solution('0', '0', [])
    cmax_tok = lines[0].split()[0]
    bcnt_tok = lines[1].split()[0]
    # Parse batches; split() avoids empty tokens from trailing spaces
    batches = []
    for ln in lines[2:]:
        toks = ln.split()
        if toks:
            batches.append([int(t) for t in toks])
    return Solution(cmax_tok, bcnt_tok, batches)

def validate(problem, solution, get_t=True):
    n, s, b, T = problem.n, problem.s, problem.b, problem.T
    p = [prj[0] for prj in T]
    r = [prj[1] for prj in T]
    cmax, bcnt, batches = solution.cmax, solution.bcnt, solution.B
    errors = ""

    if len(batches) != bcnt:
        errors += "ERROR: invalid batch number\n"

    # Check for duplicate or invalid tasks, and that all tasks are present
    seen_tasks = set()
    for batch in batches:
        for task_id in batch:
            if not (1 <= task_id <= n):
                errors += f"ERROR: invalid task {task_id}\n"
            if task_id in seen_tasks:
                errors += f"ERROR: duplicate task {task_id}\n"
            seen_tasks.add(task_id)

    if set(range(1, n + 1)) != seen_tasks:
        errors += "ERROR: not all tasks present\n"

    # Calculate the true Cmax with reload time between batches only
    completion_time = 0
    first_batch = True
    for batch in batches:
        if not batch:
            continue  # Skip empty batches
        if len(batch) > b:
            errors += f"ERROR: invalid batch length for batch {{{" ".join(map(str, batch))}}}\n"

        # Batch duration is max processing time of tasks in the batch
        batch_processing_time = max(p[task_id - 1] for task_id in batch)

        # Batch cannot start sooner than the ready time of all tasks in it
        batch_ready_time = max(r[task_id - 1] for task_id in batch)

        # Previous batch completion + reload time (only applies from second batch onward)
        prev_ready = completion_time + (s if not first_batch else 0)

        # Start time is the later of batch ready time and previous completion + reload
        start_time = max(batch_ready_time, prev_ready)

        # Update completion time
        completion_time = start_time + batch_processing_time
        first_batch = False

    # Cmax is the completion time of the last batch
    true_cmax = completion_time

    if get_t:
        return true_cmax if errors == "" else (int(2e63) - 1)

    if cmax < true_cmax:
        errors += f"ERROR: invalid Cmax: is {cmax}, should be {true_cmax}\n"
        
    return errors


class ValidationError(Exception):
    pass

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 validator.py <instance_file> <solution_file>", file=sys.stderr)
        sys.exit(2)
    inst_path = Path(sys.argv[1])
    sol_path = Path(sys.argv[2])
    try:
        problem = read_problem(inst_path)
        solution = read_solution(sol_path)
        errors = validate(problem, solution, False)
        if errors != "": raise ValidationError(errors)
        print(solution.cmax)
        sys.exit(0)
    except ValidationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
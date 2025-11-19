# file: scripts/benchmark_solvers.py
import subprocess
import os
import csv
import time
from pathlib import Path
import re
from typing import List, Dict, Any

# --- Configuration ---
SOLVERS_DIR = Path('../solvers')
INSTANCES_DIR = Path('../instances/test')
GENERATED_SOLUTIONS_DIR = Path('../solutions/generated')
RESULTS_DIR = Path('../results')
VALIDATOR_SCRIPT = Path('./validator.py')
DEFAULT_TIME_LIMIT = 5

# CSV Output Paths
SUM_UJ_CSV = RESULTS_DIR / 'results_sum_uj.csv'
TIME_CSV = RESULTS_DIR / 'results_time.csv'


class TColor:
    HEADER = '\033[95m';
    OKBLUE = '\033[94m';
    OKGREEN = '\033[92m'
    WARNING = '\033[93m';
    FAIL = '\033[91m';
    ENDC = '\033[0m';
    BOLD = '\033[1m'


def natural_sort_key(path: Path):
    """
    Splits string into text and numbers to sort 'solver_10' after 'solver_2'.
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', path.name)]


def setup_environment():
    print(f"{TColor.HEADER}--- Setting up Environment ---{TColor.ENDC}")
    for d in [RESULTS_DIR, GENERATED_SOLUTIONS_DIR]:
        d.mkdir(exist_ok=True)
    if not SOLVERS_DIR.is_dir() or not INSTANCES_DIR.is_dir():
        print(f"{TColor.FAIL}Error: Missing '{SOLVERS_DIR}' or '{INSTANCES_DIR}'.{TColor.ENDC}")
        exit(1)
    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Directories are ready.\n")


def discover_assets() -> (List[Path], List[Path]):
    print(f"{TColor.HEADER}--- Discovering Assets ---{TColor.ENDC}")

    # Discover and Sort Solvers
    solvers = [f for f in SOLVERS_DIR.iterdir() if f.is_file()]
    solvers.sort(key=natural_sort_key)

    # Discover and Sort Instances
    instances = list(INSTANCES_DIR.glob("in_*.txt"))
    instances.sort(key=natural_sort_key)

    if not solvers:
        print(f"  {TColor.FAIL}No solvers found.{TColor.ENDC}")
        exit(1)

    for solver in solvers:
        if solver.suffix != '.py' and not os.access(solver, os.X_OK):
            solver.chmod(0o755)

    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Solvers: {len(solvers)}")
    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Instances: {len(instances)}\n")

    return solvers, instances


def update_csv_reports(results: Dict[str, Dict[str, Any]], solvers: List[Path], instances: List[Path]):
    """
    Overwrites the CSV files with the current state of the 'results' dictionary.
    Uses semicolon delimiter for Excel compatibility in regions using decimal commas.
    """
    solver_names = [s.name for s in solvers]
    header = ['Instance'] + solver_names

    try:
        # --- Write Sum Uj CSV ---
        with open(SUM_UJ_CSV, 'w', newline='') as f:
            # Changed delimiter to semicolon
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)
            for inst in instances:
                row = [inst.name]
                for solv in solver_names:
                    val = results[inst.name].get(solv, {}).get('result', 'N/A')
                    row.append(val)
                writer.writerow(row)

        # --- Write Time CSV ---
        with open(TIME_CSV, 'w', newline='') as f:
            # Changed delimiter to semicolon
            writer = csv.writer(f, delimiter=';')
            writer.writerow(header)
            for inst in instances:
                row = [inst.name]
                for solv in solver_names:
                    t = results[inst.name].get(solv, {}).get('time')
                    if isinstance(t, float):
                        # LOCALIZATION: Replace dot with comma for Excel
                        time_str = f"{t:.4f}".replace('.', ',')
                    else:
                        time_str = 'N/A'
                    row.append(time_str)
                writer.writerow(row)

    except PermissionError:
        print(
            f"{TColor.WARNING}  [Warning] Could not update CSVs. Close the file in Excel to allow updates.{TColor.ENDC}")


def run_benchmarks(solvers: List[Path], instances: List[Path]):
    print(f"{TColor.HEADER}--- Running Benchmarks ---{TColor.ENDC}")

    # Initialize results structure
    results = {inst.name: {} for inst in instances}

    # Initialize CSVs (overwrite/create)
    update_csv_reports(results, solvers, instances)

    # OUTER LOOP: SOLVERS
    for s_idx, solver_path in enumerate(solvers):
        solver_name = solver_path.name
        print(f"\n{TColor.BOLD}>>> Benchmark Suite for Solver: {solver_name} ({s_idx + 1}/{len(solvers)}){TColor.ENDC}")

        # INNER LOOP: INSTANCES
        for i, instance_path in enumerate(instances):

            # 1. Determine parameters
            try:
                with open(instance_path, 'r') as f:
                    n = int(f.readline().strip().split()[0])
                    time_limit = n // 10
            except (IOError, ValueError, IndexError):
                time_limit = DEFAULT_TIME_LIMIT

            # Visual progress
            print(f"  [{i + 1}/{len(instances)}] {instance_path.name} (Limit: {time_limit}s) ... ", end='', flush=True)

            solution_path = GENERATED_SOLUTIONS_DIR / f"out_{solver_name}_{instance_path.name}"
            command_base = [str(solver_path), str(instance_path), str(solution_path), str(int(time_limit))]
            command = ['python3'] + command_base if solver_path.suffix == '.py' else command_base

            status = ""
            sum_uj = None
            exec_time = 0.0
            start_time = time.monotonic()

            try:
                proc = subprocess.run(
                    command, capture_output=True, text=True, timeout=time_limit * 3
                )
                exec_time = time.monotonic() - start_time

                if proc.returncode != 0:
                    status = "ERROR"
                    print(f"{TColor.FAIL}ERROR{TColor.ENDC}")
                else:
                    verify_proc = subprocess.run(
                        ['python3', str(VALIDATOR_SCRIPT), str(instance_path), str(solution_path)],
                        capture_output=True, text=True
                    )
                    if verify_proc.returncode == 0:
                        status = "OK"
                        sum_uj = int(verify_proc.stdout.strip())
                        print(f"{TColor.OKGREEN}OK (Uj={sum_uj}){TColor.ENDC} {exec_time:.2f}s")
                    else:
                        status = "INVALID"
                        print(f"{TColor.FAIL}INVALID{TColor.ENDC}")

            except subprocess.TimeoutExpired:
                status = "TIMEOUT"
                exec_time = time_limit
                print(f"{TColor.WARNING}TIMEOUT{TColor.ENDC}")
            except Exception as e:
                exec_time = time.monotonic() - start_time
                status = f"CRASH"
                print(f"{TColor.FAIL}CRASH{TColor.ENDC}")

            # Store Data
            results[instance_path.name][solver_name] = {
                'result': sum_uj if status == "OK" else status,
                'time': exec_time if status != "TIMEOUT" else time_limit
            }

            # Update CSV immediately
            update_csv_reports(results, solvers, instances)


def main():
    setup_environment()
    solvers, instances = discover_assets()
    run_benchmarks(solvers, instances)
    print(f"\n{TColor.HEADER}--- Benchmark Complete ---{TColor.ENDC}")
    print(f"Results saved to:\n - {SUM_UJ_CSV}\n - {TIME_CSV}")


if __name__ == "__main__":
    main()
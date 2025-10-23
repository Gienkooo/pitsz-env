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

# (You can keep your TColor class here for nice terminal output)
class TColor:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKGREEN = '\033[92m'
    WARNING = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

def setup_environment():
    print(f"{TColor.HEADER}--- Setting up Environment ---{TColor.ENDC}")
    for d in [RESULTS_DIR, GENERATED_SOLUTIONS_DIR]:
        d.mkdir(exist_ok=True)
    if not SOLVERS_DIR.is_dir() or not INSTANCES_DIR.is_dir():
        print(f"{TColor.FAIL}Error: Missing '{SOLVERS_DIR}' or '{INSTANCES_DIR}'.{TColor.ENDC}")
        exit(1)
    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Directories are ready.\n")

def discover_solvers() -> List[Path]:
    print(f"{TColor.HEADER}--- Discovering Solvers ---{TColor.ENDC}")
    solvers = [f for f in SOLVERS_DIR.iterdir() if f.is_file()]
    if not solvers:
        print(f"  {TColor.FAIL}No solvers found in '{SOLVERS_DIR}'. Aborting.{TColor.ENDC}")
        exit(1)
    for solver in sorted(solvers):
        # Make sure binary files are executable
        if solver.suffix != '.py' and not os.access(solver, os.X_OK):
            solver.chmod(0o755)
        print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Found: {solver.name}")
    print(f"  Total solvers found: {len(solvers)}\n")
    return sorted(solvers)

def run_benchmarks(solvers: List[Path]) -> Dict[str, Dict[str, Any]]:
    print(f"{TColor.HEADER}--- Running Benchmarks ---{TColor.ENDC}")
    instance_files = sorted(INSTANCES_DIR.glob("in_*.txt"))
    results: Dict[str, Dict[str, Any]] = {
        instance.name: {} for instance in instance_files
    }

    for i, instance_path in enumerate(instance_files):
        print(f"\n{TColor.BOLD}Processing instance {i+1}/{len(instance_files)}: {instance_path.name}{TColor.ENDC}")
        
        try:
            with open(instance_path, 'r') as f:
                n = int(f.readline().strip().split()[0])
                time_limit = n // 10
            print(f"  {TColor.OKBLUE}Info:{TColor.ENDC} Instance n={n}, setting time limit to {time_limit}s")
        except (IOError, ValueError, IndexError):
            time_limit = DEFAULT_TIME_LIMIT
            print(f"  {TColor.WARNING}Warning: Could not parse 'n'. Using default timeout: {time_limit}s{TColor.ENDC}")
        
        for solver_path in solvers:
            solver_name = solver_path.name
            print(f"  -> Running {TColor.OKBLUE}{solver_name}{TColor.ENDC}...")
            
            solution_path = GENERATED_SOLUTIONS_DIR / f"out_{solver_name}_{instance_path.name}"
            
            command_base = [str(solver_path), str(instance_path), str(solution_path), str(int(time_limit))]
            command = ['python3'] + command_base if solver_path.suffix == '.py' else command_base
            
            status = ""
            cmax = None
            exec_time = 0.0

            start_time = time.monotonic()
            try:
                # Allow the process up to 3x the solver's requested time limit before forcing kill.
                proc = subprocess.run(
                    command, capture_output=True, text=True, timeout=time_limit * 3
                )
                exec_time = time.monotonic() - start_time
                
                if proc.returncode != 0:
                    status = "ERROR"
                    details = proc.stderr.strip().replace('\n', ' ')
                    print(f"    {TColor.FAIL}Status: {status} (exit code {proc.returncode}) - {details}{TColor.ENDC}")
                else:
                    # Now validate the generated solution file
                    verify_proc = subprocess.run(
                        ['python3', str(VALIDATOR_SCRIPT), str(instance_path), str(solution_path)],
                        capture_output=True, text=True
                    )
                    if verify_proc.returncode == 0:
                        status = "OK"
                        cmax = int(verify_proc.stdout.strip())
                        print(f"    {TColor.OKGREEN}Status: {status}, Cmax: {cmax}{TColor.ENDC} in {exec_time:.4f}s")
                    else:
                        status = "INVALID"
                        details = verify_proc.stderr.strip().replace("ERROR: ", "")
                        print(f"    {TColor.FAIL}Status: {status} ({details}){TColor.ENDC} in {exec_time:.4f}s")

            except subprocess.TimeoutExpired:
                status = "TIMEOUT"
                exec_time = time_limit
                print(f"    {TColor.WARNING}Status: {status}{TColor.ENDC} after {exec_time:.4f}s")
            except Exception as e:
                exec_time = time.monotonic() - start_time
                status = f"CRASH ({type(e).__name__})"
                print(f"    {TColor.FAIL}Status: {status}{TColor.ENDC} after {exec_time:.4f}s")

            results[instance_path.name][solver_name] = {
                'result': cmax if status == "OK" else status,
                'time': exec_time if status != "TIMEOUT" else time_limit
            }
    return results

def generate_reports(results: Dict[str, Dict[str, Any]], solvers: List[Path]):
    print(f"\n{TColor.HEADER}--- Generating Reports for Excel ---{TColor.ENDC}")
    solver_names = [s.name for s in solvers]
    
    # --- Cmax CSV Report ---
    cmax_path = RESULTS_DIR / 'results_cmax.csv'
    with open(cmax_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Instance'] + solver_names)
        for instance_name, solver_results in sorted(results.items()):
            row = [instance_name] + [solver_results.get(name, {}).get('result', 'N/A') for name in solver_names]
            writer.writerow(row)
    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Wrote Cmax results to: {cmax_path}")

    # --- Time CSV Report ---
    time_path = RESULTS_DIR / 'results_time.csv'
    with open(time_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Instance'] + solver_names)
        for instance_name, solver_results in sorted(results.items()):
            row = [instance_name]
            for name in solver_names:
                time_val = solver_results.get(name, {}).get('time')
                time_str = f"{time_val:.4f}" if isinstance(time_val, float) else 'N/A'
                row.append(time_str)
            writer.writerow(row)
    print(f"  {TColor.OKGREEN}✓{TColor.ENDC} Wrote Time results to: {time_path}")

def main():
    setup_environment()
    solvers = discover_solvers()
    results = run_benchmarks(solvers)
    generate_reports(results, solvers)
    print(f"\n{TColor.HEADER}--- Benchmark Complete ---{TColor.ENDC}")

if __name__ == "__main__":
    main()
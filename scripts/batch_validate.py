#!/usr/bin/env python3
#
# Validates each example solution file against ALL corresponding instances
# of the same size to perform a thorough baseline check.

import subprocess
from pathlib import Path
import re

# --- Configuration ---
INSTANCES_DIR = Path('../instances/all')
SOLUTIONS_DIR = Path('../solutions/example')
VALIDATOR_SCRIPT = Path('./validator.py')

def main():
    """
    Performs an 'outer join' style validation.
    For each out_SIZE[SUFFIX].txt, it finds all in_*_SIZE.txt and runs validation.
    """
    print("--- Phase 1: Running Thorough Baseline Dataset Validation ---")

    if not INSTANCES_DIR.is_dir() or not SOLUTIONS_DIR.is_dir():
        print(f"Error: Missing '{INSTANCES_DIR}' or '{SOLUTIONS_DIR}' directories.")
        return

    solution_files = sorted(SOLUTIONS_DIR.glob("out_*.txt"))
    if not solution_files:
        print(f"No example solution files found in '{SOLUTIONS_DIR}'.")
        return

    all_instances = list(INSTANCES_DIR.glob("in_*.txt"))

    # --- Main Validation Loop ---
    for sol_path in solution_files:
        # Extract size from solution filename like 'out_50.txt' or 'out_50A.txt'
        match = re.match(r'out_(\d+)[A-E]*.txt', sol_path.name)
        if not match:
            continue
        
        size = match.group(1)
        
        # Find all instance files that match this size
        matching_instances = [
            p for p in all_instances if p.name.endswith(f"_{size}.txt")
        ]

        print(f"\n--- Testing Solution: {sol_path.name} ---")
        if not matching_instances:
            print(f"  [WARN] No instance files found for size {size}.")
            continue

        print(f"  {'Instance':<30} {'Status':<10} {'Details / Cmax'}")
        print("  " + "-" * 70)

        for inst_path in sorted(matching_instances):
            try:
                # Run the official validator script
                proc = subprocess.run(
                    ['python3', str(VALIDATOR_SCRIPT), str(inst_path), str(sol_path)],
                    capture_output=True, text=True, check=True, timeout=30
                )
                status = "OK"
                details = f"Cmax: {proc.stdout.strip()}"
            except subprocess.CalledProcessError as e:
                status = "FAIL"
                details = e.stderr.strip().replace('ERROR: ', '')
            except subprocess.TimeoutExpired:
                status = "TIMEOUT"
                details = "Validator took too long"

            print(f"  {inst_path.name:<30} {status:<10} {details}")

if __name__ == "__main__":
    main()
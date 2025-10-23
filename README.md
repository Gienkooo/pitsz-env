# [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.12-blue.svg)]

# Contest Benchmarking Framework

This framework provides a standardized Docker environment and a set of scripts to automate the validation and benchmarking of solvers for programming contests. It ensures all submissions are tested under identical conditions, eliminating environment-related errors.

## Quick Start

1.  **Install Docker**: Ensure Docker is installed and running on your system.
2.  **Prepare Directories**:
    * Place all instance files (`in_*.txt`) for baseline validation in the `instances/all/` directory.
    * Place corresponding example solution files (`out_*.txt`) in `solutions/example/`.
    * Place the subset of instances for testing in `instances/test/`.
    * Place all student solver files (e.g., `123456` or `123456.py`) in the `solvers/` directory.
3.  **Build the Docker Image**:
    ```bash
    docker build -t contest-env .
    ```
4.  **Run the Container**: This command starts an interactive shell inside the container and mounts your project directory.
    ```bash
    docker run -it --rm -v "$(pwd):/app" contest-env
    ```
5.  **Navigate to the Scripts Directory**:
    ```bash
    cd scripts
    ```
6.  **Run the Tests**:
    * **Phase 1: Validate Baseline Dataset**
        ```bash
        python3 batch_validate.py
        ```
    * **Phase 2: Benchmark All Solvers**
        ```bash
        python3 benchmark_solvers.py
        ```
7.  **View Results**: The output CSV files (`results_cmax.csv`, `results_time.csv`) will be in the `results/` directory on your host machine, ready to be opened in Excel.

## For Participants: Solver Requirements

Your solver will be tested in an Ubuntu-based container that supports C++17 and a modern Python 3.x (the dev container used here runs Python 3.12). The C++ toolchain provides GMP (`libgmp-dev`) for big-integer support. The harness was built and tested with g++ that supports C++17.

* **File Naming**:
    * For C++ programs, submit a **compiled Linux binary** named with your student ID (e.g., `123456`).
    * For Python programs, submit a script named `<student_id>.py` (e.g., `123456.py`).
* **Command-Line Interface**: Your program **must** accept three command-line arguments:

        ```
        <your_solver> <input_file_path> <output_file_path> <time_limit_seconds>
        ```

        * It must read the instance from `<input_file_path>`.
        * It must write its final solution to `<output_file_path>` using the expected format:
            - First line: reported Cmax (integer)
            - Second line: number of batches
            - Next lines: one batch per line, space-separated 1-based task ids
        * `<time_limit_seconds>` is passed by the harness as an integer number of seconds. The solver should finish and exit before the time limit. The harness will apply a small safety margin internally and also enforce an OS-level timeout equal to 3× the requested time limit to detect hung processes.
        * If you want intermediate solutions to be visible when the harness kills your process, flush and write them to the `<output_file_path>` periodically (the harness reads only the final file produced at process exit).
* **Dependencies**: The environment includes the `libgmp-dev` library for C++. No other special libraries are pre-installed.

Performance note / recommendation
- Using GMP (big integers) is supported but slower. For the contest dataset the measured Cmax values fit comfortably into 64-bit integers — switching to native 64-bit types (e.g., `int64_t`) for `p`, `r` and internal time arithmetic typically yields a large runtime speedup. If you choose to use GMP, be aware of the extra per-evaluation cost when designing time-limited heuristics.

Benchmark harness behavior
- The harness passes an integer time limit to solvers. It subtracts a small safety margin before enforcing the internal time budget and uses a subprocess timeout equal to 3× the time limit to detect stalled processes. The harness also validates solution format using `scripts/validator.py` and will report errors if the file is malformed.

Opening the dev container
-------------------------
This project is intended to be run inside the supplied development container. Below are two easy ways to open the workspace in the dev container: the recommended VS Code flow, and a CLI (Docker) fallback.

1) VS Code (recommended)

- Install the "Dev Containers" (aka Remote - Containers) extension in VS Code.
- Open the repository folder in VS Code.
- Use the command palette (Ctrl+Shift+P) and run "Dev Containers: Reopen in Container" (or "Remote-Containers: Open Folder in Container").
- VS Code will build the container (using the repo's devcontainer.json if present) and reopen the workspace inside the container. The terminal in VS Code will then operate inside the container and the editor will use the container toolchain.

Tips:
- If you don't have a `.devcontainer/devcontainer.json` file, VS Code will prompt to create one or it will reuse the Dockerfile in the repo if configured. You can also pick a predefined container config.
- When the container builds the first time it may take a few minutes; subsequent starts are much faster.

2) CLI Docker (fallback)

If you prefer the command line or need to run the container manually, build and run the container and mount the repository into `/app`:

```bash
docker build -t contest-env .
docker run -it --rm -v "$(pwd):/app" -w /app contest-env bash
```

This starts an interactive shell inside the container with the repository mounted at `/app`. From there you can run the same commands listed in this README (for example `cd scripts` and `python3 benchmark_solvers.py`).

Port forwarding / extra capabilities
- If your workflow requires forwarded ports (for web UIs) or additional mounts, add `-p` or extra `-v` flags to the `docker run` command. For GPUs, use the appropriate runtime flags (not configured by default in this repo).

Troubleshooting
- If the container rebuilds frequently, check for changes to the Dockerfile or files referenced by the devcontainer configuration.
- If extensions are installed inside the container and you want them available locally, use the VS Code extensions panel to manage container extensions.
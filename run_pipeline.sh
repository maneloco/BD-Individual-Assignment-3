#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="${1:-all}"

echo "=========================================================="
echo "  Parallel Matrix Multiplication Pipeline (Assignment 3)  "
echo "=========================================================="

if [ -d ".venv" ]; then
    PY_BIN=".venv/bin/python"
elif [ -d "../BD_Assignment2/.venv" ]; then
    PY_BIN="../BD_Assignment2/.venv/bin/python"
else
    echo "Creating Python virtual environment in .venv..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt > /dev/null
    PY_BIN=".venv/bin/python"
fi

if [ "$MODE" = "plots" ]; then
    echo "[1/1] Generating figures from existing CSV results..."
    "$PY_BIN" tools/plot_results.py
    echo "===> Figures successfully generated in results/figures/"
    exit 0
fi

echo "[1/4] Running unit tests to verify correctness..."
make clean > /dev/null
make run_tests

echo "[2/4] Compiling project in performance mode (-O3 -march=native)..."
make performance > /dev/null

mkdir -p results
CSV_OUTPUT="parallel_benchmark.csv"

echo "[3/4] Executing benchmark suite (mode: $MODE)..."
echo "      (Live progress shown below; raw data saved to results/$CSV_OUTPUT)"

if [ "$MODE" = "quick" ]; then
    ./bin/benchmark --quick --output="$CSV_OUTPUT"
elif [ "$MODE" = "medium" ]; then
    ./bin/benchmark --medium --output="$CSV_OUTPUT"
else
    ./bin/benchmark "$CSV_OUTPUT"
fi

echo "      Benchmarks completed successfully."

echo "[4/4] Generating publication-quality figures..."
"$PY_BIN" tools/plot_results.py "$CSV_OUTPUT"

echo "=========================================================="
echo "  Pipeline completed successfully!"
echo "  - Raw CSV results: results/$CSV_OUTPUT"
echo "  - Generated figures: results/figures/"
echo "=========================================================="

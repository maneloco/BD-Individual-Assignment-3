# Parallel Matrix Multiplication and Shared-Memory Scalability
**Big Data**  
*Grado en Ciencia e Ingeniería de Datos — Universidad de Las Palmas de Gran Canaria (ULPGC)*  
**Author:** Manuel Muñoz Roca  

---

## 1. Project Overview

This project implements and empirically evaluates shared-memory parallel matrix multiplication in C using POSIX Threads (`pthreads`). The study compares a parallelized matrix multiplication against an equivalent sequential baseline (`matrix_mult_ikj`) across varying matrix sizes and thread counts on a heterogeneous multi-core processor.

### Key Implementations
- **Sequential Baseline (`ikj`):**
  - Loop-reordered matrix multiplication (`ikj`) providing stride-1 contiguous memory access, register reuse, and automatic SIMD vectorization (AVX2).
- **POSIX Thread Pool (`thread.h`, `thread.c`):**
  - Persistent worker thread pool initialized once to eliminate thread creation and destruction overhead.
  - Circular FIFO task queue protected by a single mutex and condition variables (`has_work`, `all_idle`).
  - Safe barrier synchronization (`threadpool_wait`) and clean teardown (`threadpool_destroy`).
- **Parallel Matrix Multiplication (`parallel_matmul.h`, `parallel_matmul.c`):**
  - Outer-loop ($i$) row-slicing work distribution with remainder balancing ($\lfloor n/p \rfloor + (t < n\%p ? 1 : 0)$).
  - Independent cache-line writes per thread for zero false sharing ($n \ge 8$).
  - C99 `restrict` pointers enabling GCC auto-vectorization across parallel worker tasks.

---

## 2. Experimental Environment & System Specifications

All benchmarks and empirical evaluations were conducted on the following controlled hardware and software environment:

| Component | Specification |
| :--- | :--- |
| **Processor** | 12th Gen Intel(R) Core(TM) i5-12500H |
| **Microarchitecture** | Alder Lake (Hybrid: 4 Performance-cores + 8 Efficient-cores) |
| **Physical Cores** | 12 cores |
| **Logical Threads** | 16 hardware threads (P-cores support HyperThreading) |
| **L1d (Data) Cache** | 448 KiB total (48 KiB per P-core / 32 KiB per E-core) |
| **L2 Cache** | 9 MiB total (1.25 MiB per P-core / 2 MiB per E-core cluster) |
| **L3 Cache (LLC)** | 18 MiB shared Last-Level Cache |
| **System Memory** | 16 GiB DDR RAM (15 GiB physical available, 0 swap) |
| **Operating System** | Arch Linux (x86_64, Kernel `6.12.7`) |
| **C Compiler** | GCC 14.2.1 (`-std=c11`) |
| **Python Runtime** | Python 3.12+ (Virtual environment `.venv`) |

---

## 3. Compilation & Build Configuration

The project includes a modular `Makefile` with strict compilation standards:

```bash
make              # Compiles the benchmark suite (bin/benchmark)
make performance  # Recompiles from scratch with maximum CPU optimizations (-O3 -march=native)
make tests        # Compiles unit test binaries (bin/test_parallel)
make run_tests    # Compiles and executes the automated unit test suite
make clean        # Removes all build artifacts, objects, and binaries
```

### Compiler Flags Rationale

- **`-std=c11`**: Enforces ISO/IEC 9899:2011 standard compliance.
- **`-Wall -Wextra -Wpedantic`**: Enables comprehensive compile-time diagnostics.
- **`-O3`**: Enables compiler optimization passes, including loop unrolling and AVX2 vectorization.
- **`-march=native`**: Enables processor-specific vector instruction sets (AVX2, FMA) for the host Alder Lake CPU.
- **`-lpthread -lm`**: Links the POSIX threads and standard math libraries.

#### Deliberate Exclusion of `-ffast-math`
We intentionally **omit** `-ffast-math` across all benchmark builds. While `-ffast-math` can yield minor synthetic speedups by assuming floating-point associativity and ignoring NaNs/Infinities, it violates the **IEEE 754** floating-point specification. Omitting it ensures strict numerical consistency, reproducible checksums, and fair comparisons between sequential and parallel implementations.

---

## 4. Project Directory Structure

```text
BD_Assignment3/
├── Makefile                    # Build automation configuration
├── README.md                   # System specifications and reproducibility guide
├── requirements.txt            # Python dependencies for plotting (frozen versions)
├── run_pipeline.sh             # End-to-end automated execution pipeline
├── report.tex                  # LaTeX source of research report
├── report.pdf                  # Compiled PDF research report
├── benchmarks/                 # Benchmarking harness and experiment runners
│   ├── benchmark.c             # Multi-size and multi-thread benchmark execution
│   ├── benchmark_harness.c     # Monotonic timing, fork isolation, RSS tracking, CSV export
│   └── benchmark_harness.h     # Harness header declarations
├── include/                    # Header files
│   ├── matmul.h                # Sequential baseline prototype (ikj)
│   ├── matrix.h                # Matrix structure and memory allocation prototypes
│   ├── parallel_matmul.h       # Parallel matrix multiplication prototypes
│   ├── rng.h                   # Deterministic PRNG interface
│   └── thread.h                # POSIX thread pool API declarations
├── src/                        # Core C implementation sources
│   ├── matmul.c                # Sequential ikj multiplication implementation
│   ├── matrix.c                # Allocation, zeroing, random generation, equality checks
│   ├── parallel_matmul.c       # Row slicing task dispatch and worker routines
│   ├── rng.c                   # Deterministic PRNG implementation
│   └── thread.c                # Thread pool implementation (mutex, condition variables)
├── tests/                      # Unit and regression test suite
│   ├── test_matmul.c           # Sequential baseline verification against reference multiplication
│   ├── test_matrix.c           # Matrix primitives, allocation, zeros, identity, equality
│   ├── test_parallel.c         # Thread pool stress, edge cases, and equivalence tests
│   └── test_rng.c              # Deterministic PRNG properties, limits, and uniform distribution
├── tools/                      # Visualization scripts
│   └── plot_results.py         # Python script generating the 5 analytical figures
└── results/                    # Generated benchmark outputs
    ├── parallel_benchmark.csv  # Raw experimental timing, RSS, and checksums
    └── figures/                # Generated publication-quality figures (300 DPI)
        ├── speedup_vs_threads.png      # Speedup S(p) vs threads (1 to 32)
        ├── efficiency_vs_threads.png   # Parallel efficiency E(p) vs threads
        ├── execution_time_vs_n.png     # Execution time vs n (log2-log2 scale)
        ├── framework_overhead.png      # Single-thread overhead ratio T_par(1)/T_seq
        └── memory_scaling.png          # Peak RSS vs theoretical 3 * 8n^2 memory
```

---

## 5. Reproduction & Execution Guide

### Automated End-to-End Pipeline
To run the automated test suite, compile the project in performance mode, run benchmarks, and generate all figures in one step:

```bash
./run_pipeline.sh
```

### Selective / Fast Execution Modes
- **Regenerate Figures Only** (instantaneous from existing CSV data):
  ```bash
  ./run_pipeline.sh plots
  ```
- **Quick Benchmark Run** ($n \le 512$, fast verification):
  ```bash
  ./run_pipeline.sh quick
  ```
- **Medium Benchmark Run** ($n \le 2048$):
  ```bash
  ./run_pipeline.sh medium
  ```

### Verifying Code Correctness & Test Suite
To run the complete automated test suite (verifying thread pool lifecycle, edge cases, and numerical equivalence between sequential and parallel versions):

```bash
make run_tests
```

To run with AddressSanitizer and ThreadSanitizer:
```bash
# Memory leaks and undefined behavior check
gcc -fsanitize=address,undefined -Iinclude src/*.c tests/test_parallel.c -lpthread -lm -o bin/test_asan && ./bin/test_asan

# Data race detection
gcc -fsanitize=thread -Iinclude src/*.c tests/test_parallel.c -lpthread -lm -o bin/test_tsan && ./bin/test_tsan
```

### Compiling the Report
To compile the LaTeX report to PDF:
```bash
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
```

---

## 6. Summary of Experimental Findings

1. **Parallelism Threshold ($n > 128$):** For small matrices ($n \le 64$), parallel execution is slower than sequential execution ($S \approx 0.51\times$) due to thread coordination and mutex latency.
2. **Speedup on Large Matrices:** At $n = 4096$, 16 threads achieve a **$5.19\times$ speedup**, dropping execution time from 25.30 seconds down to 4.88 seconds.
3. **P-Core Scaling:** Speedup scales near-linearly across the 4 physical P-cores ($3.43\times$ speedup at $p = 4$, $85.8\%$ parallel efficiency).
4. **The Oversubscription Cliff ($p > 16$):** Running 24 or 32 threads on a 16-thread processor causes runtime to almost double (from 4.88s at 16 threads to 9.79s at 32 threads) due to OS context switches and cache thrashing.
5. **Zero Dynamic Memory Overhead:** Peak RSS strictly follows the theoretical $3 \times 8n^2$ storage footprint with zero thread-local heap allocation during multiplication.

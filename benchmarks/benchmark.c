#include "benchmark_harness.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void run_matrix_sweep(FILE *file, int repetitions, uint64_t base_seed, int max_size) {
    size_t all_sizes[] = {
        1, 2, 4, 8, 16, 32, 64, 128, 256, 512,
        1024, 1536, 2048, 2560, 3072, 3584, 4096
    };
    size_t total_sizes = sizeof(all_sizes) / sizeof(all_sizes[0]);

    size_t thread_counts[] = {1, 2, 4, 8, 12, 16, 24, 32};
    size_t num_threads = sizeof(thread_counts) / sizeof(thread_counts[0]);

    printf("\n=== Starting Matrix Multiplication Benchmark Sweep ===\n");
    printf("Sizes (%zu total, max %d): 1 to 4096\n", total_sizes, max_size > 0 ? max_size : 4096);
    printf("Thread counts (%zu total): 1, 2, 4, 8, 12, 16, 24, 32\n", num_threads);
    printf("Repetitions per config: %d (plus 1 warmup)\n\n", repetitions);

    for (size_t s = 0; s < total_sizes; s++) {
        size_t n = all_sizes[s];
        if (max_size > 0 && (int)n > max_size) {
            break;
        }

        printf(">>> MATRIX SIZE n = %zu <<<\n", n);

        run_isolated_trial(file, "seq_ikj", n, 1, -1, base_seed);
        for (int r = 0; r < repetitions; r++) {
            run_isolated_trial(file, "seq_ikj", n, 1, r, base_seed);
        }

        for (size_t t = 0; t < num_threads; t++) {
            size_t p = thread_counts[t];
            run_isolated_trial(file, "par_ikj", n, p, -1, base_seed);
            for (int r = 0; r < repetitions; r++) {
                run_isolated_trial(file, "par_ikj", n, p, r, base_seed);
            }
        }
        printf("\n");
    }
}

int main(int argc, char **argv) {
    const char *output_filename = "parallel_benchmark.csv";
    int repetitions = 5;
    uint64_t seed = 42;
    int max_size = 4096;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--quick") == 0 || strcmp(argv[i], "quick") == 0) {
            max_size = 512;
            repetitions = 3;
        } else if (strcmp(argv[i], "--medium") == 0 || strcmp(argv[i], "medium") == 0) {
            max_size = 2048;
        } else if (strncmp(argv[i], "--output=", 9) == 0) {
            output_filename = argv[i] + 9;
        } else if (argv[i][0] != '-') {
            output_filename = argv[i];
        }
    }

    FILE *csv = benchmark_create_csv("results", output_filename);
    if (csv == NULL) {
        return 1;
    }

    printf("Executing benchmark -> writing output to results/%s\n", output_filename);
    run_matrix_sweep(csv, repetitions, seed, max_size);

    benchmark_close_csv(csv);
    printf("=== Benchmarks complete. Output written to results/%s ===\n", output_filename);
    return 0;
}

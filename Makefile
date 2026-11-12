CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2 -Iinclude
LDFLAGS ?= -lpthread -lm

SRC_DIR := src
INC_DIR := include
TEST_DIR := tests
BUILD_DIR := build
BIN_DIR := bin

CORE_SRCS := $(wildcard $(SRC_DIR)/*.c)
CORE_OBJS := $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(CORE_SRCS))

TEST_SRCS := $(wildcard $(TEST_DIR)/*.c)
TEST_BINS := $(patsubst $(TEST_DIR)/%.c, $(BIN_DIR)/%, $(TEST_SRCS))

BENCH_DIR := benchmarks
BENCHMARK := $(BIN_DIR)/benchmark

.PHONY: all clean tests run_tests help performance benchmark

all: benchmark

$(BUILD_DIR) $(BIN_DIR):
	@mkdir -p $@

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(BIN_DIR)/test_%: $(TEST_DIR)/test_%.c $(CORE_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $< $(CORE_OBJS) -o $@ $(LDFLAGS)
	@echo "==> Test built successfully: $@"

tests: $(TEST_BINS)

$(BENCHMARK): $(BENCH_DIR)/benchmark.c $(BENCH_DIR)/benchmark_harness.c $(CORE_OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) -I$(BENCH_DIR) $^ -o $@ $(LDFLAGS)
	@echo "==> Benchmark built successfully: $@"

benchmark: $(BENCHMARK)

run_tests: tests
	@echo "\n=== EXECUTING TEST SUITE ==="
	@for t in $(TEST_BINS); do \
		echo "\n[TEST] Executing $$t..."; \
		$$t || exit 1; \
	done
	@echo "\n===> All tests passed successfully.\n"

performance:
	@echo "\n=== COMPILING FOR PERFORMANCE ==="
	@$(MAKE) clean
	@$(MAKE) benchmark CFLAGS="-std=c11 -Wall -Wextra -Wpedantic -O3 -march=native -Iinclude"
	@echo "==> Performance build complete: $(BENCHMARK)\n"

clean:
	@rm -rf $(BUILD_DIR) $(BIN_DIR)
	@echo "==> Clean complete."

help:
	@echo "Available commands:"
	@echo "  make            - Compiles the benchmark suite ($(BENCHMARK))"
	@echo "  make performance- Compiles benchmark with -O3 -march=native"
	@echo "  make tests      - Compiles the test suite"
	@echo "  make run_tests  - Compiles and runs tests automatically"
	@echo "  make clean      - Erases all objects and binaries"

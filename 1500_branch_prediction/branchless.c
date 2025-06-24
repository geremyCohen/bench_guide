#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

#define ARRAY_SIZE 10000000
#define ITERATIONS 100

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

uint64_t test_branchless(int *array) {
    uint64_t sum = 0;
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (int i = 0; i < ARRAY_SIZE; i++) {
            // Branchless version using bitwise operations
            int64_t value = (int64_t)i;
            int64_t neg_value = -value;
            int64_t mask = -(int64_t)array[i];  // 0 or -1
            sum += ((value & mask) | (neg_value & ~mask));
        }
    }
    
    return sum;
}

int main() {
    int *array = malloc(ARRAY_SIZE * sizeof(int));
    if (!array) return 1;
    
    // Initialize with random pattern
    for (int i = 0; i < ARRAY_SIZE; i++) {
        array[i] = rand() % 2;
    }
    
    // Benchmark
    double start = get_time();
    volatile uint64_t result = test_branchless(array);
    double end = get_time();
    
    printf("Time: %.6f seconds\n", end - start);
    printf("Result: %lu\n", result);
    
    free(array);
    return 0;
}
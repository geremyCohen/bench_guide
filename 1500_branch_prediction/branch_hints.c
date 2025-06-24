#include <stdio.h>
#include <stdlib.h>
<parameter name="time.h>
#include <stdint.h>

#define ARRAY_SIZE 10000000
#define ITERATIONS 100

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

uint64_t test_with_hints(int *array) {
    uint64_t sum = 0;
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (int i = 0; i < ARRAY_SIZE; i++) {
            // Use branch hint for likely taken branches
            if (__builtin_expect(array[i], 1)) {
                sum += i;
            } else {
                sum -= i;
            }
        }
    }
    
    return sum;
}

int main() {
    int *array = malloc(ARRAY_SIZE * sizeof(int));
    if (!array) return 1;
    
    // Initialize with mostly taken pattern (90%)
    for (int i = 0; i < ARRAY_SIZE; i++) {
        array[i] = (rand() % 100) < 90 ? 1 : 0;
    }
    
    // Benchmark
    double start = get_time();
    volatile uint64_t result = test_with_hints(array);
    double end = get_time();
    
    printf("Time: %.6f seconds\n", end - start);
    printf("Result: %lu\n", result);
    
    free(array);
    return 0;
}
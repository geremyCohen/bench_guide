#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

#define ARRAY_SIZE 10000000
#define ITERATIONS 100

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Create different branch patterns
void create_pattern(int *array, int pattern) {
    for (int i = 0; i < ARRAY_SIZE; i++) {
        switch (pattern) {
            case 0: // Always taken
                array[i] = 1;
                break;
            case 1: // Never taken
                array[i] = 0;
                break;
            case 2: // Alternating
                array[i] = i % 2;
                break;
            case 3: // Random
                array[i] = rand() % 2;
                break;
            case 4: // Mostly taken (90%)
                array[i] = (rand() % 100) < 90 ? 1 : 0;
                break;
            default:
                array[i] = rand() % 2;
        }
    }
}

// Test branch prediction
uint64_t test_branches(int *array, int pattern) {
    uint64_t sum = 0;
    
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (int i = 0; i < ARRAY_SIZE; i++) {
            if (array[i]) {
                sum += i;
            } else {
                sum -= i;
            }
        }
    }
    
    return sum;
}

int main(int argc, char *argv[]) {
    int pattern = 0;
    if (argc > 1) {
        pattern = atoi(argv[1]);
    }
    
    // Allocate array
    int *array = (int *)malloc(ARRAY_SIZE * sizeof(int));
    if (!array) {
        perror("malloc");
        return 1;
    }
    
    // Initialize random seed
    srand(time(NULL));
    
    // Create pattern
    create_pattern(array, pattern);
    
    // Warm up
    volatile uint64_t result = test_branches(array, pattern);
    
    // Benchmark
    double start_time = get_time();
    result = test_branches(array, pattern);
    double end_time = get_time();
    
    double elapsed = end_time - start_time;
    double branches_per_second = (double)ARRAY_SIZE * ITERATIONS / elapsed;
    
    printf("Pattern: %d\n", pattern);
    printf("Time: %.6f seconds\n", elapsed);
    printf("Branches per second: %.2f million\n", branches_per_second / 1000000);
    printf("Result: %lu\n", result);
    
    // Clean up
    free(array);
    return 0;
}
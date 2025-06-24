#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

#define ARRAY_SIZE (64 * 1024 * 1024)  // 64MB
#define ITERATIONS 10

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Standard sequential access
void standard_access(int *array, size_t size) {
    volatile int sum = 0;
    
    for (size_t i = 0; i < size; i++) {
        sum += array[i];
    }
}

// Arm-optimized access with prefetch
void prefetch_access(int *array, size_t size) {
    volatile int sum = 0;
    
    for (size_t i = 0; i < size; i++) {
        // Prefetch data 64 elements ahead
        #ifdef __aarch64__
        __builtin_prefetch(&array[i + 64], 0, 3);
        #endif
        
        sum += array[i];
    }
}

// Arm-optimized access with multiple prefetch distances
void multi_prefetch_access(int *array, size_t size) {
    volatile int sum = 0;
    
    for (size_t i = 0; i < size; i++) {
        #ifdef __aarch64__
        // Prefetch at different distances for different cache levels
        __builtin_prefetch(&array[i + 16], 0, 3);  // L1 cache
        __builtin_prefetch(&array[i + 64], 0, 2);  // L2 cache
        __builtin_prefetch(&array[i + 256], 0, 1); // L3 cache
        #endif
        
        sum += array[i];
    }
}

int main() {
    // Allocate array
    int *array = (int *)malloc(ARRAY_SIZE * sizeof(int));
    if (!array) {
        perror("malloc");
        return 1;
    }
    
    // Initialize array
    for (size_t i = 0; i < ARRAY_SIZE; i++) {
        array[i] = i;
    }
    
    // Test standard access
    double start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        standard_access(array, ARRAY_SIZE);
    }
    double end = get_time();
    
    printf("Standard access time: %.6f seconds\n", end - start);
    
    // Test prefetch access
    start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        prefetch_access(array, ARRAY_SIZE);
    }
    end = get_time();
    
    printf("Prefetch access time: %.6f seconds\n", end - start);
    
    // Test multi-prefetch access
    start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        multi_prefetch_access(array, ARRAY_SIZE);
    }
    end = get_time();
    
    printf("Multi-prefetch access time: %.6f seconds\n", end - start);
    
    free(array);
    return 0;
}
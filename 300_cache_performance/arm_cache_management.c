#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

#define ARRAY_SIZE (16 * 1024 * 1024)  // 16MB
#define ITERATIONS 10

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Standard array initialization
void standard_init(int *array, size_t size) {
    for (size_t i = 0; i < size; i++) {
        array[i] = i;
    }
}

// Arm-optimized initialization with cache management
void cache_managed_init(int *array, size_t size) {
    for (size_t i = 0; i < size; i++) {
        array[i] = i;
        
        // Every 4096 elements (16KB), clean the cache line
        if ((i & 0xFFF) == 0) {
            #ifdef __aarch64__
            // Clean data cache by virtual address to point of coherency
            __asm__ volatile("dc cvac, %0" : : "r" (&array[i]) : "memory");
            #endif
        }
    }
    
    #ifdef __aarch64__
    // Data synchronization barrier
    __asm__ volatile("dsb ish" : : : "memory");
    #endif
}

// Benchmark function
void benchmark_access(int *array, size_t size) {
    volatile int sum = 0;
    
    for (size_t i = 0; i < size; i++) {
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
    
    // Test standard initialization and access
    double start = get_time();
    standard_init(array, ARRAY_SIZE);
    double mid = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        benchmark_access(array, ARRAY_SIZE);
    }
    double end = get_time();
    
    printf("Standard initialization time: %.6f seconds\n", mid - start);
    printf("Standard access time: %.6f seconds\n", end - mid);
    
    // Test cache-managed initialization and access
    start = get_time();
    cache_managed_init(array, ARRAY_SIZE);
    mid = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        benchmark_access(array, ARRAY_SIZE);
    }
    end = get_time();
    
    printf("Cache-managed initialization time: %.6f seconds\n", mid - start);
    printf("Cache-managed access time: %.6f seconds\n", end - mid);
    
    free(array);
    return 0;
}
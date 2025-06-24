#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define MAX_ARRAY_SIZE (64 * 1024 * 1024)  // 64MB
#define MIN_ARRAY_SIZE (1 * 1024)          // 1KB
#define ITERATIONS 100000000
#define STEP_FACTOR 2

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Sequential access pattern
void sequential_access(int *array, size_t array_size, size_t iterations) {
    size_t i, iter;
    volatile int sum = 0;  // Prevent optimization
    
    for (iter = 0; iter < iterations; iter++) {
        for (i = 0; i < array_size; i++) {
            sum += array[i];
        }
        
        // Break early for large arrays to keep runtime reasonable
        if (array_size > 1024 * 1024 && iter > iterations / 100) {
            break;
        }
    }
}

// Random access pattern
void random_access(int *array, size_t array_size, int *indices, size_t iterations) {
    size_t i, iter;
    volatile int sum = 0;  // Prevent optimization
    
    for (iter = 0; iter < iterations; iter++) {
        for (i = 0; i < array_size; i++) {
            sum += array[indices[i]];
        }
        
        // Break early for large arrays to keep runtime reasonable
        if (array_size > 1024 * 1024 && iter > iterations / 100) {
            break;
        }
    }
}

// Strided access pattern
void strided_access(int *array, size_t array_size, size_t stride, size_t iterations) {
    size_t i, iter;
    volatile int sum = 0;  // Prevent optimization
    
    for (iter = 0; iter < iterations; iter++) {
        for (i = 0; i < array_size; i += stride) {
            sum += array[i];
        }
        
        // Break early for large arrays to keep runtime reasonable
        if (array_size > 1024 * 1024 && iter > iterations / 100) {
            break;
        }
    }
}

int main(int argc, char *argv[]) {
    int access_pattern = 0;  // 0: sequential, 1: random, 2: strided
    int stride = 16;         // Default stride for strided access
    
    // Parse command line arguments
    if (argc > 1) {
        access_pattern = atoi(argv[1]);
    }
    if (argc > 2) {
        stride = atoi(argv[2]);
    }
    
    printf("Access pattern: %d (0: sequential, 1: random, 2: strided)\n", access_pattern);
    if (access_pattern == 2) {
        printf("Stride: %d\n", stride);
    }
    
    // Allocate maximum array size
    int *array = (int *)malloc(MAX_ARRAY_SIZE * sizeof(int));
    if (!array) {
        perror("malloc");
        return 1;
    }
    
    // Initialize array
    for (size_t i = 0; i < MAX_ARRAY_SIZE; i++) {
        array[i] = i;
    }
    
    // For random access, create index array
    int *indices = NULL;
    if (access_pattern == 1) {
        indices = (int *)malloc(MAX_ARRAY_SIZE * sizeof(int));
        if (!indices) {
            perror("malloc");
            free(array);
            return 1;
        }
        
        // Initialize indices with random values
        for (size_t i = 0; i < MAX_ARRAY_SIZE; i++) {
            indices[i] = rand() % MAX_ARRAY_SIZE;
        }
    }
    
    // Test different array sizes
    printf("Array size (bytes),Access time (ns)\n");
    
    for (size_t array_size = MIN_ARRAY_SIZE; array_size <= MAX_ARRAY_SIZE; array_size *= STEP_FACTOR) {
        size_t elements = array_size / sizeof(int);
        
        // Adjust iterations based on array size to keep runtime reasonable
        size_t adjusted_iterations = ITERATIONS / (array_size / MIN_ARRAY_SIZE);
        if (adjusted_iterations < 10) adjusted_iterations = 10;
        
        // Warm up cache
        if (access_pattern == 0) {
            sequential_access(array, elements, 10);
        } else if (access_pattern == 1) {
            random_access(array, elements, indices, 10);
        } else {
            strided_access(array, elements, stride, 10);
        }
        
        // Measure access time
        double start_time = get_time();
        
        if (access_pattern == 0) {
            sequential_access(array, elements, adjusted_iterations);
        } else if (access_pattern == 1) {
            random_access(array, elements, indices, adjusted_iterations);
        } else {
            strided_access(array, elements, stride, adjusted_iterations);
        }
        
        double end_time = get_time();
        double elapsed = end_time - start_time;
        
        // Calculate average access time in nanoseconds
        double access_time_ns = (elapsed * 1e9) / (elements * adjusted_iterations);
        
        printf("%zu,%.2f\n", array_size, access_time_ns);
    }
    
    // Clean up
    free(array);
    if (indices) free(indices);
    
    return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#define ARRAY_SIZE (4 * 1024 * 1024)
#define ITERATIONS 100

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void fp_operations(double *a, double *b, double *c, int size) {
    for (int i = 0; i < size; i++) {
        c[i] = (a[i] * b[i]) + sin(a[i]) - cos(b[i]);
    }
}

int main() {
    double *a = malloc(ARRAY_SIZE * sizeof(double));
    double *b = malloc(ARRAY_SIZE * sizeof(double));
    double *c = malloc(ARRAY_SIZE * sizeof(double));
    
    if (!a || !b || !c) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Initialize arrays
    for (int i = 0; i < ARRAY_SIZE; i++) {
        a[i] = (double)i / 1000.0;
        b[i] = (double)(i + 1) / 1000.0;
    }
    
    // Benchmark
    double start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        fp_operations(a, b, c, ARRAY_SIZE);
    }
    double elapsed = get_time() - start;
    
    printf("Floating-point operations time: %.6f seconds\n", elapsed);
    printf("Operations per second: %.2f million\n", 
           (ARRAY_SIZE * ITERATIONS * 4.0) / elapsed / 1000000);
    
    free(a);
    free(b);
    free(c);
    return 0;
}
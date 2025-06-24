#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ITERATIONS 1000000

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void benchmark_function() {
    volatile int sum = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum += i;
    }
}

int main() {
    printf("Microarchitectural Benchmark\n");
    
    double start = get_time();
    benchmark_function();
    double elapsed = get_time() - start;
    
    printf("Time: %.6f seconds\n", elapsed);
    printf("Operations per second: %.2f million\n", ITERATIONS / elapsed / 1000000);
    
    return 0;
}
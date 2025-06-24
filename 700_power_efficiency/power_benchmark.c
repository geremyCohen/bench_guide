#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/time.h>

#define WORKLOAD_DURATION 10

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void cpu_intensive_workload() {
    volatile double result = 0;
    double start = get_time();
    
    while (get_time() - start < WORKLOAD_DURATION) {
        for (int i = 0; i < 100000; i++) {
            result += i * 3.14159;
        }
    }
}

void memory_intensive_workload() {
    const int size = 64 * 1024 * 1024;  // 256MB
    int *array = malloc(size * sizeof(int));
    if (!array) return;
    
    double start = get_time();
    
    while (get_time() - start < WORKLOAD_DURATION) {
        for (int i = 0; i < size; i++) {
            array[i] = i;
        }
        for (int i = 0; i < size; i++) {
            volatile int temp = array[i];
        }
    }
    
    free(array);
}

void idle_workload() {
    double start = get_time();
    
    while (get_time() - start < WORKLOAD_DURATION) {
        usleep(1000);  // Sleep for 1ms
    }
}

int main() {
    printf("Power Efficiency Benchmark\n");
    printf("Architecture: %s\n", 
#ifdef __aarch64__
        "ARM64"
#elif defined(__x86_64__)
        "x86_64"
#else
        "Unknown"
#endif
    );
    
    printf("\nRunning CPU intensive workload for %d seconds...\n", WORKLOAD_DURATION);
    double start = get_time();
    cpu_intensive_workload();
    double cpu_time = get_time() - start;
    printf("CPU workload completed in %.2f seconds\n", cpu_time);
    
    printf("\nRunning memory intensive workload for %d seconds...\n", WORKLOAD_DURATION);
    start = get_time();
    memory_intensive_workload();
    double mem_time = get_time() - start;
    printf("Memory workload completed in %.2f seconds\n", mem_time);
    
    printf("\nRunning idle workload for %d seconds...\n", WORKLOAD_DURATION);
    start = get_time();
    idle_workload();
    double idle_time = get_time() - start;
    printf("Idle workload completed in %.2f seconds\n", idle_time);
    
    printf("\nNote: Use external power monitoring tools to measure actual power consumption\n");
    
    return 0;
}
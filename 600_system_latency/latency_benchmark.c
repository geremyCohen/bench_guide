#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

#define ITERATIONS 1000000

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void test_syscall_latency() {
    double start = get_time();
    
    for (int i = 0; i < ITERATIONS; i++) {
        getpid();
    }
    
    double elapsed = get_time() - start;
    printf("System call latency: %.2f ns per call\n", 
           (elapsed * 1e9) / ITERATIONS);
}

void test_memory_latency() {
    int *array = malloc(64 * 1024 * 1024 * sizeof(int));  // 256MB
    if (!array) return;
    
    // Initialize with pointer chasing pattern
    for (int i = 0; i < 64 * 1024 * 1024 - 1; i++) {
        array[i] = i + 1;
    }
    array[64 * 1024 * 1024 - 1] = 0;
    
    double start = get_time();
    volatile int index = 0;
    
    for (int i = 0; i < ITERATIONS; i++) {
        index = array[index];
    }
    
    double elapsed = get_time() - start;
    printf("Memory access latency: %.2f ns per access\n", 
           (elapsed * 1e9) / ITERATIONS);
    
    free(array);
}

void test_context_switch() {
    int pipefd[2];
    if (pipe(pipefd) == -1) return;
    
    pid_t pid = fork();
    if (pid == 0) {
        // Child process
        char byte;
        for (int i = 0; i < ITERATIONS / 2; i++) {
            read(pipefd[0], &byte, 1);
            write(pipefd[1], &byte, 1);
        }
        exit(0);
    } else if (pid > 0) {
        // Parent process
        char byte = 'A';
        double start = get_time();
        
        for (int i = 0; i < ITERATIONS / 2; i++) {
            write(pipefd[1], &byte, 1);
            read(pipefd[0], &byte, 1);
        }
        
        double elapsed = get_time() - start;
        printf("Context switch latency: %.2f ns per switch\n", 
               (elapsed * 1e9) / (ITERATIONS / 2));
        
        wait(NULL);
    }
    
    close(pipefd[0]);
    close(pipefd[1]);
}

int main() {
    printf("System Latency Benchmark\n");
    printf("Iterations: %d\n\n", ITERATIONS);
    
    test_syscall_latency();
    test_memory_latency();
    test_context_switch();
    
    return 0;
}
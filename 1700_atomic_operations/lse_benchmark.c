#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <stdint.h>
#include <stdatomic.h>

#define NUM_THREADS 4
#define ITERATIONS 10000000

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Thread argument structure
typedef struct {
    int thread_id;
    int num_iterations;
    _Atomic int *counter;
    int use_lse;
} thread_arg_t;

// Thread function for atomic increment
void* atomic_increment_thread(void* arg) {
    thread_arg_t* thread_arg = (thread_arg_t*)arg;
    _Atomic int *counter = thread_arg->counter;
    int iterations = thread_arg->num_iterations;
    
    if (thread_arg->use_lse) {
        // Use C11 atomics (will use LSE on supported hardware)
        for (int i = 0; i < iterations; i++) {
            atomic_fetch_add(counter, 1);
        }
    } else {
        // Use inline assembly with load-exclusive/store-exclusive
        for (int i = 0; i < iterations; i++) {
            int old_val, new_val;
            do {
                // Load exclusive
                __asm__ volatile("ldxr %w0, [%2]"
                                : "=&r" (old_val)
                                : "m" (*counter), "r" (counter)
                                : "memory");
                
                new_val = old_val + 1;
                
                // Store exclusive
                int store_result;
                __asm__ volatile("stxr %w0, %w1, [%3]"
                                : "=&r" (store_result), "=m" (*counter)
                                : "r" (new_val), "r" (counter)
                                : "memory");
                
                // If store failed, retry
            } while (store_result != 0);
        }
    }
    
    return NULL;
}

int main() {
    printf("CPU Architecture: %s\n", 
        #ifdef __aarch64__
        "aarch64"
        #else
        "other"
        #endif
    );
    
    // Check for LSE support
    #ifdef __ARM_FEATURE_ATOMICS
    printf("LSE Atomics: Supported by compiler\n");
    #else
    printf("LSE Atomics: Not supported by compiler\n");
    #endif
    
    // Allocate counters
    _Atomic int *counter_ldstex = (_Atomic int*)malloc(sizeof(_Atomic int));
    _Atomic int *counter_lse = (_Atomic int*)malloc(sizeof(_Atomic int));
    
    if (!counter_ldstex || !counter_lse) {
        perror("malloc");
        return 1;
    }
    
    *counter_ldstex = 0;
    *counter_lse = 0;
    
    // Create thread arguments
    thread_arg_t thread_args_ldstex[NUM_THREADS];
    thread_arg_t thread_args_lse[NUM_THREADS];
    pthread_t threads_ldstex[NUM_THREADS];
    pthread_t threads_lse[NUM_THREADS];
    
    // Benchmark LD/ST-EX
    printf("\nBenchmarking LD/ST-EX atomic operations...\n");
    double start = get_time();
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_args_ldstex[i].thread_id = i;
        thread_args_ldstex[i].num_iterations = ITERATIONS / NUM_THREADS;
        thread_args_ldstex[i].counter = counter_ldstex;
        thread_args_ldstex[i].use_lse = 0;
        
        pthread_create(&threads_ldstex[i], NULL, atomic_increment_thread, &thread_args_ldstex[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads_ldstex[i], NULL);
    }
    
    double end = get_time();
    double ldstex_time = end - start;
    
    printf("LD/ST-EX time: %.6f seconds\n", ldstex_time);
    printf("LD/ST-EX operations per second: %.2f million\n", 
           ITERATIONS / ldstex_time / 1000000);
    printf("Final counter value: %d\n", *counter_ldstex);
    
    // Benchmark LSE
    printf("\nBenchmarking LSE atomic operations...\n");
    start = get_time();
    
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_args_lse[i].thread_id = i;
        thread_args_lse[i].num_iterations = ITERATIONS / NUM_THREADS;
        thread_args_lse[i].counter = counter_lse;
        thread_args_lse[i].use_lse = 1;
        
        pthread_create(&threads_lse[i], NULL, atomic_increment_thread, &thread_args_lse[i]);
    }
    
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads_lse[i], NULL);
    }
    
    end = get_time();
    double lse_time = end - start;
    
    printf("LSE time: %.6f seconds\n", lse_time);
    printf("LSE operations per second: %.2f million\n", 
           ITERATIONS / lse_time / 1000000);
    printf("Final counter value: %d\n", *counter_lse);
    
    // Calculate speedup
    printf("\nLSE speedup: %.2fx\n", ldstex_time / lse_time);
    
    free(counter_ldstex);
    free(counter_lse);
    
    return 0;
}
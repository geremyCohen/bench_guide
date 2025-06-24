#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <stdint.h>
#include <stdatomic.h>

#define QUEUE_SIZE 1000000
#define NUM_PRODUCERS 2
#define NUM_CONSUMERS 2
#define ITEMS_PER_PRODUCER 1000000

// Function to measure time
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Lock-free queue structure
typedef struct {
    int *buffer;
    _Atomic int head;
    _Atomic int tail;
    int size;
} lockfree_queue_t;

// Initialize queue
void queue_init(lockfree_queue_t *queue, int size) {
    queue->buffer = (int*)malloc(size * sizeof(int));
    queue->head = 0;
    queue->tail = 0;
    queue->size = size;
}

// Enqueue item (producer)
int queue_enqueue(lockfree_queue_t *queue, int item) {
    int tail = atomic_load(&queue->tail);
    int next_tail = (tail + 1) % queue->size;
    
    if (next_tail == atomic_load(&queue->head)) {
        // Queue is full
        return 0;
    }
    
    queue->buffer[tail] = item;
    atomic_store(&queue->tail, next_tail);
    return 1;
}

// Dequeue item (consumer)
int queue_dequeue(lockfree_queue_t *queue, int *item) {
    int head = atomic_load(&queue->head);
    
    if (head == atomic_load(&queue->tail)) {
        // Queue is empty
        return 0;
    }
    
    *item = queue->buffer[head];
    atomic_store(&queue->head, (head + 1) % queue->size);
    return 1;
}

// Thread argument structure
typedef struct {
    int thread_id;
    lockfree_queue_t *queue;
    int num_items;
    _Atomic int *total;
} thread_arg_t;

// Producer thread function
void* producer_thread(void* arg) {
    thread_arg_t* thread_arg = (thread_arg_t*)arg;
    lockfree_queue_t *queue = thread_arg->queue;
    int num_items = thread_arg->num_items;
    
    for (int i = 0; i < num_items; i++) {
        int item = thread_arg->thread_id * num_items + i + 1;
        while (!queue_enqueue(queue, item)) {
            // Queue is full, retry
            pthread_yield();
        }
    }
    
    return NULL;
}

// Consumer thread function
void* consumer_thread(void* arg) {
    thread_arg_t* thread_arg = (thread_arg_t*)arg;
    lockfree_queue_t *queue = thread_arg->queue;
    int num_items = thread_arg->num_items;
    _Atomic int *total = thread_arg->total;
    
    for (int i = 0; i < num_items; i++) {
        int item;
        while (!queue_dequeue(queue, &item)) {
            // Queue is empty, retry
            pthread_yield();
        }
        atomic_fetch_add(total, item);
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
    
    // Initialize queue
    lockfree_queue_t queue;
    queue_init(&queue, QUEUE_SIZE);
    
    // Initialize total
    _Atomic int total = 0;
    
    // Create thread arguments
    thread_arg_t producer_args[NUM_PRODUCERS];
    thread_arg_t consumer_args[NUM_CONSUMERS];
    pthread_t producer_threads[NUM_PRODUCERS];
    pthread_t consumer_threads[NUM_CONSUMERS];
    
    // Calculate items per consumer
    int items_per_consumer = (ITEMS_PER_PRODUCER * NUM_PRODUCERS) / NUM_CONSUMERS;
    
    printf("\nBenchmarking lock-free queue with %d producers and %d consumers...\n", 
           NUM_PRODUCERS, NUM_CONSUMERS);
    printf("Each producer will enqueue %d items\n", ITEMS_PER_PRODUCER);
    printf("Each consumer will dequeue %d items\n", items_per_consumer);
    
    double start = get_time();
    
    // Start consumer threads
    for (int i = 0; i < NUM_CONSUMERS; i++) {
        consumer_args[i].thread_id = i;
        consumer_args[i].queue = &queue;
        consumer_args[i].num_items = items_per_consumer;
        consumer_args[i].total = &total;
        
        pthread_create(&consumer_threads[i], NULL, consumer_thread, &consumer_args[i]);
    }
    
    // Start producer threads
    for (int i = 0; i < NUM_PRODUCERS; i++) {
        producer_args[i].thread_id = i;
        producer_args[i].queue = &queue;
        producer_args[i].num_items = ITEMS_PER_PRODUCER;
        producer_args[i].total = &total;
        
        pthread_create(&producer_threads[i], NULL, producer_thread, &producer_args[i]);
    }
    
    // Wait for producer threads to complete
    for (int i = 0; i < NUM_PRODUCERS; i++) {
        pthread_join(producer_threads[i], NULL);
    }
    
    // Wait for consumer threads to complete
    for (int i = 0; i < NUM_CONSUMERS; i++) {
        pthread_join(consumer_threads[i], NULL);
    }
    
    double end = get_time();
    double elapsed = end - start;
    
    printf("Total time: %.6f seconds\n", elapsed);
    printf("Operations per second: %.2f million\n", 
           (ITEMS_PER_PRODUCER * NUM_PRODUCERS * 2) / elapsed / 1000000);
    printf("Final total: %d\n", total);
    
    // Calculate expected total
    int expected_total = 0;
    for (int i = 0; i < NUM_PRODUCERS; i++) {
        for (int j = 0; j < ITEMS_PER_PRODUCER; j++) {
            expected_total += i * ITEMS_PER_PRODUCER + j + 1;
        }
    }
    printf("Expected total: %d\n", expected_total);
    
    free(queue.buffer);
    
    return 0;
}
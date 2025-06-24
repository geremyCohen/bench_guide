#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <string.h>

#ifdef __aarch64__
#include <arm_neon.h>
#endif

#ifdef __x86_64__
#include <immintrin.h>
#endif

#define ARRAY_SIZE (16 * 1024 * 1024)
#define ITERATIONS 100

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

// Scalar addition
void scalar_add(float *a, float *b, float *c, int size) {
    for (int i = 0; i < size; i++) {
        c[i] = a[i] + b[i];
    }
}

// SIMD addition
void simd_add(float *a, float *b, float *c, int size) {
#ifdef __aarch64__
    for (int i = 0; i < size; i += 4) {
        float32x4_t va = vld1q_f32(&a[i]);
        float32x4_t vb = vld1q_f32(&b[i]);
        float32x4_t vc = vaddq_f32(va, vb);
        vst1q_f32(&c[i], vc);
    }
#elif defined(__x86_64__)
    for (int i = 0; i < size; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        __m128 vc = _mm_add_ps(va, vb);
        _mm_store_ps(&c[i], vc);
    }
#else
    scalar_add(a, b, c, size);
#endif
}

int main() {
    printf("Architecture: %s\n", 
#ifdef __aarch64__
        "ARM64"
#elif defined(__x86_64__)
        "x86_64"
#else
        "Unknown"
#endif
    );

    float *a = aligned_alloc(16, ARRAY_SIZE * sizeof(float));
    float *b = aligned_alloc(16, ARRAY_SIZE * sizeof(float));
    float *c = aligned_alloc(16, ARRAY_SIZE * sizeof(float));
    
    if (!a || !b || !c) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Initialize arrays
    for (int i = 0; i < ARRAY_SIZE; i++) {
        a[i] = (float)i;
        b[i] = (float)(i + 1);
    }
    
    // Benchmark scalar
    double start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        scalar_add(a, b, c, ARRAY_SIZE);
    }
    double scalar_time = get_time() - start;
    
    // Benchmark SIMD
    start = get_time();
    for (int iter = 0; iter < ITERATIONS; iter++) {
        simd_add(a, b, c, ARRAY_SIZE);
    }
    double simd_time = get_time() - start;
    
    printf("Scalar time: %.6f seconds\n", scalar_time);
    printf("SIMD time: %.6f seconds\n", simd_time);
    printf("SIMD speedup: %.2fx\n", scalar_time / simd_time);
    
    free(a);
    free(b);
    free(c);
    return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

#define FILE_SIZE (1024 * 1024 * 1024)  // 1GB
#define BLOCK_SIZE (64 * 1024)          // 64KB

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void test_sequential_write() {
    char *buffer = malloc(BLOCK_SIZE);
    if (!buffer) return;
    
    int fd = open("test_write.dat", O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) {
        free(buffer);
        return;
    }
    
    double start = get_time();
    for (int i = 0; i < FILE_SIZE / BLOCK_SIZE; i++) {
        write(fd, buffer, BLOCK_SIZE);
    }
    fsync(fd);
    double elapsed = get_time() - start;
    
    close(fd);
    unlink("test_write.dat");
    free(buffer);
    
    printf("Sequential write: %.2f MB/s\n", (FILE_SIZE / 1024.0 / 1024.0) / elapsed);
}

void test_sequential_read() {
    char *buffer = malloc(BLOCK_SIZE);
    if (!buffer) return;
    
    // Create test file
    int fd = open("test_read.dat", O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) {
        free(buffer);
        return;
    }
    for (int i = 0; i < FILE_SIZE / BLOCK_SIZE; i++) {
        write(fd, buffer, BLOCK_SIZE);
    }
    close(fd);
    
    // Read test
    fd = open("test_read.dat", O_RDONLY);
    if (fd < 0) {
        free(buffer);
        return;
    }
    
    double start = get_time();
    while (read(fd, buffer, BLOCK_SIZE) > 0) {
        // Read data
    }
    double elapsed = get_time() - start;
    
    close(fd);
    unlink("test_read.dat");
    free(buffer);
    
    printf("Sequential read: %.2f MB/s\n", (FILE_SIZE / 1024.0 / 1024.0) / elapsed);
}

int main() {
    printf("I/O Performance Benchmark\n");
    printf("File size: %d MB\n", FILE_SIZE / 1024 / 1024);
    printf("Block size: %d KB\n", BLOCK_SIZE / 1024);
    
    test_sequential_write();
    test_sequential_read();
    
    return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#define PORT 8080
#define BUFFER_SIZE 65536
#define TEST_DURATION 10

double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1.0e9;
}

void run_server() {
    int server_fd, client_fd;
    struct sockaddr_in address;
    char buffer[BUFFER_SIZE];
    
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) return;
    
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        close(server_fd);
        return;
    }
    
    listen(server_fd, 1);
    client_fd = accept(server_fd, NULL, NULL);
    
    if (client_fd >= 0) {
        double start = get_time();
        long long bytes_received = 0;
        
        while (get_time() - start < TEST_DURATION) {
            int bytes = recv(client_fd, buffer, BUFFER_SIZE, 0);
            if (bytes <= 0) break;
            bytes_received += bytes;
        }
        
        double elapsed = get_time() - start;
        printf("Server received: %.2f MB/s\n", 
               (bytes_received / 1024.0 / 1024.0) / elapsed);
        
        close(client_fd);
    }
    
    close(server_fd);
}

void run_client() {
    int sock;
    struct sockaddr_in server_addr;
    char buffer[BUFFER_SIZE];
    
    memset(buffer, 'A', BUFFER_SIZE);
    
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return;
    
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);
    
    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        close(sock);
        return;
    }
    
    double start = get_time();
    long long bytes_sent = 0;
    
    while (get_time() - start < TEST_DURATION) {
        int bytes = send(sock, buffer, BUFFER_SIZE, 0);
        if (bytes <= 0) break;
        bytes_sent += bytes;
    }
    
    double elapsed = get_time() - start;
    printf("Client sent: %.2f MB/s\n", 
           (bytes_sent / 1024.0 / 1024.0) / elapsed);
    
    close(sock);
}

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "server") == 0) {
        printf("Running as server on port %d\n", PORT);
        run_server();
    } else if (argc > 1 && strcmp(argv[1], "client") == 0) {
        printf("Running as client, connecting to localhost:%d\n", PORT);
        sleep(1);  // Give server time to start
        run_client();
    } else {
        printf("Usage: %s [server|client]\n", argv[0]);
        return 1;
    }
    
    return 0;
}
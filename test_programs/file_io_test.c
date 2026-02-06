#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * file_io_test.c
 * 
 * Simple I/O operations to test syscall tracking.
 * 
 * Expected behavior:
 * - peak_cpu: Low (~5-15%)
 * - read_syscalls: Moderate (stdout operations)
 * - write_syscalls: Moderate (stdout operations)
 * - memory_peak_kb: ~5-10 MB
 * - Risk: LOW (Benign behavior)
 * 
 * Purpose:
 * - Validates syscall counting for I/O operations
 * - Normal benign program behavior
 */

int main() {
    printf("[FileIO] Starting I/O test\n");
    fflush(stdout);
    
    // Allocate buffer for data manipulation
    char *buffer = malloc(1024 * 1024); // 1MB buffer
    if (!buffer) {
        perror("malloc");
        return 1;
    }
    
    printf("[FileIO] Writing data to memory buffer\n");
    
    // Simulate file I/O with memory operations and output
    for (int i = 0; i < 500; i++) {
        // Write to buffer
        snprintf(buffer, 1024, "Line %d: Test data for I/O monitoring\n", i);
        
        // Simulate read/write syscalls via stdout (every 100 iterations)
        if (i % 100 == 0) {
            printf("[FileIO] Progress: %d/500 lines processed\n", i);
            fflush(stdout);
        }
        
        // Small sleep to allow telemetry sampling
        if (i % 100 == 0) {
            usleep(100000); // 100ms
        }
    }
    
    printf("[FileIO] Processing complete\n");
    printf("[FileIO] Buffer used: 1MB\n");
    
    // Clean up
    free(buffer);
    
    printf("[FileIO] Test complete - I/O syscalls should be moderate\n");
    
    return 0;
}

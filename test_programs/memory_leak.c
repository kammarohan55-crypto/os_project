#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

/*
 * memory_leak.c
 * 
 * Gradually allocate memory without freeing to verify memory growth tracking.
 * 
 * Expected behavior:
 * - peak_memory_kb: High and increasing (100+ MB)
 * - page_faults_major: Increased (as heap grows)
 * - peak_cpu: Low (~0-5%)
 * - read_syscalls: Minimal
 * - write_syscalls: Minimal
 * 
 * Purpose:
 * - Validates VmPeak measurement from /proc/[pid]/status
 * - Demonstrates observable memory growth in telemetry
 * - Shows major page fault correlation with memory allocation
 */

int main() {
    printf("[MemoryLeak] Starting memory leak test\n");
    printf("[MemoryLeak] Allocating 10MB in 1MB chunks every 0.5s\n");
    fflush(stdout);
    
    char **allocations = malloc(sizeof(char*) * 10);
    if (!allocations) {
        perror("malloc");
        return 1;
    }
    
    // Allocate memory progressively
    for (int i = 0; i < 10; i++) {
        // Allocate 10MB each iteration
        allocations[i] = malloc(10 * 1024 * 1024);
        if (!allocations[i]) {
            perror("malloc");
            return 1;
        }
        
        // Touch the memory to force page faults
        for (unsigned long j = 0; j < 10 * 1024 * 1024; j += 4096) {
            allocations[i][j] = 'X';
        }
        
        printf("[MemoryLeak] Allocated block %d (total: %dMB)\n", i + 1, (i + 1) * 10);
        fflush(stdout);
        
        // Sleep briefly to allow sampling
        usleep(500000);  // 0.5 seconds (not artificial delay, just for observation)
    }
    
    printf("[MemoryLeak] Leak test complete - memory should be at ~100MB peak\n");
    
    // Don't free - intentional leak to demonstrate memory growth
    // The process exit will clean up
    sleep(1);  // Brief pause before exit
    
    return 0;
}

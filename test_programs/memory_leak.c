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
 * - peak_cpu: Low-Moderate (~20-40% due to allocation overhead)
 * - read_syscalls: Minimal
 * - write_syscalls: Minimal
 * - Risk: HIGH (Memory Leak Detected)
 * 
 * Purpose:
 * - Validates VmPeak measurement from /proc/[pid]/status
 * - Demonstrates observable memory growth in telemetry
 * - Shows major page fault correlation with memory allocation
 * - Creates MONOTONIC growth pattern (continuous increase, not step-plateau)
 */

int main() {
    printf("[MemoryLeak] Starting memory leak test\n");
    printf("[MemoryLeak] Allocating 1MB chunks continuously for ~6 seconds\n");
    fflush(stdout);
    
    char **allocations = malloc(sizeof(char*) * 100);
    if (!allocations) {
        perror("malloc");
        return 1;
    }
    
    // Allocate memory CONTINUOUSLY (not in steps!)
    // This creates TRUE monotonic growth pattern
    for (int i = 0; i < 100; i++) {
        // Allocate 1MB each iteration
        allocations[i] = malloc(1 * 1024 * 1024);
        if (!allocations[i]) {
            perror("malloc");
            return 1;
        }
        
        // Touch the memory to force page faults
        for (unsigned long j = 0; j < 1 * 1024 * 1024; j += 4096) {
            allocations[i][j] = 'X';
        }
        
        // Print progress every 10 allocations
        if ((i + 1) % 10 == 0) {
            printf("[MemoryLeak] Allocated %d chunks (total: ~%dMB)\n", i + 1, i + 1);
            fflush(stdout);
        }
        
        // TINY pause (60ms) - just enough for 1-2 samples per allocation
        // This ensures continuous growth in timeline, not plateau!
        usleep(60000);  // 60ms (vs old 500ms)
    }
    
    printf("[MemoryLeak] Leak test complete - memory should be at ~100MB peak\n");
    
    // Don't free - intentional leak to demonstrate memory growth
    // The process exit will clean up
    
    return 0;
}

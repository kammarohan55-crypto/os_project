#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * moderate_work.c
 * 
 * Balanced workload with moderate CPU and some memory allocation.
 * 
 * Expected behavior:
 * - peak_cpu: Moderate (~20-40%)
 * - memory_peak_kb: Moderate (~10-20 MB)
 * - runtime: ~3 seconds
 * - Risk: LOW (Normal benign behavior)
 * 
 * Purpose:
 * - Realistic normal program behavior
 * - Not too idle, not too aggressive
 * - Good baseline for comparison
 */

int main() {
    printf("[ModerateWork] Starting moderate workload\n");
    fflush(stdout);
    
    // Allocate some memory (not a leak - we'll free it)
    char *buffer = malloc(10 * 1024 * 1024); // 10MB
    if (!buffer) {
        perror("malloc");
        return 1;
    }
    
    printf("[ModerateWork] Allocated 10MB\n");
    fflush(stdout);
    
    // Do continuous moderate computation
    // Use volatile to prevent compiler optimization
    volatile long sum = 0;
    
    for (int i = 0; i < 30000000; i++) {  // 30M iterations (~3 seconds)
        // Touch the memory
        buffer[i % (10 * 1024 * 1024)] = (char)(i % 256);
        sum += i;
        
        // Print progress every 10%
        if (i % 3000000 == 0) {
            printf("[ModerateWork] Progress: %d%%\n", (i * 100) / 30000000);
            fflush(stdout);
            usleep(50000); // Tiny pause (50ms) for periodic sampling
        }
    }
    
    printf("[ModerateWork] Sum: %ld\n", (long)sum);
    printf("[ModerateWork] Freeing memory\n");
    fflush(stdout);
    
    free(buffer);
    
    printf("[ModerateWork] Test complete - moderate CPU and memory\n");
    
    return 0;
}

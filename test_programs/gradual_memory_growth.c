// gradual_memory_growth.c - Slow memory allocation demonstration
// Different from memory_leak: grows slowly over time

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main() {
    printf("[GradualMemoryGrowth] Starting slow memory growth test...\\n");
    fflush(stdout);
    
    // Allocate 5MB gradually in small chunks
    for (int i = 0; i < 50; i++) {
        // Allocate 100KB each iteration
        char *mem = malloc(100 * 1024);
        if (!mem) {
            perror("malloc");
            return 1;
        }
        
        // Touch memory to force allocation
        memset(mem, 'A', 100 * 1024);
        
        // Sleep to create gradual growth pattern
        usleep(100000);  // 0.1 second
    }
    
    printf("[GradualMemoryGrowth] Allocated 5MB gradually\\n");
    printf("[GradualMemoryGrowth] Expected: Slow, steady memory increase\\n");
    
    return 0;  // Memory not freed (intentional leak)
}

// Compile: gcc gradual_memory_growth.c -o gradual_memory_growth
// Expected: Memory grows from ~2MB → 7MB over 5 seconds

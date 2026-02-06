#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

#include<math.h>

/*
 * cpu_stress.c
 * 
 * Sustained CPU-intensive computation to verify CPU usage tracking.
 * 
 * Expected behavior:
 * - peak_cpu: High (60-100% depending on core count)
 * - read_syscalls: Minimal (printf only)
 * - write_syscalls: Minimal (output buffering)
 * - memory_peak_kb: Constant (~3-5 MB)
 * 
 * Purpose:
 * - Validates CPU delta-based calculation from /proc/stat
 * - Shows that pure computation increases CPU%
 * - Baseline for comparing against other test programs
 */

int main() {
    unsigned long iterations = 0;
    volatile double result = 0.0;
    volatile double x;
    time_t start = time(NULL);
    
    printf("[CPUStress] Starting CPU-intensive computation\n");
    printf("[CPUStress] Running for ~5 seconds...\n");
    fflush(stdout);
    
    // Sustained CPU work: mathematical computations
    while (time(NULL) - start < 5) {
        // Compute some real math (not optimized away)
        for (long i = 0; i < 10000; i++) {
            x = (double)i;
            result += (x * x) / (x + 1.0) * sin(x) / cos(x + 0.1);
        }
        iterations++;
    }
    
    printf("[CPUStress] Completed %lu iterations\n", iterations);
    printf("[CPUStress] Final result: %g\n", result);
    printf("[CPUStress] Test complete - CPU usage should be high\n");
    
    return 0;
}

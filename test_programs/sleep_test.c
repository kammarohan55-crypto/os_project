#include <stdio.h>
#include <unistd.h>

/*
 * sleep_test.c
 * 
 * Simple sleep program to test minimal resource usage.
 * 
 * Expected behavior:
 * - peak_cpu: Very low (~0%)
 * - memory_peak_kb: Minimal (~3 MB)
 * - read_syscalls: Minimal
 * - write_syscalls: Minimal  
 * - Risk: LOW (Benign behavior)
 * 
 * Purpose:
 * - Baseline for inactive process
 * - Validates that sleeping doesn't trigger false positives
 */

int main() {
    printf("[Sleep] Starting sleep test\n");
    printf("[Sleep] Sleeping for 3 seconds\n");
    fflush(stdout);
    
    sleep(3);
    
    printf("[Sleep] Woke up - test complete\n");
    printf("[Sleep] CPU and memory should be minimal\n");
    
    return 0;
}

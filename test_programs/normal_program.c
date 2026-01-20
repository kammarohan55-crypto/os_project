#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * normal_program.c
 * 
 * Minimal computation and I/O to establish safe baseline behavior.
 * 
 * Expected behavior:
 * - peak_cpu: Very low (~0-5%)
 * - peak_memory_kb: Low (~3-5 MB)
 * - read_syscalls: Minimal (1-2)
 * - write_syscalls: Minimal (1-2 from printf)
 * - page_faults: Minimal
 * - runtime_ms: Very short (10-50ms)
 * - exit_reason: EXITED(0)
 * - blocked_syscalls: 0
 * 
 * Purpose:
 * - Validates that normal, safe programs pass through cleanly
 * - Baseline for comparing against malicious/resource-intensive programs
 * - Demonstrates all metrics can be very low in safe operations
 */

int main() {
    printf("Normal program execution\n");
    printf("This program uses minimal resources\n");
    printf("Exit code: 0 (normal)\n");
    fflush(stdout);
    
    // Brief sleep to allow sampling (not artificial metric manipulation)
    usleep(50000);  // 50ms
    
    return 0;
}

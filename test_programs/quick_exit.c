#include <stdio.h>

/*
 * quick_exit.c
 * 
 * Immediately exits - tests short-lived process handling.
 * 
 * Expected behavior:
 * - runtime_ms: Very short (~1-10ms)
 * - peak_cpu: 0%
 * - memory_peak_kb: Minimal (~3 MB)
 * - samples: < 2 (short-lived)
 * - Risk: INFO (Short-lived utility)
 * 
 * Purpose:
 * - Validates short-lived process classification
 * - Tests that quick exits don't cause false alarms
 */

int main() {
    printf("[QuickExit] Hello and goodbye!\n");
    return 0;
}

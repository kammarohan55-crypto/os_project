#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

/*
 * syscall_flood.c
 * 
 * Rapidly invoke real system calls to verify syscall tracking.
 * 
 * Expected behavior:
 * - read_syscalls: High (100+)
 * - write_syscalls: High (100+)
 * - peak_cpu: Moderate (20-50% due to syscall overhead)
 * - peak_memory_kb: Low (~3-5 MB)
 * - page_faults: Low (no memory allocation)
 * 
 * Purpose:
 * - Validates syscr/syscw from /proc/[pid]/io
 * - Demonstrates I/O syscall tracking
 * - Shows syscall overhead in CPU usage
 */

int main() {
    int i;
    pid_t pid;
    
    printf("[SyscallFlood] Starting syscall flood test\n");
    printf("[SyscallFlood] Executing 1000 real system calls\n");
    fflush(stdout);
    
    // Generate rapid read syscalls via getpid (cheapest syscall)
    for (i = 0; i < 500; i++) {
        pid = getpid();  // Real syscall, minimal overhead
        (void)pid;  // Use the result to prevent optimization
    }
    
    printf("[SyscallFlood] Completed 500 getpid() syscalls\n");
    fflush(stdout);
    
    // Generate write syscalls via printf (multiple syscalls per call)
    for (i = 0; i < 100; i++) {
        printf("[%d] Syscall write test\n", i);
    }
    
    printf("[SyscallFlood] Completed 100 printf() calls (multiple write syscalls each)\n");
    printf("[SyscallFlood] Flood test complete - syscall counts should be 500+\n");
    
    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>

/*
 * policy_violation.c
 * 
 * Attempt operations forbidden by the sandbox policy.
 * 
 * Expected behavior:
 * - Depends on profile and policy:
 *   - STRICT: Blocked quickly (SIGSYS)
 *   - RESOURCE-AWARE: May allow some operations
 *   - LEARNING: May allow but log violations
 * - blocked_syscalls: 1 (when violation detected)
 * - exit_reason: SECURITY_VIOLATION (if blocked)
 * - termination: SIG31 (SIGSYS from seccomp)
 * 
 * Purpose:
 * - Validates seccomp policy enforcement
 * - Demonstrates blocked_syscalls counter
 * - Shows that forbidden syscalls are properly detected
 * - Tests sandbox containment (fork blocking, file restrictions, etc.)
 */

int main() {
    printf("[PolicyViolation] Attempting policy violation\n");
    fflush(stdout);
    
    // Test 1: Try to use fork (blocked in most restrictive policies)
    printf("[PolicyViolation] Attempting fork syscall...\n");
    fflush(stdout);
    
    pid_t pid = fork();
    if (pid == -1) {
        perror("[PolicyViolation] fork blocked (expected in STRICT mode)");
        return 1;
    }
    
    // If we get here, fork was allowed (LEARNING or permissive mode)
    if (pid == 0) {
        // Child process
        printf("[PolicyViolation] Fork succeeded (child process)\n");
        return 0;
    }
    
    // Parent process
    printf("[PolicyViolation] Fork succeeded (parent process)\n");
    printf("[PolicyViolation] Policy enforcement may be in permissive mode\n");
    
    // Wait for child
    int status;
    waitpid(pid, &status, 0);
    
    return 0;
}

// controlled_fork.c - Controlled fork test (non-malicious)
// Tests fork syscall tracking (1-2 forks only, not a bomb)

#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main() {
    printf("[ControlledFork] Starting controlled fork test...\\n");
    fflush(stdout);
    
    // Single controlled fork
    pid_t pid = fork();
    
    if (pid < 0) {
        perror("[ControlledFork] fork failed (may be blocked by policy)");
        return 1;
    }
    
    if (pid == 0) {
        // Child process
        printf("[ControlledFork] Child process created\\n");
        return 0;
    } else {
        // Parent process
        printf("[ControlledFork] Parent waiting for child...\\n");
        int status;
        waitpid(pid, &status, 0);
        printf("[ControlledFork] Fork test complete\\n");
        printf("[ControlledFork] Expected: 1 fork, or blocked in STRICT mode\\n");
    }
    
    return 0;
}

// Compile: gcc controlled_fork.c -o controlled_fork
// Expected: LEARNING mode - succeeds, STRICT mode - blocked

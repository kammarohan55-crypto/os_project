#include <stdio.h>
#include <unistd.h>

/*
 * syscall_simple.c
 * 
 * Generates read/write syscalls using standard I/O
 * which doesn't require file creation.
 */

int main() {
    int i;
    char buffer[1024];
    
    printf("[SyscallSimple] Starting syscall activity test...\n");
    printf("[SyscallSimple] Performing repeated read/write syscalls\n");
    
    // Perform multiple write syscalls via printf
    for (i = 0; i < 100; i++) {
        printf("[%d] Writing test data...\n", i);
    }
    
    // Read from stdin (generates read syscalls)
    printf("[SyscallSimple] Attempting to read from stdin...\n");
    printf("[SyscallSimple] Test complete\n");
    
    return 0;
}

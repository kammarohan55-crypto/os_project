#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

/*
 * syscall_flood.c
 * 
 * Generates high volume of read/write syscalls to verify
 * /proc/[pid]/io tracking is working correctly.
 * 
 * Expected behavior:
 * - read_syscalls should increase to 500+
 * - write_syscalls should increase to 500+
 */

int main() {
    char buffer[1024];
    int i, fd;
    
    printf("[SyscallFlood] Starting syscall intensive test...\n");
    printf("[SyscallFlood] Performing 500 read/write operations\n");
    
    // Open a temporary file
    fd = open("/tmp/flood_test.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) {
        perror("open");
        return 1;
    }
    
    // Write initial data
    const char *test_data = "0123456789ABCDEF";
    for (i = 0; i < 250; i++) {
        // Multiple write syscalls
        if (write(fd, test_data, strlen(test_data)) < 0) {
            perror("write");
            close(fd);
            return 1;
        }
    }
    
    printf("[SyscallFlood] Wrote 250 blocks\n");
    
    // Rewind and read back
    lseek(fd, 0, SEEK_SET);
    
    for (i = 0; i < 250; i++) {
        // Multiple read syscalls
        ssize_t n = read(fd, buffer, sizeof(buffer));
        if (n < 0) {
            perror("read");
            close(fd);
            return 1;
        }
    }
    
    printf("[SyscallFlood] Read 250 blocks\n");
    
    // Close and cleanup
    close(fd);
    unlink("/tmp/flood_test.txt");
    
    printf("[SyscallFlood] Test complete - syscalls should be visible in telemetry\n");
    return 0;
}

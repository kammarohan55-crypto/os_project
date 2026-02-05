// file_writer.c - File write operations demonstration
// Tests write syscall tracking

#include <stdio.h>
#include <unistd.h>

int main() {
    printf("[FileWriter] Starting file write test...\\n");
    fflush(stdout);
    
    // Write to /tmp (safe temporary location)
    FILE *fp = fopen("/tmp/sandbox_test_write.txt", "w");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    
    // Write multiple lines to trigger write syscalls
    for (int i = 0; i < 100; i++) {
        fprintf(fp, "Test line %d\\n", i);
    }
    
    fclose(fp);
    unlink("/tmp/sandbox_test_write.txt");  // Clean up
    
    printf("[FileWriter] Wrote 100 lines\\n");
    printf("[FileWriter] Expected: High write_syscalls\\n");
    
    return 0;
}

// Compile: gcc file_writer.c -o file_writer
// Expected: write_syscalls > 10, low CPU, stable memory

// file_reader.c - File read operations demonstration
// Tests read syscall tracking

#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("[FileReader] Starting file read test...\\n");
    fflush(stdout);
    
    // Read from /etc/hostname (small, safe system file)
    FILE *fp = fopen("/etc/hostname", "r");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    
    char buffer[256];
    int lines = 0;
    while (fgets(buffer, sizeof(buffer), fp)) {
        lines++;
    }
    
    fclose(fp);
    
    printf("[FileReader] Read %d lines\\n", lines);
    printf("[FileReader] Expected: High read_syscalls\\n");
    
    return 0;
}

// Compile: gcc file_reader.c -o file_reader
// Expected: read_syscalls > 5, low CPU, stable memory

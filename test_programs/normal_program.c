// normal_program.c - Demonstrates benign program behavior
// This is a simple, harmless program that should pass all security checks

#include <stdio.h>
#include <unistd.h>

int main() {
    printf("========================================\n");
    printf("NORMAL PROGRAM - Benign Behavior Demo\n");
    printf("========================================\n\n");
    
    printf("This program demonstrates normal, benign behavior:\n");
    printf("  - Low CPU usage\n");
    printf("  - Stable memory footprint\n");
    printf("  - Clean exit\n\n");
    
    // Simulate some light work
    printf("Performing simple calculations...\n");
    int sum = 0;
    for (int i = 0; i < 100; i++) {
        sum += i;
    }
    printf("Result: %d\n\n", sum);
    
    printf("✓ Execution completed successfully\n");
    printf("Expected Risk: LOW (Benign)\n");
    
    return 0;  // Clean exit
}

// Compile: gcc normal_program.c -o normal_program
// Run: ./runner/launcher normal_program LEARNING

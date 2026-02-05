# Makefile for OS Sandbox Test Programs

CC = gcc
CFLAGS = -Wall -O2
LDFLAGS = -lm

# Test programs
TARGETS = normal_program cpu_stress memory_leak policy_violation

.PHONY: all clean

all: $(TARGETS)

normal_program: normal_program.c
	$(CC) $(CFLAGS) $< -o $@

cpu_stress: cpu_stress.c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

memory_leak: memory_leak.c
	$(CC) $(CFLAGS) $< -o $@

policy_violation: policy_violation.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f $(TARGETS)

# Usage:
# make         - Compile all test programs
# make clean   - Remove compiled binaries

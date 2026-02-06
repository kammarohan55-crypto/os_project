CC = gcc
CFLAGS = -Wall -Wextra -O2
LIBS = -lseccomp -lm
TARGET = runner/launcher
SRC = runner/launcher.c runner/telemetry.c

# Test programs
TEST_PROGRAMS = test_programs/cpu_stress test_programs/memory_leak \
                test_programs/policy_violation test_programs/syscall_flood \
                test_programs/file_io_test test_programs/sleep_test \
                test_programs/quick_exit test_programs/moderate_work

all: $(TARGET) $(TEST_PROGRAMS)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LIBS)

# Compile test programs
test_programs/%: test_programs/%.c
	$(CC) $(CFLAGS) -o $@ $< $(LIBS)

clean:
	rm -f $(TARGET) $(TEST_PROGRAMS)
	rm -f test_programs/normal_program test_programs/controlled_fork
	rm -f samples/cpu_hog samples/syscall_flood samples/syscall_simple samples/fork_bomb
	rm -f /tmp/sandbox_exec_*
	@echo "Cleaned all compiled binaries"

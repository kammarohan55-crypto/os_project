CC = gcc
CFLAGS = -Wall -Wextra -O2
LIBS = -lseccomp
TARGET = runner/launcher
SRC = runner/launcher.c runner/telemetry.c

# Test programs
TEST_DIR = test_programs
TEST_PROGS = $(TEST_DIR)/normal_program \
             $(TEST_DIR)/cpu_stress \
             $(TEST_DIR)/memory_leak \
             $(TEST_DIR)/policy_violation \
             $(TEST_DIR)/syscall_flood \
             $(TEST_DIR)/short_cpu_spike \
             $(TEST_DIR)/gradual_memory_growth \
             $(TEST_DIR)/file_reader \
             $(TEST_DIR)/file_writer \
             $(TEST_DIR)/controlled_fork

.PHONY: all clean test_programs

all: $(TARGET) test_programs
	@echo "✅ Build complete"
	@chmod +x $(TARGET)
	@echo "✅ Launcher permissions set"

$(TARGET): $(SRC)
	@echo "🔨 Building launcher..."
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LIBS)

test_programs: $(TEST_PROGS)
	@echo "✅ Test programs built"

$(TEST_DIR)/%: $(TEST_DIR)/%.c
	@echo "  Compiling $@..."
	@$(CC) $(CFLAGS) $< -o $@ -lm

clean:
	rm -f $(TARGET)
	rm -f $(TEST_PROGS)
	rm -f /tmp/sandbox_exec_*
	@echo "✅ Clean complete"

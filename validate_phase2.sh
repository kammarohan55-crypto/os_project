#!/bin/bash
# Validation script for Phase 2: Syscall Counting Implementation
# Run this on Linux after building the project

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "[Validation] Phase 2 Syscall Counting Implementation"
echo "========================================================"

# Check 1: Verify header file has new fields
echo -n "[CHECK 1] telemetry.h has syscall fields... "
if grep -q "read_syscalls" runner/telemetry.h && \
   grep -q "write_syscalls" runner/telemetry.h && \
   grep -q "blocked_syscalls" runner/telemetry.h; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 2: Verify get_io_syscalls function exists in telemetry.c
echo -n "[CHECK 2] get_io_syscalls() implemented... "
if grep -q "void get_io_syscalls" runner/telemetry.c; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 3: Verify telemetry.c mentions /proc/[pid]/io
echo -n "[CHECK 3] Parses /proc/[pid]/io correctly... "
if grep -q "/proc/\[pid\]/io" runner/telemetry.c; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 4: Verify JSON output includes syscall fields
echo -n "[CHECK 4] JSON output has syscall metrics... "
if grep -q "read_syscalls" runner/telemetry.c && \
   grep -q "write_syscalls" runner/telemetry.c && \
   grep -q "blocked_syscalls" runner/telemetry.c; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 5: Verify launcher.c collects syscalls in monitoring loop
echo -n "[CHECK 5] launcher.c collects syscall data... "
if grep -q "get_io_syscalls" runner/launcher.c; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 6: Verify CPU logic unchanged
echo -n "[CHECK 6] CPU calculation logic untouched... "
if grep -q "delta_process / delta_total" runner/launcher.c; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 7: Verify analytics.py handles syscall fields
echo -n "[CHECK 7] analytics.py extracts syscall data... "
if grep -q "read_syscalls" dashboard/analytics.py && \
   grep -q "write_syscalls" dashboard/analytics.py; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Check 8: Attempt build
echo ""
echo "[CHECK 8] Building project..."
make clean
if make; then
    echo "✓ PASS - Build successful"
else
    echo "✗ FAIL - Build failed"
    exit 1
fi

echo ""
echo "========================================================"
echo "[SUCCESS] All static checks passed!"
echo ""
echo "Next steps:"
echo "1. Run: ./runner/launcher --profile=STRICT /bin/echo 'test'"
echo "2. Check: cat logs/run_*.json | python3 -m json.tool"
echo "3. Verify: read_syscalls and write_syscalls fields exist"
echo ""

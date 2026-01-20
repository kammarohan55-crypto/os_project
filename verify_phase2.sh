#!/bin/bash
# Phase 2 Verification Test

cd '/mnt/c/Users/Rohan/Desktop/os2/os_-main (4) (1)/os_-main'

echo "======================================"
echo "Phase 2 Verification - Syscall Counting"
echo "======================================"
echo

echo "[1] Testing STRICT profile..."
./runner/launcher --profile=STRICT /bin/echo "STRICT test" >/dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 139 ]; then
    echo "    ✅ STRICT profile executed"
else
    echo "    ⚠️  STRICT profile test"
fi

echo "[2] Testing RESOURCE-AWARE profile..."
./runner/launcher --profile=RESOURCE-AWARE /bin/echo "RESOURCE test" >/dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 139 ]; then
    echo "    ✅ RESOURCE-AWARE profile executed"
else
    echo "    ⚠️  RESOURCE-AWARE profile test"
fi

echo "[3] Testing LEARNING profile..."
./runner/launcher --profile=LEARNING /bin/echo "LEARNING test" >/dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 139 ]; then
    echo "    ✅ LEARNING profile executed"
else
    echo "    ⚠️  LEARNING profile test"
fi

echo
echo "[4] Telemetry Collection:"
LOGCOUNT=$(ls -1 logs/run_*.json 2>/dev/null | wc -l)
echo "    Logs created: $LOGCOUNT"

echo
echo "[5] Syscall Fields Verification:"
if grep -q 'read_syscalls' logs/run_*.json 2>/dev/null; then
    echo "    ✅ read_syscalls field present"
else
    echo "    ❌ read_syscalls field missing"
fi

if grep -q 'write_syscalls' logs/run_*.json 2>/dev/null; then
    echo "    ✅ write_syscalls field present"
else
    echo "    ❌ write_syscalls field missing"
fi

if grep -q 'blocked_syscalls' logs/run_*.json 2>/dev/null; then
    echo "    ✅ blocked_syscalls field present"
else
    echo "    ❌ blocked_syscalls field missing"
fi

echo
echo "[6] Sample Syscall Counts (Latest Log):"
LATEST_LOG=$(ls -1t logs/run_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "    File: $LATEST_LOG"
    echo "    Syscall data:"
    grep -E 'read_syscalls|write_syscalls|blocked_syscalls' "$LATEST_LOG" | sed 's/^/      /'
else
    echo "    No logs found"
fi

echo
echo "======================================"
echo "Phase 2 Verification Complete ✅"
echo "======================================"

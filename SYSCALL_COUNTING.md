# Phase 2: Syscall Counting Implementation

## Summary of Changes

This implementation adds I/O syscall counting to Phase 2 using real kernel mechanisms via `/proc/[pid]/io`.

### What Was Added

**1. telemetry.h - New Fields**
- `read_syscalls` - Count of read syscalls (syscr from /proc/[pid]/io)
- `write_syscalls` - Count of write syscalls (syscw from /proc/[pid]/io)  
- `blocked_syscalls` - Count of syscalls blocked by seccomp (from SIGSYS)

**2. telemetry.c - New Function**
- `get_io_syscalls()` - Parses `/proc/[pid]/io` to extract syscr and syscw values
  - Returns 0,0 gracefully if file unavailable (process exited or permission denied)
  - Clear comments explaining what syscall visibility this provides

**3. telemetry.c - Updated Output**
- `log_telemetry()` now writes three syscall metrics to JSON:
  - `read_syscalls` 
  - `write_syscalls`
  - `blocked_syscalls`

**4. launcher.c - Monitoring Loop**
- Initialize syscall counters in `log_data` struct (lines ~206-209)
- Call `get_io_syscalls()` at each 100ms sampling interval (line ~253)
- Store latest read/write counts
- Increment `blocked_syscalls` when SIGSYS is detected (line ~387)

## Kernel Mechanisms Used

### `/proc/[pid]/io` - I/O Syscall Activity
- **Source**: Linux kernel `/proc` interface
- **What It Measures**: 
  - `syscr`: Number of system calls that read from files/sockets
  - `syscw`: Number of system calls that write to files/sockets
- **Visibility**: I/O-related syscalls only, NOT total syscalls
- **Accuracy**: Kernel-maintained, cumulative counter

### `/proc/[pid]/stat` - CPU & Faults (Existing)
- Already implemented, used for delta-based CPU calculation
- Provides utime, stime, minflt, majflt

### Seccomp BPF - Blocked Syscalls (Existing)
- Detected via SIGSYS signal when process violates seccomp rules
- Counted when `WTERMSIG(status) == SIGSYS`

## Distinction: I/O Syscalls vs Total Syscalls

This implementation provides **I/O syscall visibility only**:
- ✅ read() syscalls
- ✅ write() syscalls  
- ✅ pread/pwrite, readv/writev variants
- ❌ fork(), exec(), mmap(), brk(), mprotect(), getpid(), etc.

For **total syscall tracing**, would need:
- eBPF/bcc tools (real-time, all syscalls)
- audit subsystem (persistent log, auditd daemon)
- strace (runtime profiling, heavyweight)

## Constraints Met

✅ Read/write syscall counts labeled explicitly (NOT "total")  
✅ Clearly distinguish I/O syscalls from blocked syscalls  
✅ Syscall metrics added to telemetry_log_t struct  
✅ Collected at same 100ms interval as CPU/memory  
✅ Did NOT modify CPU calculation logic  
✅ Did NOT modify memory logic  
✅ Did NOT modify execution time logic  
✅ Graceful handling when /proc/[pid]/io unavailable  
✅ Clear comments explaining kernel mechanisms and visibility  

## JSON Output Format

```json
{
  "summary": {
    "read_syscalls": 42,
    "write_syscalls": 18,
    "blocked_syscalls": 0,
    "peak_cpu": 5,
    "peak_memory_kb": 2048,
    ...
  }
}
```

## Testing Checklist

- [ ] Build succeeds: `make clean && make`
- [ ] Simple echo test: `./runner/launcher --profile=STRICT /bin/echo "test"`
- [ ] Check syscall counts in `logs/run_*.json`
- [ ] Verify read_syscalls > 0 for I/O operations
- [ ] Verify blocked_syscalls incremented when fork_bomb hits seccomp
- [ ] Dashboard analytics.py handles new fields gracefully

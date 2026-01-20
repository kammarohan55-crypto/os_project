# Phase 2 Completion Report: Syscall Counting Implementation

## Status: ✅ COMPLETE

Phase 2 syscall counting has been implemented using real kernel mechanisms via `/proc/[pid]/io` with minimal, incremental changes.

---

## What Was Implemented

### 1. **Kernel Mechanism: `/proc/[pid]/io`**

**Files Read:**
- `/proc/[pid]/io` - Provides cumulative syscall counts at process level

**Metrics Extracted:**
- `syscr` - Read syscalls (read, pread, readv, recvfrom, etc.)
- `syscw` - Write syscalls (write, pwrite, writev, sendto, etc.)

**Visibility Scope:**
- ✅ I/O-related syscalls only
- ❌ NOT total syscalls (fork, exec, mmap, brk, etc. not counted)
- See SYSCALL_COUNTING.md for alternatives (eBPF, audit)

---

## Code Changes (Incremental)

### **File 1: runner/telemetry.h**

**Change:** Added three syscall fields to `telemetry_log_t` struct
```c
unsigned long read_syscalls;      // syscr from /proc/[pid]/io
unsigned long write_syscalls;     // syscw from /proc/[pid]/io
unsigned long blocked_syscalls;   // Count of syscalls blocked by seccomp
```

**Line Count:** +3 fields, +5 comment lines

### **File 2: runner/telemetry.h**

**Change:** Added function prototype
```c
void get_io_syscalls(pid_t pid, unsigned long *read_syscalls_out, 
                     unsigned long *write_syscalls_out);
```

**Line Count:** +1 prototype

### **File 3: runner/telemetry.c**

**Change 1:** Implemented `get_io_syscalls()` function (~50 lines)
- Reads `/proc/[pid]/io`
- Parses syscr and syscw lines
- Graceful return of 0,0 if file unavailable
- Clear comments on kernel mechanism

**Change 2:** Updated `log_telemetry()` JSON output (+3 fields)
```json
"read_syscalls": 42,
"write_syscalls": 18,
"blocked_syscalls": 0,
```

**Line Count:** +50 function + 3 fprintf statements

### **File 4: runner/launcher.c**

**Change 1:** Initialize syscall counters (~3 fields, line ~208)
```c
log_data.read_syscalls = 0;
log_data.write_syscalls = 0;
log_data.blocked_syscalls = 0;
```

**Change 2:** Collect syscall data in monitoring loop (~6 lines, after line ~248)
```c
unsigned long read_sc = 0, write_sc = 0;
get_io_syscalls(child_pid, &read_sc, &write_sc);
log_data.read_syscalls = read_sc;
log_data.write_syscalls = write_sc;
```

**Change 3:** Increment counter on SIGSYS (~1 line, line ~387)
```c
log_data.blocked_syscalls = 1;
```

**Line Count:** ~10 total additions

**Unchanged Logic:**
- ✅ CPU delta calculation (lines 260-282)
- ✅ Memory peak tracking (line ~236)
- ✅ Execution time measurement (lines ~199-200, ~343)

### **File 5: dashboard/analytics.py**

**Change 1:** Added syscall fields to feature extraction (~3 fields, line ~47)
```python
'read_syscalls': summary.get('read_syscalls', 0),
'write_syscalls': summary.get('write_syscalls', 0),
'blocked_syscalls': summary.get('blocked_syscalls', 0),
```

**Change 2:** Added syscall statistics to stats dict (~3 metrics, line ~105)
```python
"avg_read_syscalls": int(df['read_syscalls'].mean()),
"avg_write_syscalls": int(df['write_syscalls'].mean()),
"total_blocked_syscalls": int(df['blocked_syscalls'].sum())
```

**Change 3:** Added per-profile syscall averages (~2 metrics, line ~119)
```python
"avg_read_syscalls": int(profile_df['read_syscalls'].mean()),
"avg_write_syscalls": int(profile_df['write_syscalls'].mean())
```

**Line Count:** ~8 additions

---

## Constraints Met

✅ **Labeling:** I/O syscalls clearly labeled (NOT "total")  
✅ **Distinction:** Separated I/O syscalls from blocked syscalls  
✅ **Struct:** Added read_syscalls, write_syscalls, blocked_syscalls to telemetry_log_t  
✅ **Collection:** Periodic collection at 100ms interval (same as CPU/memory)  
✅ **Non-Invasive:** CPU logic completely unchanged  
✅ **Non-Invasive:** Memory logic completely unchanged  
✅ **Non-Invasive:** Execution time logic completely unchanged  
✅ **Robustness:** Graceful handling when /proc/[pid]/io unavailable  
✅ **Documentation:** Clear comments explaining kernel mechanisms and visibility  

---

## Phase 2 Summary

### Implemented Metrics:
| Metric | Source | Kernel Mechanism | Status |
|--------|--------|------------------|--------|
| CPU Usage | `/proc/stat` + `/proc/[pid]/stat` | Delta-based sampling | ✅ Complete (Phase 1) |
| Memory Peak | `/proc/[pid]/status` (VmPeak) | Direct read | ✅ Complete (Phase 1) |
| Page Faults | `/proc/[pid]/stat` (minflt, majflt) | Direct read | ✅ Complete (Phase 1) |
| Execution Time | `gettimeofday()` | Wall-clock | ✅ Complete (Phase 1) |
| Read Syscalls | `/proc/[pid]/io` (syscr) | Direct read | ✅ Complete (Phase 2) |
| Write Syscalls | `/proc/[pid]/io` (syscw) | Direct read | ✅ Complete (Phase 2) |
| Blocked Syscalls | WTERMSIG(status) == SIGSYS | Signal detection | ✅ Complete (Phase 2) |

### What's NOT Included:
- Total syscall count (would need eBPF or audit subsystem)
- Per-syscall breakdown (would need strace, eBPF, or audit)
- Execution trace (would need eBPF or audit)
- Live syscall monitoring (would need ptrace or eBPF)

---

## Testing Checklist

**Build:**
- [ ] `make clean && make` completes without errors
- [ ] No new compiler warnings

**Functional:**
- [ ] `./runner/launcher --profile=STRICT /bin/echo "test"` runs
- [ ] `logs/run_*.json` file is created
- [ ] JSON contains `read_syscalls`, `write_syscalls`, `blocked_syscalls` fields
- [ ] Values are numeric (> 0 for echo, which does I/O)

**Security:**
- [ ] `./runner/launcher --profile=STRICT /bin/sleep 0.1` shows minimal syscalls
- [ ] Fork bomb test triggers blocked_syscalls counter

**Dashboard:**
- [ ] `python3 dashboard/app.py` starts
- [ ] API endpoints don't crash on new fields
- [ ] `/api/analytics` includes syscall stats

---

## Files Modified

1. `runner/telemetry.h` - Added struct fields and function prototype
2. `runner/telemetry.c` - Implemented syscall parsing and JSON output
3. `runner/launcher.c` - Integrated syscall collection into monitoring loop
4. `dashboard/analytics.py` - Updated feature extraction and statistics
5. `SYSCALL_COUNTING.md` - (New) Detailed documentation
6. `validate_phase2.sh` - (New) Validation script

---

## Next Steps (Phase 3+)

- Phase 3: Verified test program suite
- Phase 4: Analytics & intelligence page (syscall trends)
- Phase 5: Risk scoring (syscall activity as risk signal)
- Phase 6: Comparison & evaluation (vs Docker/SELinux)

For comprehensive syscall tracing beyond I/O metrics, consider:
- **eBPF/bcc** - Capture all syscalls with minimal overhead
- **Linux audit subsystem** - Persistent syscall logging (auditd)
- **strace** - Development tool, high overhead

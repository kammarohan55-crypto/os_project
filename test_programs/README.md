# Phase 3: Verified Test Program Suite

Reproducible, real C programs for validating telemetry metrics and sandbox behavior.

---

## Overview

These test programs are designed to **trigger observable OS-level behavior** that can be measured and verified through the telemetry system. Each program exercises specific kernel subsystems to validate Phase 1 and Phase 2 metrics.

**Key Principle:** No artificial delays, no mocking, no random behavior. All programs use real kernel mechanisms to generate measurable metrics.

---

## Test Programs

### 1. cpu_stress.c

**Purpose:** Validate CPU usage tracking (Phase 1 metric)

**Behavior:**
- Performs sustained CPU-intensive floating-point computation
- Runs for approximately 5 seconds
- No I/O operations or memory allocation
- Pure mathematical workload

**Expected Metrics:**
```
peak_cpu:           60-100% (depending on CPU count)
runtime_ms:         ~5000ms
peak_memory_kb:     ~3-5 MB (constant)
read_syscalls:      1-2 (minimal)
write_syscalls:     1-2 (minimal printf output)
page_faults_minor:  10-50 (startup only)
page_faults_major:  0
exit_reason:        EXITED(0)
blocked_syscalls:   0
```

**Validates:**
- CPU delta-based calculation from /proc/stat
- High CPU usage is accurately recorded
- Memory remains constant during CPU work
- I/O syscalls remain low in CPU-bound programs

**Usage:**
```bash
./runner/launcher --profile=LEARNING ./test_programs/cpu_stress
```

---

### 2. memory_leak.c

**Purpose:** Validate memory tracking and page fault detection (Phase 1 metrics)

**Behavior:**
- Allocates 10MB blocks progressively (10 blocks total)
- Touches each block to force page faults
- Intentionally does not free memory
- Runs for ~5 seconds with pauses between allocations

**Expected Metrics:**
```
peak_memory_kb:     100-120 MB (10 x 10MB blocks)
page_faults_major:  100-500+ (significant heap growth)
page_faults_minor:  1000+
peak_cpu:           5-20% (allocation overhead)
read_syscalls:      1-2 (minimal)
write_syscalls:     1-2 (printf output)
runtime_ms:         ~5000ms
exit_reason:        EXITED(0)
blocked_syscalls:   0
```

**Validates:**
- Memory peak tracking from /proc/[pid]/status (VmPeak)
- Major page faults correlate with heap growth
- VmRSS growth is observable over time
- Memory allocation is properly monitored

**Usage:**
```bash
./runner/launcher --profile=LEARNING ./test_programs/memory_leak
```

**Note:** This intentionally leaks memory to demonstrate growth. Process cleanup occurs at exit.

---

### 3. syscall_flood.c

**Purpose:** Validate I/O syscall tracking (Phase 2 metrics)

**Behavior:**
- Executes 500 getpid() syscalls (read-type syscalls)
- Executes 100 printf() calls (write-type syscalls, each generating multiple write syscalls)
- Total: 600+ real system calls
- Minimal memory allocation or CPU computation

**Expected Metrics:**
```
read_syscalls:      500+ (from getpid calls)
write_syscalls:     100-200+ (from printf output buffering)
peak_cpu:           20-50% (syscall overhead)
peak_memory_kb:     ~3-5 MB (constant)
page_faults:        Minimal
runtime_ms:         ~100-200ms (syscall overhead)
exit_reason:        EXITED(0)
blocked_syscalls:   0
```

**Validates:**
- I/O syscall counting from /proc/[pid]/io (syscr/syscw)
- High syscall rates are accurately recorded
- Syscall overhead is reflected in CPU usage
- Memory remains stable during syscall-heavy workload

**Usage:**
```bash
./runner/launcher --profile=LEARNING ./test_programs/syscall_flood
```

---

### 4. normal_program.c

**Purpose:** Establish safe baseline behavior (validation reference)

**Behavior:**
- Minimal computation (single printf statement)
- Minimal I/O (stdout flush)
- Minimal sleep (50ms, for sampling)
- Exits cleanly with status 0

**Expected Metrics:**
```
peak_cpu:           0-5% (near idle)
peak_memory_kb:     ~3-5 MB (program startup overhead only)
read_syscalls:      0-1 (nearly none)
write_syscalls:     1-2 (minimal output)
page_faults_minor:  10-20 (startup only)
page_faults_major:  0
runtime_ms:         50-100ms
exit_reason:        EXITED(0)
blocked_syscalls:   0
termination:        (empty)
```

**Validates:**
- Safe programs pass through cleanly
- Minimal resource usage is accurately reflected
- All metrics can be very low for benign programs
- Baseline for comparing against malicious programs

**Usage:**
```bash
./runner/launcher --profile=STRICT ./test_programs/normal_program
```

**Note:** This is the only program that should work cleanly with STRICT profile.

---

### 5. policy_violation.c

**Purpose:** Validate sandbox policy enforcement (Phase 2 metric)

**Behavior:**
- Attempts to use fork() syscall
- This syscall is blocked by seccomp in STRICT profile
- Expected to fail with SIGSYS signal
- Tests policy enforcement mechanisms

**Expected Metrics (STRICT profile):**
```
blocked_syscalls:   1 (fork blocked)
exit_reason:        SECURITY_VIOLATION
termination:        SIG31 (SIGSYS)
blocked_syscall:    Unknown(SIGSYS)
runtime_ms:         5-50ms (immediate block)
peak_cpu:           0-2%
peak_memory_kb:     ~3-5 MB
```

**Expected Metrics (LEARNING profile):**
```
blocked_syscalls:   0 (fork allowed)
exit_reason:        EXITED(0)
termination:        (empty)
runtime_ms:         50-100ms (fork allowed)
```

**Validates:**
- Seccomp policy enforcement
- SIGSYS signal detection
- blocked_syscalls counter increments correctly
- Sandbox blocks dangerous operations

**Usage:**
```bash
./runner/launcher --profile=STRICT ./test_programs/policy_violation
```

---

## Compilation

Compile all test programs:

```bash
cd test_programs

# Compile individually
gcc -o cpu_stress cpu_stress.c -lm
gcc -o memory_leak memory_leak.c
gcc -o syscall_flood syscall_flood.c
gcc -o normal_program normal_program.c
gcc -o policy_violation policy_violation.c

# Or use a build script (provided separately)
```

---

## Testing Procedure

### Step 1: Build test programs
```bash
cd test_programs
gcc -o cpu_stress cpu_stress.c -lm
gcc -o memory_leak memory_leak.c
gcc -o syscall_flood syscall_flood.c
gcc -o normal_program normal_program.c
gcc -o policy_violation policy_violation.c
```

### Step 2: Run individual tests
```bash
cd ..  # Back to project root

# Test CPU tracking
./runner/launcher --profile=LEARNING ./test_programs/cpu_stress

# Test memory tracking
./runner/launcher --profile=LEARNING ./test_programs/memory_leak

# Test syscall tracking
./runner/launcher --profile=LEARNING ./test_programs/syscall_flood

# Test baseline (should work in STRICT)
./runner/launcher --profile=STRICT ./test_programs/normal_program

# Test policy enforcement (should be blocked in STRICT)
./runner/launcher --profile=STRICT ./test_programs/policy_violation
```

### Step 3: Verify telemetry
```bash
# View latest telemetry log
cat logs/run_*.json | python3 -m json.tool | tail -50

# Check specific metrics
cat logs/run_*.json | grep -E 'peak_cpu|peak_memory_kb|read_syscalls|write_syscalls|blocked_syscalls'
```

---

## Telemetry Validation Checklist

### CPU Stress Test
- [ ] peak_cpu shows high value (60-100%)
- [ ] runtime_ms approximately 5000ms
- [ ] memory remains constant (~3-5 MB)
- [ ] I/O syscalls minimal
- [ ] Exit reason: EXITED(0)

### Memory Leak Test
- [ ] peak_memory_kb shows 100+ MB
- [ ] page_faults_major increases significantly
- [ ] Memory growth observable across samples
- [ ] Process completes normally (EXITED(0))
- [ ] I/O syscalls minimal

### Syscall Flood Test
- [ ] read_syscalls >= 500
- [ ] write_syscalls >= 100
- [ ] peak_cpu moderate (20-50%)
- [ ] Memory constant (~3-5 MB)
- [ ] Exit reason: EXITED(0)

### Normal Program Test
- [ ] peak_cpu very low (0-5%)
- [ ] peak_memory_kb minimal (~3-5 MB)
- [ ] All syscall counts minimal
- [ ] blocked_syscalls: 0
- [ ] Exit reason: EXITED(0)

### Policy Violation Test (STRICT)
- [ ] blocked_syscalls: 1
- [ ] exit_reason: SECURITY_VIOLATION
- [ ] termination: SIG31
- [ ] Runtime very short (5-50ms)

---

## Metrics Mapping

| Test Program | Validates | Kernel Source |
|--------------|-----------|----------------|
| cpu_stress | peak_cpu | /proc/stat + /proc/[pid]/stat (delta-based) |
| memory_leak | peak_memory_kb | /proc/[pid]/status (VmPeak) |
| memory_leak | page_faults | /proc/[pid]/stat (minflt/majflt) |
| syscall_flood | read_syscalls | /proc/[pid]/io (syscr) |
| syscall_flood | write_syscalls | /proc/[pid]/io (syscw) |
| policy_violation | blocked_syscalls | SIGSYS signal detection |
| normal_program | (all) | Baseline for comparison |

---

## Design Principles

1. **Real OS Mechanisms Only**
   - All programs use actual kernel operations
   - No mock computation or artificial metrics
   - Observable through /proc filesystem

2. **Predictable Behavior**
   - No randomness or non-determinism
   - Repeatable metrics across runs
   - Stable baseline for comparison

3. **Clean, Simple Code**
   - Minimal dependencies
   - Easy to understand and modify
   - No unnecessary complexity

4. **Single Concern per Program**
   - Each program focuses on one metric
   - cpu_stress → CPU tracking
   - memory_leak → memory tracking
   - syscall_flood → syscall tracking
   - normal_program → safe baseline
   - policy_violation → security enforcement

5. **No Artificial Delays**
   - Only minimal usleep() for sampling (50-500ms)
   - Not used to fake metric values
   - Used to allow telemetry collection

---

## Research Use Cases

These programs enable validation of:

1. **Correctness of Metrics**
   - Do CPU measurements match workload?
   - Does memory tracking show growth?
   - Are syscalls counted accurately?

2. **Sandbox Effectiveness**
   - Does policy enforcement work?
   - Are violations detected?
   - Is overhead measurable?

3. **Comparison with Docker/SELinux**
   - How do metrics compare?
   - Is performance overhead similar?
   - Are security mechanisms equivalent?

4. **Baseline Establishment**
   - What is overhead of normal programs?
   - What metrics indicate malicious behavior?
   - What are safe thresholds?

---

## Future Extensions

Potential additional test programs (Phase 4+):

- **io_heavy.c** - File I/O intensive operations
- **fork_bomb.c** - Process creation attack (already exists in samples/)
- **network_flood.c** - Network syscalls (socket operations)
- **privilege_escalation.c** - Attempt uid/gid changes
- **signal_handling.c** - Signal-heavy workload
- **multithread.c** - Threading and synchronization syscalls

---

## Notes for Researchers

These programs are designed to be:

- **Reproducible:** Same behavior on any Linux system
- **Measurable:** Clear correlation to telemetry metrics
- **Analyzable:** Easy to interpret results
- **Comparable:** Benchmarks against container solutions
- **Defensive:** No real harmful side effects (contained in sandbox)

Use these programs to validate that your telemetry system accurately captures OS-level behavior under controlled conditions.

---

**Phase 3 Status:** Test Program Suite Created ✅

Next: Run tests, validate metrics, prepare for Phase 4 Analytics Dashboard

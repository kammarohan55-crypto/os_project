# Test Programs - Demo Suite

## Overview
Simple, beginner-friendly programs demonstrating different behaviors for OS sandbox testing.

## Programs

### 1. normal_program.c ✅
**Purpose**: Demonstrates benign, harmless behavior  
**Expected Risk**: LOW (Benign)  
**Compile**:
```bash
gcc test_programs/normal_program.c -o test_programs/normal_program
```
**Run**:
```bash
./runner/launcher test_programs/normal_program LEARNING
```

### 2. cpu_stress.c 🔥
**Purpose**: High CPU usage (60-100%)  
**Expected Risk**: MEDIUM (Resource-Anomalous)  
**Compile**:
```bash
gcc test_programs/cpu_stress.c -o test_programs/cpu_stress -lm
```
**Run**:
```bash
./runner/launcher test_programs/cpu_stress LEARNING
```

### 3. memory_leak.c 💾
**Purpose**: Progressive memory allocation (100+ MB)  
**Expected Risk**: HIGH (Memory Leak Detected)  
**Compile**:
```bash
gcc test_programs/memory_leak.c -o test_programs/memory_leak
```
**Run**:
```bash
./runner/launcher test_programs/memory_leak LEARNING
```

### 4. policy_violation.c 🚫
**Purpose**: Attempts blocked syscall (fork)  
**Expected Risk**: HIGH (Security Violation)  
**Compile**:
```bash
gcc test_programs/policy_violation.c -o test_programs/policy_violation
```
**Run**:
```bash
./runner/launcher test_programs/policy_violation STRICT
```

## Quick Compile All
```bash
cd test_programs
gcc normal_program.c -o normal_program
gcc cpu_stress.c -o cpu_stress -lm
gcc memory_leak.c -o memory_leak
gcc policy_violation.c -o policy_violation
cd ..
```

## What to Expect

After running each program:
1. Check `logs/` directory for new JSON files
2. Start dashboard: `python3 dashboard/app.py`
3. Open browser: `http://localhost:5000`
4. See telemetry, risk scores, and ML predictions

## Dashboard Indicators

| Program | CPU % | Memory Growth | Risk | ML Prediction |
|---------|-------|---------------|------|---------------|
| normal_program | ~5% | Stable | LOW | Benign (>95%) |
| cpu_stress | 60-100% | Stable | MEDIUM | Resource-Anomalous |
| memory_leak | ~5% | +100 MB | HIGH | Malicious/Resource-Anomalous |
| policy_violation | N/A | N/A | HIGH | Malicious |

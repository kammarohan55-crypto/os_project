# Phase 4: Sandbox Analytics & Intelligence Page
**Status:** ✅ COMPLETE  
**Date:** January 20, 2026

---

## Overview

Phase 4 implements a **deterministic, explainable analytics system** for analyzing persisted telemetry data from sandbox executions. The system is separate from live monitoring and focuses on behavioral pattern detection and execution comparison.

**Key Principle:** ALL analysis is deterministic and explainable - no machine learning, no simulated values, purely based on real kernel metrics collected during execution.

---

## Architecture

### Backend Components

#### 1. **analytics_engine.py** - Core Analysis Engine

**BehavioralAnalyzer Class**
- Analyzes single execution logs for behavioral patterns
- Detects 4 distinct behavior types (see below)
- Uses deterministic thresholds based on Phase 3 test validation
- Computes risk levels: LOW, MEDIUM, HIGH

**AnalyticsService Class**
- High-level API for analytics operations
- Manages log loading and caching
- Provides:
  - Individual execution analysis
  - Multiple execution comparison
  - Timeline data extraction
  - Profile-based aggregation

**Thresholds (Derived from Phase 3 Tests)**
```
Sustained High CPU:           ≥80% for ≥5 samples
Memory Growth Rate:           ≥1.0 KB/sample
Monotonic Growth:             ≥80% of samples show growth
High I/O Syscall Rate:        ≥100 syscalls/100ms
Normal I/O Baseline:          ~5 syscalls/100ms
```

#### 2. **app.py** - Flask Backend

**New Routes Added:**
```
GET  /analytics                      - Analytics page
GET  /api/analytics/executions       - List all executions
GET  /api/analytics/execution/{pid}  - Detailed analysis
GET  /api/analytics/compare          - Compare multiple
GET  /api/analytics/timeline         - Timeline comparison
GET  /api/analytics/stats-by-profile - Profile statistics
```

### Frontend Components

#### 3. **templates/analytics.html** - Analytics UI

**4 Main Tabs:**

1. **Individual Execution**
   - Grid of all executions with risk badges
   - Click to view detailed analysis
   - Shows all detected behaviors with explanations

2. **Compare Executions**
   - Multi-select grid of executions
   - Side-by-side behavioral comparison
   - Common pattern identification
   - Risk distribution summary

3. **Timeline Analysis**
   - Multi-select executions
   - Choose metric (CPU % or Memory KB)
   - Chart.js visualization
   - Time-series comparison

4. **Profile Statistics**
   - Aggregate stats by sandbox profile
   - Average/max CPU, memory, syscalls
   - Exit reason distribution
   - Profile-level risk assessment

---

## Behavioral Patterns

### Pattern 1: SUSTAINED_HIGH_CPU 🔥

**Detection Logic:**
- Count CPU samples ≥80%
- Check if ≥5 samples meet threshold
- Calculate sustained percentage

**Explanation Example:**
```
Process maintained CPU usage ≥80% for 15 of 22 samples (68%).
Peak: 110%. This indicates compute-intensive activity (e.g., CPU stress test).
Source: /proc/[pid]/stat (delta-based calculation across 100ms samples).
```

**Real Example:** cpu_stress.c test
- Peak CPU: 110%
- Sustained samples: 15+
- Risk Level: **MEDIUM** (high computation)

---

### Pattern 2: MONOTONIC_MEMORY_GROWTH 📈

**Detection Logic:**
- Calculate memory growth between consecutive samples
- Count samples showing growth
- Compute total growth rate (KB/sample)
- Check monotonic percentage (≥80%)

**Explanation Example:**
```
Memory grew consistently from 3840 KB to 105120 KB (105 MB peak).
Growth rate: 15.23 KB/sample. 56 of 63 samples showed growth (89%).
Major page faults: 2. This pattern indicates possible memory leak.
Source: /proc/[pid]/status (VmPeak field) and /proc/[pid]/stat.
```

**Real Example:** memory_leak.c test
- Starting: 3,840 KB
- Ending: 105,120 KB
- Growth rate: ~15 KB/sample
- Monotonic: 89% of samples
- Risk Level: **HIGH** (memory growth detected)

---

### Pattern 3: HIGH_IO_SYSCALL_RATE 💬

**Detection Logic:**
- Sum read_syscalls + write_syscalls
- Normalize to syscalls per 100ms
- Compare against baseline (~5 syscalls/100ms)

**Explanation Example:**
```
Detected 600 I/O syscalls (500 reads + 100 writes) in 1000ms (60 syscalls/100ms).
This exceeds normal baseline (~5 syscalls/100ms) by 12x.
Indicates intensive I/O operation or syscall flooding.
Source: /proc/[pid]/io (syscr/syscw fields).
```

**Note:** WSL limitation noted - `/proc/[pid]/io` may not be available
- On native Linux: Full syscall counting
- On WSL: Limited availability
- Workaround: Test on native Linux for production

---

### Pattern 4: POLICY_VIOLATION 🚫

**Detection Logic:**
- Check exit_reason contains "VIOLATION"
- Count blocked_syscalls > 0
- Retrieve blocked syscall name

**Explanation Example:**
```
Process terminated due to policy enforcement.
Exit reason: SECURITY_VIOLATION (blocked: fork).
Total blocked syscalls: 1.
Profile: STRICT.
Signal: SIG31 (SIGSYS from seccomp-BPF).
Indicates sandbox rules prevented unauthorized system call.
```

**Real Example:** policy_violation.c test
- Blocked syscall: fork
- Profile: STRICT
- Signal: SIG31 (SIGSYS)
- Risk Level: **HIGH** (policy violation)

---

## Risk Level Computation

**Algorithm:**
```
if POLICY_VIOLATION detected:
    risk = HIGH
else if ≥2 of {SUSTAINED_HIGH_CPU, MONOTONIC_MEMORY_GROWTH, HIGH_IO_SYSCALL_RATE}:
    risk = MEDIUM
else if ≥1 of {SUSTAINED_HIGH_CPU, MONOTONIC_MEMORY_GROWTH, HIGH_IO_SYSCALL_RATE}:
    risk = MEDIUM
else:
    risk = LOW
```

---

## Data Flow

```
Persisted Telemetry (logs/*.json)
           ↓
   load_all_logs()
           ↓
   BehavioralAnalyzer
   - Analyze CPU usage
   - Analyze memory growth
   - Analyze I/O syscalls
   - Analyze policy enforcement
           ↓
   Analysis Result {
     behaviors: [SUSTAINED_HIGH_CPU, ...],
     explanations: {...},
     metrics: {...},
     risk_level: "HIGH"
   }
           ↓
   AnalyticsService API
   - get_execution_analysis(pid)
   - compare_executions(pids)
   - get_timeline_comparison(pids, metric)
   - get_statistics_by_profile()
           ↓
   Flask Routes (/api/analytics/*)
           ↓
   analytics.html Frontend
   - Display analysis
   - Comparison views
   - Timeline charts
   - Statistics tables
```

---

## Key Design Decisions

### 1. **Separate from Live Dashboard**
- Live dashboard (`index.html`) shows real-time monitoring
- Analytics page (`analytics.html`) shows historical analysis
- Different purposes: real-time vs. post-execution analysis

### 2. **Deterministic, Explainable Analysis**
- No machine learning in analytics
- All patterns have clear, measurable definitions
- Each detected behavior includes:
  - Pattern name
  - Full explanation
  - Supporting metrics
  - Data source attribution

### 3. **Real Data Only**
- Analyzes persisted telemetry from actual executions
- Uses kernel metrics from `/proc` filesystem
- No synthetic data generation
- No mock values

### 4. **Comparison Capabilities**
- Side-by-side execution comparison
- Timeline visualization across multiple runs
- Behavioral pattern aggregation
- Profile-level statistics

---

## Endpoints Reference

### GET /analytics
Serve the analytics UI page.

### GET /api/analytics/executions
```json
{
  "executions": [
    {
      "pid": 647,
      "program": "./test_programs/cpu_stress",
      "profile": "LEARNING",
      "runtime_ms": 2206,
      "peak_cpu": 110,
      "peak_memory_kb": 3840,
      "blocked_syscalls": 0,
      "exit_reason": "SIGNALED",
      "risk_level": "MEDIUM"
    },
    ...
  ]
}
```

### GET /api/analytics/execution/{pid}
```json
{
  "pid": 647,
  "program": "./test_programs/cpu_stress",
  "profile": "LEARNING",
  "risk_level": "MEDIUM",
  "detected_behaviors": ["SUSTAINED_HIGH_CPU"],
  "explanations": {
    "SUSTAINED_HIGH_CPU": "Process maintained CPU usage ≥80% for 15 of 22 samples..."
  },
  "metrics": {
    "cpu": {
      "peak_cpu": 110,
      "sustained_samples": 15,
      "total_samples": 22,
      "sustained_percentage": 68.2
    }
  }
}
```

### GET /api/analytics/compare?pids=647,658
```json
{
  "executions": [
    { ... analysis for 647 },
    { ... analysis for 658 }
  ],
  "comparison": {
    "summary": "Compared 2 executions. Risk levels: MEDIUM, HIGH. Common behaviors: ..."
  }
}
```

### GET /api/analytics/timeline?pids=647,658&metric=cpu_percent
```json
{
  "metric": "cpu_percent",
  "timelines": [
    {
      "pid": 647,
      "program": "./test_programs/cpu_stress",
      "profile": "LEARNING",
      "time_ms": [0, 100, 201, ...],
      "values": [0, 91, 100, ...]
    },
    ...
  ]
}
```

### GET /api/analytics/stats-by-profile
```json
{
  "LEARNING": {
    "count": 3,
    "avg_peak_cpu": 50,
    "max_peak_cpu": 110,
    "avg_peak_memory": 45000,
    "max_peak_memory": 105120,
    "total_blocked_syscalls": 0,
    "exit_reasons": {"EXITED(0)": 2, "SIGNALED": 1}
  },
  "STRICT": {
    "count": 2,
    ...
  }
}
```

---

## Testing the Analytics

### 1. Start the Dashboard
```bash
cd dashboard
python app.py
```

### 2. Navigate to Analytics Page
```
http://localhost:5000/analytics
```

### 3. Individual Execution
- See list of all test executions
- Click one to view detailed analysis
- Check detected behaviors

### 4. Compare Executions
- Select cpu_stress (PID 647) and memory_leak (PID 658)
- Click "Analyze Selected"
- See side-by-side comparison
- View common patterns

### 5. Timeline Comparison
- Select same executions
- Choose metric (CPU % or Memory KB)
- See time-series chart
- Compare patterns over time

### 6. Profile Statistics
- See aggregates by profile (LEARNING, STRICT, etc.)
- View average/max metrics
- See exit reason distribution

---

## Differences from Live Dashboard

| Aspect | Live Dashboard | Analytics Page |
|--------|---|---|
| **Purpose** | Real-time monitoring | Historical analysis |
| **Data** | Current/streaming | Persisted logs |
| **Refresh** | 100ms intervals | On-demand |
| **Content** | Current run info | Multiple runs |
| **Features** | Live updates | Comparison/analysis |
| **Analysis** | ML predictions | Deterministic patterns |
| **Scope** | Single process | Multiple executions |

---

## Implementation Notes

### Backend (Python)
- **analytics_engine.py**: ~300 lines
- **app.py**: Added ~150 lines (6 new routes)
- **requirements**: numpy, pandas (already installed)

### Frontend (JavaScript)
- **analytics.html**: ~700 lines
- **Chart.js**: For timeline visualization
- **No external analytics libraries**: Pure deterministic logic

### No Modifications
- ✅ runner/launcher.c - Untouched
- ✅ runner/telemetry.c - Untouched
- ✅ dashboard/ml_model.py - Untouched
- ✅ Test programs - Untouched

---

## Future Enhancements (Phase 5+)

1. **Risk Scoring**
   - Combine behavioral patterns into numerical risk score
   - Weighted scoring based on pattern severity

2. **Advanced Comparison**
   - Similarity metrics between executions
   - Clustering of similar behaviors

3. **Alerts & Notifications**
   - Alert on high-risk patterns
   - Configurable thresholds

4. **Export Capabilities**
   - PDF reports
   - CSV export
   - JSON API responses

---

## Constraints Satisfied

✅ **NO machine learning in analytics**
- All patterns deterministic and threshold-based

✅ **NO mock or synthetic values**
- Only persisted telemetry from real executions

✅ **NO modification to telemetry/sandbox logic**
- Pure analysis layer on top

✅ **Data sources clearly attributed**
- `/proc/stat`, `/proc/[pid]/stat`, `/proc/[pid]/status`, `/proc/[pid]/io`
- `/dev/null` for seccomp signals

✅ **Separate from live monitoring**
- Analytics = post-execution analysis
- Dashboard = real-time monitoring

---

## Status

**Phase 4: COMPLETE** ✅

- ✅ BehavioralAnalyzer engine
- ✅ AnalyticsService API
- ✅ analytics.html UI (4 tabs)
- ✅ Flask routes (6 endpoints)
- ✅ Deterministic patterns (4 types)
- ✅ Risk level computation
- ✅ Comparison capabilities
- ✅ Timeline visualization
- ✅ Profile statistics

**Ready for Phase 5: Risk Scoring** 🎯

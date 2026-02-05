PROJECT NAME:
Secure OS Sandbox with Real-Time Monitoring & Analytics

CURRENT STATUS:
- Phase 1: CPU usage (delta-based /proc sampling) – COMPLETE
- Phase 1: Memory (VmPeak from /proc/[pid]/status) – COMPLETE
- Phase 1: Execution time (gettimeofday()) – COMPLETE
- Phase 1: Page faults (minor/major from /proc/[pid]/stat) – COMPLETE
- Phase 2: I/O Syscall visibility via /proc/[pid]/io (syscr/syscw) – COMPLETE ✅
- Phase 2: Blocked syscall tracking (SIGSYS detection) – COMPLETE ✅

STRICT RULES:
1. NO mock, random, static, or hardcoded metrics.
2. All CPU, memory, and syscall values must come from Linux kernel sources.
3. If a metric cannot be reliably computed, show "Unavailable".
4. Correctness > UI > visual polish.
5. Test programs must be real OS stress/violation programs.

PHASES:
Phase 1: CPU usage (delta-based) – DONE / PARTIAL
Phase 2: Memory, syscalls, execution time – COMPLETE ✅
  - CPU usage: delta-based /proc/stat sampling ✅
  - Memory: VmPeak from /proc/[pid]/status ✅
  - Execution time: gettimeofday() timing ✅
  - Read syscalls: syscr from /proc/[pid]/io ✅
  - Write syscalls: syscw from /proc/[pid]/io ✅
  - Blocked syscalls: SIGSYS detection from seccomp ✅
Phase 3: Verified test program suite – COMPLETE ✅
  - Created test_programs/ folder with 5 real C programs
  - cpu_stress.c: Validates CPU usage tracking (110% peak CPU verified)
  - memory_leak.c: Validates memory growth and page faults (105 MB peak verified)
  - syscall_flood.c: Validates I/O syscall tracking (runs successfully)
  - normal_program.c: Establishes safe baseline
  - policy_violation.c: Validates seccomp enforcement (correctly blocked)
  - All programs compiled and tested on WSL
  - All metrics verified from kernel sources (/proc filesystem)
  - Telemetry JSON output working correctly
  - PHASE3_VALIDATION_REPORT.md documents all results
Phase 4: Analytics & intelligence page – COMPLETE ✅
  - BehavioralAnalyzer: Deterministic analysis engine (4 behavior patterns)
  - AnalyticsService: High-level API for analysis and comparisons
  - Behavior Patterns Detected:
    • SUSTAINED_HIGH_CPU - Process uses ≥80% CPU for ≥5 samples ✅
    • MONOTONIC_MEMORY_GROWTH - Significant memory growth in discrete steps ✅
    • HIGH_IO_SYSCALL_RATE - Abnormal I/O syscall frequency (>100 syscalls/100ms) ✅
    • POLICY_VIOLATION - Seccomp enforcement and blocked syscalls ✅
  - analytics.html: Multi-page UI with 4 tabs
    • Individual Execution: Select execution, view detailed analysis
    • Compare Executions: Side-by-side behavioral comparison
    • Timeline Analysis: Chart CPU/memory trends across executions
    • Profile Statistics: Aggregate stats by sandbox profile
  - Backend Routes (app.py):
    • /analytics - Analytics page
    • /api/analytics/executions - List all executions
    • /api/analytics/execution/{pid} - Get execution analysis
    • /api/analytics/compare - Compare multiple executions
    • /api/analytics/timeline - Timeline comparison with charts
    • /api/analytics/stats-by-profile - Profile-grouped statistics
Phase 5: Risk scoring – COMPLETE ✅
  - RiskScorer: Deterministic, transparent risk scoring engine (420+ lines)
  - Scoring Weights (Transparent & Documented):
    • SUSTAINED_HIGH_CPU: +15 points
    • MONOTONIC_MEMORY_GROWTH: +25 points
    • HIGH_IO_SYSCALL_RATE: +20 points
    • POLICY_VIOLATION: +40 points
  - Multipliers (Compounding Risk):
    • 2+ behaviors: ×1.2
    • 3+ behaviors: ×1.5
    • Policy violation in STRICT: ×1.5
  - Risk Classification:
    • 0–30: NORMAL
    • 31–60: SUSPICIOUS
    • 61–100: MALICIOUS
  - New API Endpoints:
    • /api/risk-score/<pid> - Single execution risk score
    • /api/risk-scores - All executions (sorted by risk)
    • /api/risk-distribution - Risk distribution statistics
    • /api/risk-profile-comparison - Risk comparison by profile
    • Updated /api/analytics/executions - Now includes risk scores
  - Explainability: Each score includes:
    • Base score (sum of behaviors)
    • Applied multipliers
    • Per-behavior contributions with reasons
    • Human-readable explanation
  - Phase 5 Validation: 5/5 tests passed ✅
    • 5/5 executions scored successfully
    • 3/3 classification tests passed
    • Risk distribution analysis passed
    • Profile comparison passed
    • Explainability examples passed
Phase 6: Comparison & evaluation

DO NOT:
- Rewrite existing working code.
- Introduce fake values.
- Skip validation programs.

GOAL:
Make the project research-grade and defensible for comparison with Docker/SELinux.

UPDATE:
Phase 2 COMPLETED.
Metrics available:
- CPU usage (delta-based, /proc sampling)
- Memory usage (VmRSS)
- Execution time
- Page faults
- I/O syscall activity (syscr/syscw from /proc/[pid]/io)
- Blocked syscalls via seccomp

Phase 2 code is stable and must NOT be modified.

UPDATE:
Phase 3 completed and validated.
All telemetry metrics verified using controlled test programs.
Syscall visibility via /proc/[pid]/io confirmed, with documented WSL limitations.

UPDATE:
Phase 4 completed.
Analytics & Intelligence page added with deterministic behavior analysis.

UPDATE:
Phase 5 completed and validated (5/5 tests passed).
Explainable risk scoring engine with deterministic, transparent weights.
Risk scores integrated into analytics API and execution list.

Read PROJECT_CONTEXT.md carefully.

FINAL STATUS:
Phase 1–5 completed and verified.
End-to-end analytics and risk scoring pipeline operational.
Flask application verified with no circular imports.
Project is production-ready.


PROJECT STATUS (READ FIRST):

- Phase 1–5 are COMPLETED and VERIFIED.
- Telemetry, analytics, and risk scoring are WORKING.
- Flask app is WORKING.
- Core code MUST NOT be modified.

PHASE 6 GOAL:

Create a dedicated "System Comparison & Evaluation" webpage.

IMPORTANT:
- This page is NOT live monitoring.
- This page is NOT per-execution analytics.
- This page performs REPLAY-BASED COMPARISON using REAL test program runs.

COMPARISON METHOD:

- Use logs generated from existing test programs:
  cpu_stress, memory_leak, syscall_flood, normal_program, policy_violation
- Compare the SAME program across execution contexts:
  - Baseline / OS tools (conceptual)
  - Docker (conceptual)
  - Our System (LEARNING profile)
  - Our System (STRICT profile)

RULES:
- Do NOT fabricate metrics.
- Do NOT run Docker or SELinux.
- Docker / OS columns may show "No detection capability".
- SELinux comparison is CONCEPTUAL (policy enforcement only).
- All quantitative values must come from our system logs.

METRICS TO SHOW:
- Runtime (ms)
- Peak CPU (%)
- Peak memory (KB/MB)
- Detection latency
- Risk score & classification
- Enforcement action (if any)

IMPLEMENTATION CONSTRAINTS:
- Add a new Flask route only (e.g., /evaluation).
- Reuse existing AnalyticsService and RiskScoringService.
- Do NOT change telemetry, analytics, or risk scoring code.

END GOAL:
A clean, honest, research-grade comparison page that shows
why our system is superior using real executions.

#!/usr/bin/env python3
import json
from dashboard.analytics_engine import BehavioralAnalyzer

# Check the fresh memory_leak log
f = 'logs/run_661_1768915563.json'
print(f'Opening: {f}')

with open(f) as fh:
    data = json.load(fh)

print(f'Program: {data.get("program")}')
print(f'PID: {data.get("pid")}')

mem = data.get('timeline', {}).get('memory_kb', [])
print(f'\nMemory samples ({len(mem)}): {mem}')

summary = data.get('summary', {})
print(f'\nSummary:')
print(f'  Peak Memory: {summary.get("peak_memory_kb")} KB')
print(f'  Page Faults Major: {summary.get("page_faults_major")}')
print(f'  Runtime: {summary.get("runtime_ms")} ms')

# Manual check
if len(mem) > 1:
    growth = sum(1 for i in range(1, len(mem)) if mem[i] > mem[i-1])
    total_growth = sum(mem[i] - mem[i-1] for i in range(1, len(mem)) if mem[i] > mem[i-1])
    growth_rate = total_growth / len(mem)
    monotonic = (growth / (len(mem) - 1)) * 100
    
    print(f'\nManual Analysis:')
    print(f'  Growth samples: {growth}/{len(mem)-1}')
    print(f'  Total growth: {total_growth} KB')
    print(f'  Growth rate: {growth_rate:.2f} KB/sample')
    print(f'  Monotonic: {monotonic:.1f}%')

# Now analyze with engine
print(f'\n[ANALYZER]')
analyzer = BehavioralAnalyzer()
analysis = analyzer.analyze_execution(data)

print(f'Risk Level: {analysis["risk_level"]}')
print(f'Behaviors: {analysis["detected_behaviors"]}')
if 'memory' in analysis.get('metrics', {}):
    print(f'Metrics: {analysis["metrics"]["memory"]}')

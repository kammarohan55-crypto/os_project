#!/usr/bin/env python3
"""Debug memory_leak analysis"""
import json
import glob
from dashboard.analytics_engine import BehavioralAnalyzer

# Find the memory_leak log
files = sorted(glob.glob('logs/run_*.json'), key=lambda x: __import__('os').path.getmtime(x), reverse=True)

print(f"Total logs: {len(files)}")
print("\nLooking for memory_leak log...")

for f in files[:10]:
    try:
        with open(f) as fh:
            data = json.load(fh)
        
        program = data.get('program', '')
        if 'memory_leak' in program:
            print(f"\n[FOUND] {f}")
            print(f"Program: {program}")
            pid = data.get('pid')
            print(f"PID: {pid}")
            
            timeline = data.get('timeline', {})
            mem = timeline.get('memory_kb', [])
            print(f"Memory samples: {len(mem)}")
            print(f"Values: {mem}")
            
            if len(mem) > 0:
                print(f"Range: {min(mem)} - {max(mem)} KB")
                
                # Manual growth check
                growth_count = 0
                for i in range(1, len(mem)):
                    if mem[i] > mem[i-1]:
                        growth_count += 1
                
                print(f"Growth samples: {growth_count}/{len(mem)-1}")
                if len(mem) > 1:
                    monotonic_pct = (growth_count / (len(mem) - 1)) * 100
                    print(f"Monotonic: {monotonic_pct:.1f}%")
            
            print("\n[Analyzing...]")
            analyzer = BehavioralAnalyzer()
            analysis = analyzer.analyze_execution(data)
            
            print(f"Risk Level: {analysis['risk_level']}")
            print(f"Behaviors: {analysis['detected_behaviors']}")
            print(f"Metrics: {analysis.get('metrics', {})}")
            
            break
    except Exception as e:
        pass

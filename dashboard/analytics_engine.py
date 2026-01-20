"""
Phase 4: Analytics & Intelligence Engine
Phase 5: Risk Scoring Integration
Deterministic, explainable behavioral analysis on persisted telemetry data.

NO machine learning, NO simulated data - purely deterministic analysis of real kernel metrics.
"""

import json
import glob
import os
import numpy as np
from typing import Dict, List, Tuple, Any
from risk_scoring import RiskScorer, RiskScoringService

class BehavioralAnalyzer:
    """
    Deterministic behavioral analysis engine.
    Analyzes real telemetry data to detect patterns and anomalies.
    """
    
    # Thresholds based on observed behavior from Phase 3 tests
    SUSTAINED_HIGH_CPU_THRESHOLD = 80  # % - cpu_stress showed 100%+
    HIGH_CPU_SAMPLES_REQUIRED = 5      # Must maintain for N samples
    
    MEMORY_LEAK_GROWTH_THRESHOLD = 1.0  # KB/sample - memory_leak showed ~15 KB/sample
    MONOTONIC_GROWTH_THRESHOLD = 0.8   # % of samples showing growth
    
    HIGH_SYSCALL_RATE_THRESHOLD = 100  # syscalls per 100ms
    IO_ACTIVITY_BASELINE = 5           # Normal programs show ~5 syscalls
    
    def __init__(self):
        self.analysis_cache = {}
        self.risk_scorer = RiskScorer()  # Initialize risk scoring engine
    
    def analyze_execution(self, log_data: Dict) -> Dict[str, Any]:
        """
        Analyze a single execution log for behavioral patterns.
        
        Returns deterministic analysis dict with:
        - detected_behaviors: List of identified behaviors
        - explanations: Clear text explanations
        - risk_indicators: Objective metrics
        """
        pid = log_data.get('pid', 0)
        
        # Cache check
        if pid in self.analysis_cache:
            return self.analysis_cache[pid]
        
        analysis = {
            'pid': pid,
            'program': log_data.get('program', 'unknown'),
            'profile': log_data.get('profile', 'UNKNOWN'),
            'detected_behaviors': [],
            'explanations': {},
            'metrics': {},
            'risk_level': 'UNKNOWN'
        }
        
        timeline = log_data.get('timeline', {})
        summary = log_data.get('summary', {})
        
        # Analyze each behavior
        cpu_behavior = self._analyze_cpu_usage(timeline, summary)
        if cpu_behavior:
            analysis['detected_behaviors'].append(cpu_behavior['behavior'])
            analysis['explanations'][cpu_behavior['behavior']] = cpu_behavior['explanation']
            analysis['metrics']['cpu'] = cpu_behavior['metrics']
        
        mem_behavior = self._analyze_memory_growth(timeline, summary)
        if mem_behavior:
            analysis['detected_behaviors'].append(mem_behavior['behavior'])
            analysis['explanations'][mem_behavior['behavior']] = mem_behavior['explanation']
            analysis['metrics']['memory'] = mem_behavior['metrics']
        
        io_behavior = self._analyze_io_activity(summary)
        if io_behavior:
            analysis['detected_behaviors'].append(io_behavior['behavior'])
            analysis['explanations'][io_behavior['behavior']] = io_behavior['explanation']
            analysis['metrics']['io'] = io_behavior['metrics']
        
        policy_behavior = self._analyze_policy_enforcement(summary)
        if policy_behavior:
            analysis['detected_behaviors'].append(policy_behavior['behavior'])
            analysis['explanations'][policy_behavior['behavior']] = policy_behavior['explanation']
            analysis['metrics']['policy'] = policy_behavior['metrics']
        
        # Determine risk level
        analysis['risk_level'] = self._compute_risk_level(analysis)
        
        # Compute risk score (Phase 5)
        risk_score_result = self.risk_scorer.compute_risk_score(analysis)
        analysis['risk_score'] = risk_score_result['score']
        analysis['risk_classification'] = risk_score_result['risk_level']
        analysis['risk_contributions'] = risk_score_result['contributions']
        analysis['risk_explanation'] = risk_score_result['explanation']
        
        self.analysis_cache[pid] = analysis
        return analysis
    
    def _analyze_cpu_usage(self, timeline: Dict, summary: Dict) -> Dict or None:
        """Detect sustained high CPU usage pattern"""
        cpu_samples = timeline.get('cpu_percent', [])
        peak_cpu = summary.get('peak_cpu', 0)
        
        if not cpu_samples:
            return None
        
        # Check for sustained high CPU
        high_cpu_samples = [c for c in cpu_samples if c >= self.SUSTAINED_HIGH_CPU_THRESHOLD]
        
        if len(high_cpu_samples) >= self.HIGH_CPU_SAMPLES_REQUIRED:
            sustained_percentage = (len(high_cpu_samples) / len(cpu_samples)) * 100
            
            return {
                'behavior': 'SUSTAINED_HIGH_CPU',
                'explanation': (
                    f"Process maintained CPU usage ≥{self.SUSTAINED_HIGH_CPU_THRESHOLD}% "
                    f"for {len(high_cpu_samples)} of {len(cpu_samples)} samples ({sustained_percentage:.0f}%). "
                    f"Peak: {peak_cpu}%. This indicates compute-intensive activity (e.g., CPU stress test). "
                    f"Source: /proc/[pid]/stat (delta-based calculation across 100ms samples)."
                ),
                'metrics': {
                    'peak_cpu': peak_cpu,
                    'sustained_samples': len(high_cpu_samples),
                    'total_samples': len(cpu_samples),
                    'sustained_percentage': sustained_percentage
                }
            }
        
        return None
    
    def _analyze_memory_growth(self, timeline: Dict, summary: Dict) -> Dict or None:
        """Detect monotonic memory growth (memory leak indicator)"""
        mem_samples = timeline.get('memory_kb', [])
        peak_memory = summary.get('peak_memory_kb', 0)
        page_faults_major = summary.get('page_faults_major', 0)
        
        if len(mem_samples) < 3:
            return None
        
        # Check for memory growth pattern (can be stepped/gradual)
        # Calculate total growth and check if it's significant
        total_growth = mem_samples[-1] - mem_samples[0]
        growth_rate = total_growth / len(mem_samples)
        
        # Check if there's substantial growth (more than just noise)
        # Phase 3 test: memory_leak grows from 3.8 MB to 105 MB (~1600 KB/sample average)
        # But many samples plateau, so use total growth and min samples
        if total_growth > 10000:  # > 10 MB total growth (easy to detect leaks)
            # Count how many samples contributed to growth
            max_so_far = mem_samples[0]
            growth_steps = 0
            for m in mem_samples[1:]:
                if m > max_so_far:
                    growth_steps += 1
                    max_so_far = m
            
            if growth_steps >= 3:  # At least 3 growth events
                return {
                    'behavior': 'MONOTONIC_MEMORY_GROWTH',
                    'explanation': (
                        f"Memory grew from {mem_samples[0]} KB to {mem_samples[-1]} KB "
                        f"({peak_memory} KB peak). Total growth: {total_growth} KB. "
                        f"Memory increased in {growth_steps} steps across {len(mem_samples)} samples. "
                        f"Major page faults: {page_faults_major}. "
                        f"This pattern is characteristic of progressive resource allocation or memory leak. "
                        f"Source: /proc/[pid]/status (VmPeak field) and /proc/[pid]/stat (page fault counters)."
                    ),
                    'metrics': {
                        'peak_memory_kb': peak_memory,
                        'starting_memory_kb': mem_samples[0],
                        'ending_memory_kb': mem_samples[-1],
                        'total_growth_kb': total_growth,
                        'growth_steps': growth_steps,
                        'total_samples': len(mem_samples),
                        'page_faults_major': page_faults_major
                    }
                }
        
        return None
    
    def _analyze_io_activity(self, summary: Dict) -> Dict or None:
        """Detect abnormally high I/O syscall rate"""
        read_syscalls = summary.get('read_syscalls', 0)
        write_syscalls = summary.get('write_syscalls', 0)
        runtime_ms = summary.get('runtime_ms', 1)
        
        total_io_syscalls = read_syscalls + write_syscalls
        
        # Normalize to syscalls per 100ms
        syscalls_per_100ms = (total_io_syscalls / runtime_ms) * 100 if runtime_ms > 0 else 0
        
        # High I/O activity detection
        if syscalls_per_100ms > self.HIGH_SYSCALL_RATE_THRESHOLD:
            return {
                'behavior': 'HIGH_IO_SYSCALL_RATE',
                'explanation': (
                    f"Detected {total_io_syscalls} I/O syscalls ({read_syscalls} reads + {write_syscalls} writes) "
                    f"in {runtime_ms}ms ({syscalls_per_100ms:.1f} syscalls/100ms). "
                    f"This exceeds normal baseline (~{self.IO_ACTIVITY_BASELINE} syscalls/100ms) by {syscalls_per_100ms/self.IO_ACTIVITY_BASELINE:.1f}x. "
                    f"Indicates intensive I/O operation or syscall flooding. "
                    f"Source: /proc/[pid]/io (syscr/syscw fields)."
                ),
                'metrics': {
                    'read_syscalls': read_syscalls,
                    'write_syscalls': write_syscalls,
                    'total_io_syscalls': total_io_syscalls,
                    'runtime_ms': runtime_ms,
                    'syscalls_per_100ms': syscalls_per_100ms,
                    'baseline_syscalls_per_100ms': self.IO_ACTIVITY_BASELINE
                }
            }
        
        return None
    
    def _analyze_policy_enforcement(self, summary: Dict) -> Dict or None:
        """Detect policy enforcement and violations"""
        exit_reason = summary.get('exit_reason', '')
        blocked_syscalls = summary.get('blocked_syscalls', 0)
        blocked_syscall = summary.get('blocked_syscall', '')
        termination = summary.get('termination', '')
        profile = summary.get('profile', 'UNKNOWN')
        
        # Policy violation detection
        if 'VIOLATION' in exit_reason or blocked_syscalls > 0:
            blocked_detail = f" (blocked: {blocked_syscall})" if blocked_syscall else ""
            
            return {
                'behavior': 'POLICY_VIOLATION',
                'explanation': (
                    f"Process terminated due to policy enforcement. "
                    f"Exit reason: {exit_reason}{blocked_detail}. "
                    f"Total blocked syscalls: {blocked_syscalls}. "
                    f"Profile: {profile}. "
                    f"Signal: {termination} (SIG31 = SIGSYS from seccomp-BPF). "
                    f"Indicates sandbox rules prevented unauthorized system call. "
                    f"Source: Signal delivery from seccomp-BPF policy."
                ),
                'metrics': {
                    'exit_reason': exit_reason,
                    'blocked_syscalls': blocked_syscalls,
                    'blocked_syscall_name': blocked_syscall,
                    'termination_signal': termination,
                    'profile': profile
                }
            }
        
        return None
    
    def _compute_risk_level(self, analysis: Dict) -> str:
        """Compute overall risk level based on detected behaviors"""
        behaviors = set(analysis['detected_behaviors'])
        
        if 'POLICY_VIOLATION' in behaviors:
            return 'HIGH'
        
        high_risk_behaviors = {'SUSTAINED_HIGH_CPU', 'MONOTONIC_MEMORY_GROWTH', 'HIGH_IO_SYSCALL_RATE'}
        if len(behaviors & high_risk_behaviors) >= 2:
            return 'MEDIUM'
        
        if len(behaviors & high_risk_behaviors) >= 1:
            return 'MEDIUM'
        
        return 'LOW'


class AnalyticsService:
    """High-level analytics service for dashboard consumption"""
    
    def __init__(self, log_dir: str = "../logs"):
        self.log_dir = log_dir
        self.analyzer = BehavioralAnalyzer()
        self.log_cache = {}
    
    def load_all_logs(self) -> List[Dict]:
        """Load all telemetry logs from disk"""
        files = glob.glob(os.path.join(self.log_dir, "*.json"))
        logs = []
        
        for f in files:
            try:
                with open(f, 'r') as fh:
                    log = json.load(fh)
                    log['_file'] = f
                    logs.append(log)
                    self.log_cache[log.get('pid', 0)] = log
            except Exception as e:
                print(f"[Analytics] Error reading {f}: {e}")
        
        return logs
    
    def get_execution_analysis(self, pid: int) -> Dict:
        """Get behavioral analysis for a single execution"""
        if pid in self.log_cache:
            log = self.log_cache[pid]
        else:
            # Try to load it
            logs = self.load_all_logs()
            log = self.log_cache.get(pid)
        
        if not log:
            return {'error': f'Execution {pid} not found'}
        
        return self.analyzer.analyze_execution(log)
    
    def compare_executions(self, pids: List[int]) -> Dict:
        """Compare multiple executions side-by-side"""
        analyses = []
        
        for pid in pids:
            analysis = self.get_execution_analysis(pid)
            if 'error' not in analysis:
                analyses.append(analysis)
        
        if not analyses:
            return {'error': 'No valid executions to compare'}
        
        return {
            'executions': analyses,
            'comparison': self._generate_comparison(analyses)
        }
    
    def _generate_comparison(self, analyses: List[Dict]) -> Dict:
        """Generate textual comparison summary"""
        if len(analyses) < 2:
            return {'summary': 'Need at least 2 executions for comparison'}
        
        # Aggregate behaviors
        all_behaviors = set()
        risk_levels = []
        
        for analysis in analyses:
            all_behaviors.update(analysis['detected_behaviors'])
            risk_levels.append(analysis['risk_level'])
        
        summary = f"Compared {len(analyses)} executions. "
        summary += f"Risk levels: {', '.join(risk_levels)}. "
        summary += f"Common behaviors: {', '.join(all_behaviors) if all_behaviors else 'None detected'}."
        
        return {
            'summary': summary,
            'unique_behaviors': list(all_behaviors),
            'risk_distribution': {level: risk_levels.count(level) for level in set(risk_levels)}
        }
    
    def get_timeline_comparison(self, pids: List[int], metric: str) -> Dict:
        """
        Compare timeline data across multiple executions.
        
        metric: 'cpu_percent', 'memory_kb', etc.
        """
        timelines = []
        
        for pid in pids:
            log = self.log_cache.get(pid)
            if not log:
                logs = self.load_all_logs()
                log = self.log_cache.get(pid)
            
            if log:
                timeline = log.get('timeline', {})
                if metric in timeline:
                    timelines.append({
                        'pid': pid,
                        'program': log.get('program', 'unknown'),
                        'profile': log.get('profile', 'UNKNOWN'),
                        'time_ms': timeline.get('time_ms', []),
                        'values': timeline.get(metric, [])
                    })
        
        return {
            'metric': metric,
            'timelines': timelines
        }
    
    def get_statistics_by_profile(self) -> Dict:
        """Aggregate statistics grouped by profile"""
        logs = self.load_all_logs()
        
        stats_by_profile = {}
        
        for log in logs:
            profile = log.get('profile', 'UNKNOWN')
            summary = log.get('summary', {})
            
            if profile not in stats_by_profile:
                stats_by_profile[profile] = {
                    'count': 0,
                    'peak_cpu_values': [],
                    'peak_memory_values': [],
                    'blocked_syscall_counts': [],
                    'exit_reasons': {}
                }
            
            stats = stats_by_profile[profile]
            stats['count'] += 1
            stats['peak_cpu_values'].append(summary.get('peak_cpu', 0))
            stats['peak_memory_values'].append(summary.get('peak_memory_kb', 0))
            stats['blocked_syscall_counts'].append(summary.get('blocked_syscalls', 0))
            
            exit_reason = summary.get('exit_reason', 'UNKNOWN')
            stats['exit_reasons'][exit_reason] = stats['exit_reasons'].get(exit_reason, 0) + 1
        
        # Compute aggregates
        for profile, stats in stats_by_profile.items():
            if stats['peak_cpu_values']:
                stats['avg_peak_cpu'] = int(np.mean(stats['peak_cpu_values']))
                stats['max_peak_cpu'] = int(np.max(stats['peak_cpu_values']))
            else:
                stats['avg_peak_cpu'] = 0
                stats['max_peak_cpu'] = 0
            
            if stats['peak_memory_values']:
                stats['avg_peak_memory'] = int(np.mean(stats['peak_memory_values']))
                stats['max_peak_memory'] = int(np.max(stats['peak_memory_values']))
            else:
                stats['avg_peak_memory'] = 0
                stats['max_peak_memory'] = 0
            
            stats['total_blocked_syscalls'] = sum(stats['blocked_syscall_counts'])
            
            # Clean up raw values
            del stats['peak_cpu_values']
            del stats['peak_memory_values']
            del stats['blocked_syscall_counts']
        
        return stats_by_profile

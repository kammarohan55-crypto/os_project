from flask import Flask, render_template, jsonify, request
import pandas as pd
import traceback
from ml_model import RiskClassifier
from analytics import load_all_logs, extract_features, compute_statistics, get_syscall_frequency
from analytics_engine import AnalyticsService
from risk_scoring import RiskScoringService

app = Flask(__name__)

# Global state (cached)
classifier = RiskClassifier()
cached_features = None
last_log_count = 0
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "logs"))

analytics_service = AnalyticsService(LOGS_DIR)
risk_scoring_service = RiskScoringService()  # Phase 5: Risk scoring

def get_feature_dataframe():
    """
    CRITICAL: Single source of truth for all data
    
    Returns: pandas DataFrame with extracted features
    """
    global cached_features, last_log_count
    
    try:
        logs = load_all_logs(LOGS_DIR)
        
        # Cache invalidation
        if len(logs) != last_log_count:
            print(f"[Analytics] Extracting features from {len(logs)} logs...")
            cached_features = extract_features(logs)
            last_log_count = len(logs)
            
            # Train ML once when data changes
            if len(cached_features) > 0:
                print(f"[ML] Training on {len(cached_features)} samples...")
                classifier.train(cached_features)
        
        return cached_features if cached_features is not None else pd.DataFrame()
    
    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        traceback.print_exc()
        return pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    """
    CRASH-RESISTANT: Always returns valid JSON
    """
    try:
        # Get original logs for timeline data
        original_logs = load_all_logs(LOGS_DIR)
        df = get_feature_dataframe()
        
        if df.empty:
            return jsonify({
                "total_runs": 0,
                "avg_cpu": 0,
                "avg_mem": 0,
                "violations": {},
                "runs": []
            })
        
        # Create a mapping of PID to original log (for timeline data)
        log_map = {log.get('pid'): log for log in original_logs}
        
        enriched_runs = []
        for idx, row in df.head(50).iterrows():
            try:
                # Enrich with ML predictions AND Heuristic Risk
                ml_result = classifier.predict(row.to_dict())
                run_data = row.to_dict()
                run_data.update(ml_result) # Adds 'prediction' and 'confidence'
                
                # HEURISTIC ANALYZER (Deterministically overrides ML for enforcement)
                # We need the full log to analyze properly
                pid = row.get('pid', 0)
                if pid in log_map:
                    log = log_map[pid]
                    analysis = analytics_service.analyzer.analyze_execution(log)
                    
                    # Logic 1: Heuristic Risk is the final authority
                    run_data['heuristic_risk'] = analysis.get('risk_level', 'UNKNOWN')
                    run_data['detected_behaviors'] = analysis.get('detected_behaviors', [])
                    
                    # Logic 2: Short-lived execution check (< 2 samples)
                    # We need to know if timeline exists and has samples
                    timeline = log.get('timeline', {})
                    time_samples = timeline.get('time_ms', [])
                    sample_count = len(time_samples)
                    
                    mem_metrics = analysis.get('metrics', {}).get('memory', {})
                    mem_growth = mem_metrics.get('memory_growth_kb', 0)
                    
                    peak_memory = log.get('summary', {}).get('peak_memory_kb', 0)
                    
                    behaviors = analysis.get('detected_behaviors', [])

                    if sample_count < 2:
                        exit_reason = log.get('summary', {}).get('exit_reason', 'UNKNOWN')
                        
                        # Rule 2b: If exited nicely, it's just a short utility.
                        if "EXITED(0)" in exit_reason:
                            run_data['final_risk'] = 'INFO'
                            run_data['heuristic_risk'] = 'SHORT_LIVED'
                            run_data['prediction'] = 'Ignored' 
                            run_data['confidence'] = 0
                            run_data['risk_reason'] = "Short-lived Utility (Benign)"
                            mem_growth = 0
                        else:
                            # Dangerous short-lived
                            risk_val = analysis.get('risk_level', 'UNKNOWN')
                            if risk_val == 'UNKNOWN':
                                risk_val = 'HIGH' if "VIOLATION" in exit_reason else 'MEDIUM'
                            
                            run_data['final_risk'] = risk_val
                            run_data['risk_reason'] = f"Short-lived but dangerous: {exit_reason}"
                            mem_growth = 0 
                    else:
                        # Normal Execution (> 2 samples)
                        risk_val = analysis.get('risk_level', 'UNKNOWN')
                        
                        # Explicitly map behaviors to dashboard risks with HIGH confidence
                        if 'MONOTONIC_MEMORY_GROWTH' in behaviors:
                            run_data['final_risk'] = 'HIGH'
                            run_data['heuristic_risk'] = 'MEMORY_LEAK'
                            run_data['prediction'] = 'Resource-Anomalous'
                            run_data['confidence'] = 98
                            run_data['risk_reason'] = "Heuristic: Severe Memory Leak Detected"

                        elif 'SUSTAINED_HIGH_CPU' in behaviors:
                            run_data['final_risk'] = 'MEDIUM'
                            run_data['heuristic_risk'] = 'CPU_HOG'
                            run_data['prediction'] = 'Resource-Anomalous'
                            run_data['confidence'] = 95
                            run_data['risk_reason'] = "Heuristic: Sustained High CPU Usage"
                        
                        elif 'POLICY_VIOLATION' in behaviors:
                             run_data['final_risk'] = 'HIGH'
                             run_data['heuristic_risk'] = 'SECURITY_VIOLATION'
                             run_data['prediction'] = 'Malicious'
                             run_data['risk_reason'] = "Heuristic: Policy Violation Trap"

                        # Fallback: Check risk_val directly if behaviors list missed it
                        elif risk_val == 'CPU_HOG':
                             run_data['final_risk'] = 'MEDIUM'
                             run_data['prediction'] = 'Resource-Anomalous'
                             run_data['confidence'] = 95
                             run_data['risk_reason'] = "Heuristic: CPU Usage Anomaly"
                             
                        elif risk_val == 'MEMORY_LEAK':
                             run_data['final_risk'] = 'HIGH'
                             run_data['prediction'] = 'Resource-Anomalous'
                             run_data['confidence'] = 98
                             run_data['risk_reason'] = "Heuristic: Memory Leak Anomaly"

                        elif risk_val == 'UNKNOWN':
                            # No anomalies detected. Check exit status.
                            exit_reason = log.get('summary', {}).get('exit_reason', 'UNKNOWN')
                            if "EXITED(0)" in exit_reason:
                                run_data['final_risk'] = 'LOW'
                                run_data['heuristic_risk'] = 'NORMAL'
                                run_data['prediction'] = 'Benign'
                                run_data['confidence'] = 100
                                run_data['risk_reason'] = "Normal Behavior (No Anomalies)"
                            else:
                                # Crashed/Killed but no specific anomaly detected
                                run_data['final_risk'] = 'MEDIUM'
                                run_data['risk_reason'] = f"Abnormal Exit: {exit_reason}"
                        else:
                             run_data['final_risk'] = risk_val

                    
                    # SPECIAL OVERRIDE: Whitelist /bin/echo (User Request)
                    if '/bin/echo' in str(log.get('program', '')):
                         run_data['final_risk'] = 'LOW'
                         run_data['heuristic_risk'] = 'OK'
                         run_data['prediction'] = 'Benign'
                         run_data['confidence'] = 99
                         run_data['risk_reason'] = "Whitelisted Utility (Known Safe)"

                    # Explicitly populate metrics expected by frontend
                    run_data['memory_growth_kb'] = mem_growth
                    run_data['memory_samples'] = sample_count
                    run_data['peak_memory_kb'] = peak_memory
                        
                else:
                    # Fallback if no log found
                    run_data['final_risk'] = 'UNKNOWN'
                    run_data['heuristic_risk'] = 'UNKNOWN'
                    run_data['memory_growth_kb'] = 0
                    run_data['memory_samples'] = 0
                        
                # Add timeline data
                if pid in log_map:
                    run_data['timeline'] = log_map[pid].get('timeline', {})
                else:
                    run_data['timeline'] = {'time_ms': [], 'cpu_percent': [], 'memory_kb': []}
                
                enriched_runs.append(run_data)
            except Exception as e:
                print(f"[WARNING] Processing failed for row {idx}: {e}")
                # Still include the row without ML/Risk
                run_data = row.to_dict()
                run_data['final_risk'] = 'UNKNOWN'
                run_data['timeline'] = {'time_ms': [], 'cpu_percent': [], 'memory_kb': []}
                enriched_runs.append(run_data)
        
        result = {
            "total_runs": len(df),
            "avg_cpu": int(df['peak_cpu'].mean()) if 'peak_cpu' in df.columns else 0,
            "avg_mem": int(df['peak_memory_kb'].mean()) if 'peak_memory_kb' in df.columns else 0,
            "violations": df['exit_reason'].value_counts().to_dict() if 'exit_reason' in df.columns else {},
            "runs": enriched_runs
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] /api/stats crashed: {e}")
        traceback.print_exc()
        return jsonify({"error": "Stats generation failed", "total_runs": 0, "runs": []}), 200

@app.route('/api/analytics')
def analytics():
    """Comprehensive analytics endpoint"""
    try:
        df = get_feature_dataframe()
        
        if df.empty:
            return jsonify({
                "statistics": {"total_runs": 0},
                "syscall_frequency": {},
                "total_logs": 0
            })
        
        stats = compute_statistics(df)
        syscall_freq = get_syscall_frequency(df)
        
        result = {
            "statistics": stats,
            "syscall_frequency": syscall_freq,
            "total_logs": len(df)
        }
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] /api/analytics crashed: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "statistics": {}}), 200

@app.route('/api/ml')
def ml_predictions():
    """ML predictions for recent runs"""
    try:
        df = get_feature_dataframe()
        
        if df.empty:
            return jsonify({"predictions": [], "model_info": {"trained": False}})
        
        predictions = []
        for idx, row in df.head(20).iterrows():
            try:
                pred = classifier.predict(row.to_dict())
                pred['program'] = row.get('program', 'unknown')
                pred['profile'] = row.get('profile', 'unknown')
                predictions.append(pred)
            except Exception as e:
                print(f"[WARNING] Prediction failed for row {idx}: {e}")
        
        return jsonify({
            "predictions": predictions,
            "model_info": {
                "type": "RandomForest",
                "features": ["runtime_ms", "peak_cpu", "peak_memory_kb", "page_faults_minor", "page_faults_major"],
                "trained": classifier.is_trained
            }
        })
    
    except Exception as e:
        print(f"[ERROR] /api/ml crashed: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "predictions": []}), 200

# ============================================================================
# PHASE 4: ANALYTICS & INTELLIGENCE ENDPOINTS
# ============================================================================

@app.route('/evaluation')
def evaluation():
    """Phase 6: System Comparison & Evaluation page"""
    return render_template('comparison.html')

@app.route('/analytics')
def analytics_page():
    """Serve the analytics & intelligence page"""
    return render_template('analytics.html')

@app.route('/api/analytics/executions')
def get_all_executions():
    """Get list of all executions with basic info and risk assessment"""
    try:
        logs = analytics_service.load_all_logs()
        
        executions = []
        for log in logs:
            pid = log.get('pid', 0)
            analysis = analytics_service.get_execution_analysis(pid)
            risk_score = risk_scoring_service.score_execution(analysis)
            
            # MANDATORY: Derive sample count directly from timeline
            timeline = log.get('timeline', {})
            # We strictly count time points to know valid samples
            time_samples = timeline.get('time_ms', [])
            sample_count = len(time_samples)
            
            # Safe extraction of memory metrics (relies on analytics_engine to calculate growth)
            mem_metrics = analysis.get('metrics', {}).get('memory', {})
            mem_growth = mem_metrics.get('memory_growth_kb', 0)
            
            # Logic 3: Enforcement Overrides based on sample count
            final_risk = analysis.get('risk_level', 'UNKNOWN')
            
            if sample_count < 2:
                final_risk = "SHORT_LIVED_UTILITY"
                # Override memory metrics for consistency
                mem_growth = 0 
                
            executions.append({
                'pid': pid,
                'program': log.get('program', 'unknown'),
                'profile': log.get('profile', 'UNKNOWN'),
                'runtime_ms': log.get('summary', {}).get('runtime_ms', 0),
                'peak_cpu': log.get('summary', {}).get('peak_cpu', 0),
                'peak_memory_kb': log.get('summary', {}).get('peak_memory_kb', 0),
                'memory_growth_kb': mem_growth,
                'memory_samples': sample_count,
                'blocked_syscalls': log.get('summary', {}).get('blocked_syscalls', 0),
                'exit_reason': log.get('summary', {}).get('exit_reason', 'UNKNOWN'),
                'risk_level': final_risk,
                'risk_score': risk_score['score'],
                'risk_classification': risk_score['risk_level']
            })
        
        return jsonify({'executions': executions})
    
    except Exception as e:
        print(f"[ERROR] Failed to get executions: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'executions': []}), 200

@app.route('/api/analytics/execution/<int:pid>')
def get_execution_analysis(pid):
    """Get detailed behavioral analysis for a single execution"""
    try:
        analysis = analytics_service.get_execution_analysis(pid)
        return jsonify(analysis)
    
    except Exception as e:
        print(f"[ERROR] Failed to analyze execution {pid}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'pid': pid}), 200

@app.route('/api/analytics/compare')
def compare_executions():
    """Compare multiple executions side-by-side"""
    try:
        pids_str = request.args.get('pids', '')
        pids = [int(p) for p in pids_str.split(',') if p.strip()]
        
        if not pids:
            return jsonify({'error': 'No PIDs provided'})
        
        result = analytics_service.compare_executions(pids)
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] Failed to compare executions: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200

@app.route('/api/analytics/timeline')
def get_timeline_comparison():
    """Compare timeline data across executions"""
    try:
        pids_str = request.args.get('pids', '')
        metric = request.args.get('metric', 'cpu_percent')
        
        pids = [int(p) for p in pids_str.split(',') if p.strip()]
        
        if not pids:
            return jsonify({'error': 'No PIDs provided'})
        
        result = analytics_service.get_timeline_comparison(pids, metric)
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] Failed to get timeline comparison: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200

@app.route('/api/analytics/stats-by-profile')
def get_stats_by_profile():
    """Get aggregate statistics by sandbox profile"""
    try:
        stats = analytics_service.get_statistics_by_profile()
        return jsonify(stats)
    
    except Exception as e:
        print(f"[ERROR] Failed to get profile statistics: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200

# ============================================================================
# PHASE 5: EXPLAINABLE RISK SCORING ENDPOINTS
# ============================================================================

@app.route('/api/risk-score/<int:pid>')
def get_risk_score(pid):
    """Get explainable risk score for a single execution"""
    try:
        analysis = analytics_service.get_execution_analysis(pid)
        risk_score_result = risk_scoring_service.score_execution(analysis)
        return jsonify(risk_score_result)
    
    except Exception as e:
        print(f"[ERROR] Failed to compute risk score for {pid}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'pid': pid}), 200

@app.route('/api/risk-scores')
def get_all_risk_scores():
    """Get risk scores for all executions with explanations"""
    try:
        logs = analytics_service.load_all_logs()
        
        risk_scores = []
        for log in logs:
            pid = log.get('pid', 0)
            analysis = analytics_service.get_execution_analysis(pid)
            risk_result = risk_scoring_service.score_execution(analysis)
            
            risk_scores.append({
                'pid': pid,
                'program': log.get('program', 'unknown'),
                'profile': log.get('profile', 'UNKNOWN'),
                'score': risk_result['score'],
                'risk_level': risk_result['risk_level'],
                'explanation': risk_result['explanation']
            })
        
        # Sort by risk score (descending)
        risk_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({'risk_scores': risk_scores})
    
    except Exception as e:
        print(f"[ERROR] Failed to get risk scores: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'risk_scores': []}), 200

@app.route('/api/risk-distribution')
def get_risk_distribution():
    """Get distribution of risk across all executions"""
    try:
        logs = analytics_service.load_all_logs()
        analyses = [analytics_service.get_execution_analysis(log.get('pid', 0)) for log in logs]
        
        distribution = risk_scoring_service.get_risk_distribution(analyses)
        return jsonify(distribution)
    
    except Exception as e:
        print(f"[ERROR] Failed to get risk distribution: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200

@app.route('/api/risk-profile-comparison')
def get_risk_by_profile():
    """Compare risk scores across sandbox profiles"""
    try:
        logs = analytics_service.load_all_logs()
        
        # Group analyses by profile
        profiles = {}
        for log in logs:
            profile = log.get('profile', 'UNKNOWN')
            pid = log.get('pid', 0)
            
            if profile not in profiles:
                profiles[profile] = []
            
            analysis = analytics_service.get_execution_analysis(pid)
            profiles[profile].append(analysis)
        
        # Compute comparison
        comparison = risk_scoring_service.compare_profile_risk(profiles)
        return jsonify(comparison)
    
    except Exception as e:
        print(f"[ERROR] Failed to get profile comparison: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200
@app.route('/api/analytics/scenario/<scenario_name>')
def get_scenario_analytics(scenario_name):
    """
    Get aggregated analytics for a specific scenario (Section B & C).
    Strict filtering and aggregation logic.
    """
    try:
        logs = analytics_service.load_all_logs()
        
        # 1. Filter logs based on Scenario Rules
        matching_logs = []
        for log in logs:
            timeline = log.get('timeline', {})
            summary = log.get('summary', {})
            exit_reason = summary.get('exit_reason', 'UNKNOWN')
            
            # Safe metric extraction
            cpu_samples = timeline.get('cpu_percent', [])
            mem_samples = timeline.get('memory_kb', [])
            sample_count = len(timeline.get('time_ms', []))
            peak_cpu = summary.get('peak_cpu', 0)
            
            mem_growth = 0
            if len(mem_samples) >= 2:
                mem_growth = mem_samples[-1] - mem_samples[0]
            
            is_match = False
            
            if scenario_name == 'cpu_stress':
                # Rule: max(cpu) >= 80 AND samples >= 5
                # Using summary peak_cpu is safer/faster
                if peak_cpu >= 80 and sample_count >= 5:
                    is_match = True
            
            elif scenario_name == 'memory_leak':
                # Rule: growth > 5000 AND samples >= 5
                if mem_growth > 5000 and sample_count >= 5:
                    is_match = True
                    
            elif scenario_name == 'policy_violation':
                # Rule: exit_reason == "SECURITY_VIOLATION"
                if "SECURITY_VIOLATION" in exit_reason:
                    is_match = True
                    
            elif scenario_name == 'normal_program':
                # Rule: EXITED(0) AND cpu < 50 AND growth == 0 (stable)
                if "EXITED(0)" in exit_reason and peak_cpu < 50 and mem_growth <= 100: # allow tiny fluctuation
                    is_match = True
            
            if is_match:
                matching_logs.append(log)
        
        if not matching_logs:
            return jsonify({'error': 'No matching executions found for this scenario', 'count': 0})

        # 2. Aggregate Metrics (Section B)
        runtimes = [l.get('summary', {}).get('runtime_ms', 0) for l in matching_logs]
        peak_cpus = [l.get('summary', {}).get('peak_cpu', 0) for l in matching_logs]
        peak_mems = [l.get('summary', {}).get('peak_memory_kb', 0) for l in matching_logs]
        
        avg_runtime = int(sum(runtimes) / len(runtimes))
        peak_cpu_range = f"{min(peak_cpus)}-{max(peak_cpus)}%"
        peak_mem_range = f"{min(peak_mems)}-{max(peak_mems)} KB"
        
        # Risk Distribution in selected set
        risk_counts = {}
        for l in matching_logs:
            pid = l.get('pid')
            analysis = analytics_service.get_execution_analysis(pid)
            risk = analysis.get('risk_level', 'UNKNOWN')
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
        dominant_risk = max(risk_counts, key=risk_counts.get) if risk_counts else "UNKNOWN"

        # 3. Calculate Overhead (Section C)
        # Compare STRICT vs LEARNING profiles - try specific scenario first, then fallback to all runs
        strict_apps = [l for l in matching_logs if l.get('profile') == 'STRICT']
        learning_apps = [l for l in matching_logs if l.get('profile') == 'LEARNING']
        
        overhead_pct = 0
        overhead_msg = "Not computed (Requires paired runs)"
        
        # If no paired runs in selected scenario, try ANY programs from all logs
        if not (strict_apps and learning_apps):
            # Fallback: Use any STRICT vs any LEARNING from entire dataset
            all_strict = [l for l in all_logs if l.get('profile') == 'STRICT']
            all_learning = [l for l in all_logs if l.get('profile') == 'LEARNING']
            
            if all_strict and all_learning:
                strict_apps = all_strict
                learning_apps = all_learning
        
        if strict_apps and learning_apps:
            avg_strict = sum([l.get('summary', {}).get('runtime_ms', 0) for l in strict_apps]) / len(strict_apps)
            avg_learning = sum([l.get('summary', {}).get('runtime_ms', 0) for l in learning_apps]) / len(learning_apps)
            
            if avg_learning > 0:
                overhead_pct = ((avg_strict - avg_learning) / avg_learning) * 100
                
                # Provide context about what was compared
                if len(strict_apps) == len(learning_apps) and strict_apps[0].get('program') == learning_apps[0].get('program'):
                    overhead_msg = f"{overhead_pct:.1f}% (Same Program: {len(strict_apps)} runs)"
                else:
                    overhead_msg = f"{overhead_pct:.1f}% (STRICT: {len(strict_apps)} runs vs LEARNING: {len(learning_apps)} runs)"
            else:
                overhead_msg = "Invalid Baseline (0ms)"
        
        # Detection Latency (Hardcoded Logic per rules)
        latency_val = "N/A"
        latency_reason = "No monitoring"
        
        if scenario_name == 'policy_violation':
            latency_val = "Immediate"
            latency_reason = "Kernel Trap (Seccomp)"
        elif scenario_name == 'normal_program':
            latency_val = "N/A"
            latency_reason = "No anomalies"
        else:
             latency_val = "~500 ms"
             latency_reason = "Heuristic (5 samples × 100ms)"

        return jsonify({
            'scenario': scenario_name,
            'count': len(matching_logs),
            'metrics': {
                'avg_runtime': avg_runtime,
                'peak_cpu_range': peak_cpu_range,
                'peak_mem_range': peak_mem_range,
                'dominant_risk': dominant_risk,
                'enforcement': "Blocked" if "violation" in scenario_name else "Allowed"
            },
            'analysis': {
                'overhead': overhead_msg,
                'latency': latency_val,
                'latency_reason': latency_reason
            },
            'samples': [l.get('pid') for l in matching_logs[:5]] # Return top 5 PIDs for proof
        })

    except Exception as e:
        print(f"[ERROR] Scenario analytics failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 200

if __name__ == '__main__':
    print("[Flask] Starting OS Sandbox Analytics Dashboard...")
    print("[Flask] Initializing ML model with seed data...")
    print("[Flask] Server ready at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)



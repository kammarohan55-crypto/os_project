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
analytics_service = AnalyticsService("../logs")
risk_scoring_service = RiskScoringService()  # Phase 5: Risk scoring

def get_feature_dataframe():
    """
    CRITICAL: Single source of truth for all data
    
    Returns: pandas DataFrame with extracted features
    """
    global cached_features, last_log_count
    
    try:
        logs = load_all_logs("../logs")
        
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
        original_logs = load_all_logs("../logs")
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
        
        # Enrich with ML predictions AND timeline
        enriched_runs = []
        for idx, row in df.head(50).iterrows():
            try:
                ml_result = classifier.predict(row.to_dict())
                run_data = row.to_dict()
                run_data.update(ml_result)
                
                # Add timeline from original log
                pid = row.get('pid', 0)
                if pid in log_map:
                    run_data['timeline'] = log_map[pid].get('timeline', {})
                else:
                    run_data['timeline'] = {'time_ms': [], 'cpu_percent': [], 'memory_kb': []}
                
                enriched_runs.append(run_data)
            except Exception as e:
                print(f"[WARNING] ML prediction failed for row {idx}: {e}")
                # Still include the row without ML
                run_data = row.to_dict()
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
            
            executions.append({
                'pid': pid,
                'program': log.get('program', 'unknown'),
                'profile': log.get('profile', 'UNKNOWN'),
                'runtime_ms': log.get('summary', {}).get('runtime_ms', 0),
                'peak_cpu': log.get('summary', {}).get('peak_cpu', 0),
                'peak_memory_kb': log.get('summary', {}).get('peak_memory_kb', 0),
                'blocked_syscalls': log.get('summary', {}).get('blocked_syscalls', 0),
                'exit_reason': log.get('summary', {}).get('exit_reason', 'UNKNOWN'),
                'risk_level': analysis.get('risk_level', 'UNKNOWN'),
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

if __name__ == '__main__':
    print("[Flask] Starting OS Sandbox Analytics Dashboard...")
    print("[Flask] Initializing ML model with seed data...")
    print("[Flask] Server ready at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)



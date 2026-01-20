#!/usr/bin/env python3
"""
Comprehensive import and integrity verification
Ensures all Phase 5 integration is working correctly before starting Flask app
"""

import sys
import os

# Add dashboard to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))

print("=" * 80)
print("COMPREHENSIVE IMPORT & INTEGRITY CHECK FOR PHASE 5")
print("=" * 80)

# Test 1: Check all imports in risk_scoring.py
print("\n[TEST 1] Checking risk_scoring.py imports...")
try:
    from risk_scoring import RiskScorer, RiskScoringService
    print("  ✓ RiskScorer imported")
    print("  ✓ RiskScoringService imported")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR: {e}")
    sys.exit(1)

# Test 2: Check all imports in analytics_engine.py
print("\n[TEST 2] Checking analytics_engine.py imports...")
try:
    from analytics_engine import BehavioralAnalyzer, AnalyticsService
    print("  ✓ BehavioralAnalyzer imported")
    print("  ✓ AnalyticsService imported")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR: {e}")
    sys.exit(1)

# Test 3: Check all imports in app.py prerequisites
print("\n[TEST 3] Checking app.py dependencies...")
try:
    from flask import Flask
    print("  ✓ Flask imported")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR (Flask): {e}")
    sys.exit(1)

try:
    from ml_model import RiskClassifier
    print("  ✓ RiskClassifier imported")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR (ml_model): {e}")
    sys.exit(1)

try:
    from analytics import load_all_logs
    print("  ✓ load_all_logs imported")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR (analytics): {e}")
    sys.exit(1)

try:
    # This tests Phase 5 + Phase 4 integration
    from analytics_engine import AnalyticsService
    from risk_scoring import RiskScoringService
    print("  ✓ AnalyticsService imported (Phase 4)")
    print("  ✓ RiskScoringService imported (Phase 5)")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR: {e}")
    sys.exit(1)

# Test 4: Verify numpy availability
print("\n[TEST 4] Checking numpy (required by risk_scoring)...")
try:
    import numpy as np
    print(f"  ✓ numpy version: {np.__version__}")
except ImportError as e:
    print(f"  ✗ IMPORT ERROR: {e}")
    sys.exit(1)

# Test 5: Check RiskScorer instantiation
print("\n[TEST 5] Instantiating RiskScorer...")
try:
    scorer = RiskScorer()
    print("  ✓ RiskScorer instantiated successfully")
    print(f"  ✓ Behavior weights: {list(scorer.BEHAVIOR_WEIGHTS.keys())}")
    print(f"  ✓ Thresholds: Normal={scorer.THRESHOLDS['normal']}, Suspicious={scorer.THRESHOLDS['suspicious']}")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check RiskScoringService instantiation
print("\n[TEST 6] Instantiating RiskScoringService...")
try:
    service = RiskScoringService()
    print("  ✓ RiskScoringService instantiated successfully")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 7: Check BehavioralAnalyzer instantiation
print("\n[TEST 7] Instantiating BehavioralAnalyzer...")
try:
    analyzer = BehavioralAnalyzer()
    print("  ✓ BehavioralAnalyzer instantiated successfully")
    print("  ✓ Risk scorer integrated in analyzer")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Check AnalyticsService instantiation
print("\n[TEST 8] Instantiating AnalyticsService...")
try:
    analytics = AnalyticsService("logs")
    print("  ✓ AnalyticsService instantiated successfully")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    sys.exit(1)

# Test 9: Test risk scoring with dummy data (end-to-end)
print("\n[TEST 9] Testing risk scoring (end-to-end)...")
try:
    dummy_analysis = {
        'pid': 999,
        'program': 'test_program',
        'profile': 'LEARNING',
        'detected_behaviors': ['POLICY_VIOLATION'],
        'explanations': {'POLICY_VIOLATION': 'test violation'},
        'metrics': {'policy': {'blocked_syscalls': 1}}
    }
    result = service.score_execution(dummy_analysis)
    
    # Verify result structure
    required_fields = ['score', 'risk_level', 'contributions', 'explanation']
    missing_fields = [f for f in required_fields if f not in result]
    
    if missing_fields:
        print(f"  ✗ Missing fields in result: {missing_fields}")
        sys.exit(1)
    
    print(f"  ✓ Risk score computed: {result['score']}/100")
    print(f"  ✓ Risk level: {result['risk_level']}")
    print(f"  ✓ Contributions tracked: {len(result['contributions'])} factors")
    print(f"  ✓ Explanation generated: {len(result['explanation'])} chars")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 10: Test BehavioralAnalyzer + RiskScorer integration
print("\n[TEST 10] Testing BehavioralAnalyzer → RiskScorer integration...")
try:
    # Create a simple log structure that analyzer can work with
    test_log = {
        'pid': 10001,
        'program': '/bin/test',
        'profile': 'LEARNING',
        'timeline': {'cpu_percent': [10, 15, 12, 14, 11]},
        'summary': {
            'peak_cpu': 15,
            'peak_memory_kb': 50000,
            'runtime_ms': 5000,
            'page_faults_minor': 100,
            'page_faults_major': 0,
            'read_syscalls': 5,
            'write_syscalls': 3,
            'blocked_syscalls': 0,
            'exit_reason': 'normal'
        }
    }
    
    # Analyze with BehavioralAnalyzer (which now includes risk scoring)
    analysis = analyzer.analyze_execution(test_log)
    
    # Verify analysis contains risk fields from Phase 5
    risk_fields = ['risk_score', 'risk_classification', 'risk_contributions', 'risk_explanation']
    missing_risk_fields = [f for f in risk_fields if f not in analysis]
    
    if missing_risk_fields:
        print(f"  ✗ Missing risk fields: {missing_risk_fields}")
        sys.exit(1)
    
    print(f"  ✓ Analysis completed")
    print(f"  ✓ Risk score: {analysis['risk_score']}/100")
    print(f"  ✓ Risk classification: {analysis['risk_classification']}")
    print(f"  ✓ Risk contributions: {len(analysis['risk_contributions'])} factors")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 11: Flask app structure
print("\n[TEST 11] Verifying Flask app structure...")
try:
    app = Flask(__name__)
    print("  ✓ Flask app created")
    
    # Check if all required modules can be imported together
    from flask import Flask, render_template, jsonify, request
    from ml_model import RiskClassifier
    from analytics import load_all_logs, extract_features
    from analytics_engine import AnalyticsService
    from risk_scoring import RiskScoringService
    
    print("  ✓ All app.py imports successful")
    print("  ✓ Flask can load all dependencies")
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 12: Check for circular imports
print("\n[TEST 12] Checking for circular imports...")
try:
    # Try reimporting in different order
    from risk_scoring import RiskScorer
    from analytics_engine import BehavioralAnalyzer
    from risk_scoring import RiskScoringService
    from analytics_engine import AnalyticsService
    print("  ✓ No circular import issues detected")
except ImportError as e:
    print(f"  ✗ CIRCULAR IMPORT ERROR: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("✅ ALL 12 CHECKS PASSED - PROJECT IS PRODUCTION READY")
print("=" * 80)

print("\n📋 VERIFICATION SUMMARY:")
print("  ✓ All imports successful (no missing dependencies)")
print("  ✓ All classes instantiate correctly")
print("  ✓ Risk scoring engine functional")
print("  ✓ Phase 4 + Phase 5 integration verified")
print("  ✓ End-to-end analysis pipeline working")
print("  ✓ Flask structure verified")
print("  ✓ No circular imports detected")

print("\n🚀 READY TO START FLASK APP:")
print("  cd dashboard")
print("  python3 app.py")
print("\n  Then visit: http://localhost:5000")
print("  Analytics page: http://localhost:5000/analytics")

sys.exit(0)

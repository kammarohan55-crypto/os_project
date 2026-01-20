"""
Phase 5: Explainable Risk Scoring Engine
Deterministic, transparent risk scoring based on behavioral analysis.

No machine learning, no randomization - purely rule-based scoring with clear explanations.
"""

from typing import Dict, List, Tuple, Any

class RiskScorer:
    """
    Deterministic risk scoring engine.
    Assigns weights to each behavioral indicator and computes a final risk score 0-100.
    
    Scoring Methodology:
    - Each detected behavior contributes to the risk score
    - Weights are transparent and documented
    - Final score is clamped to 0-100
    - Clear explanations provided for each contribution
    """
    
    # ========================================================================
    # SCORING WEIGHTS (Transparent & Documented)
    # ========================================================================
    
    # Base score for each detected behavior
    BEHAVIOR_WEIGHTS = {
        'SUSTAINED_HIGH_CPU': 15,           # Compute-intensive, but not inherently malicious
        'MONOTONIC_MEMORY_GROWTH': 25,      # Memory leak or resource exhaustion attempt
        'HIGH_IO_SYSCALL_RATE': 20,         # Excessive I/O or syscall flooding
        'POLICY_VIOLATION': 40,             # Attempted unauthorized syscall - HIGH RISK
    }
    
    # Multipliers for severity factors
    MULTIPLIERS = {
        'policy_violation_high_severity': 1.5,  # If policy violation in STRICT profile
        'combined_behaviors': 1.2,               # If 2+ behaviors detected
        'multi_combined_behaviors': 1.5,        # If 3+ behaviors detected
    }
    
    # Risk level thresholds
    THRESHOLDS = {
        'normal': 30,           # 0-30: Normal
        'suspicious': 60,       # 31-60: Suspicious
        'malicious': 100,       # 61-100: Malicious
    }
    
    def __init__(self):
        self.score_cache = {}
    
    def compute_risk_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute deterministic risk score for an execution.
        
        Returns dict with:
        - score: Integer 0-100
        - risk_level: "Normal", "Suspicious", "Malicious"
        - contributions: List of (behavior, weight, explanation)
        - explanation: Plain text explanation
        """
        pid = analysis.get('pid', 0)
        
        # Check cache
        if pid in self.score_cache:
            return self.score_cache[pid]
        
        detected_behaviors = analysis.get('detected_behaviors', [])
        explanations = analysis.get('explanations', {})
        metrics = analysis.get('metrics', {})
        profile = analysis.get('profile', 'UNKNOWN')
        
        # Initialize score calculation
        base_score = 0
        contributions = []
        
        # ====================================================================
        # STEP 1: Add base weights for each detected behavior
        # ====================================================================
        for behavior in detected_behaviors:
            if behavior in self.BEHAVIOR_WEIGHTS:
                weight = self.BEHAVIOR_WEIGHTS[behavior]
                base_score += weight
                contributions.append({
                    'behavior': behavior,
                    'weight': weight,
                    'reason': f"{behavior} detected"
                })
        
        # ====================================================================
        # STEP 2: Apply multipliers for severity factors
        # ====================================================================
        multiplier = 1.0
        
        # Policy violation in strict profile = very high risk
        if 'POLICY_VIOLATION' in detected_behaviors and profile == 'STRICT':
            multiplier *= self.MULTIPLIERS['policy_violation_high_severity']
            contributions.append({
                'behavior': 'POLICY_VIOLATION_STRICT',
                'weight': f"+{int((multiplier - 1.0) * 100)}%",
                'reason': "Policy violation in STRICT profile (maximum enforcement)"
            })
        
        # Multiple behaviors detected = compounding risk
        if len(detected_behaviors) >= 3:
            multiplier *= self.MULTIPLIERS['multi_combined_behaviors']
            contributions.append({
                'behavior': 'MULTIPLE_BEHAVIORS',
                'weight': f"+{int((multiplier - 1.0) * 100)}%",
                'reason': "3+ behaviors detected (compounding risk indicators)"
            })
        elif len(detected_behaviors) >= 2:
            multiplier *= self.MULTIPLIERS['combined_behaviors']
            contributions.append({
                'behavior': 'COMBINED_BEHAVIORS',
                'weight': f"+{int((multiplier - 1.0) * 100)}%",
                'reason': "2+ behaviors detected (combined risk indicators)"
            })
        
        # ====================================================================
        # STEP 3: Apply multiplier and clamp to 0-100
        # ====================================================================
        final_score = int(base_score * multiplier)
        final_score = max(0, min(100, final_score))  # Clamp to 0-100
        
        # ====================================================================
        # STEP 4: Determine risk level
        # ====================================================================
        if final_score <= self.THRESHOLDS['normal']:
            risk_level = 'NORMAL'
            risk_description = 'Normal execution behavior'
        elif final_score <= self.THRESHOLDS['suspicious']:
            risk_level = 'SUSPICIOUS'
            risk_description = 'Suspicious behavior detected'
        else:
            risk_level = 'MALICIOUS'
            risk_description = 'High-risk behavior detected'
        
        # ====================================================================
        # STEP 5: Generate explanation
        # ====================================================================
        if len(detected_behaviors) == 0:
            explanation = (
                "No anomalous behaviors detected. Process executed normally "
                "with minimal resource usage and no policy violations. "
                "This execution appears safe."
            )
        else:
            behavior_list = ", ".join(detected_behaviors)
            explanation = (
                f"Risk Score: {final_score}/100 ({risk_description}). "
                f"Detected behaviors: {behavior_list}. "
            )
            
            if 'POLICY_VIOLATION' in detected_behaviors:
                explanation += (
                    "Security-critical finding: Process attempted unauthorized system calls "
                    "that were blocked by the sandbox policy. "
                )
            
            if 'SUSTAINED_HIGH_CPU' in detected_behaviors:
                cpu_metrics = metrics.get('cpu', {})
                sustained = cpu_metrics.get('sustained_percentage', 0)
                explanation += (
                    f"Process sustained high CPU usage ({sustained:.0f}% of runtime). "
                )
            
            if 'MONOTONIC_MEMORY_GROWTH' in detected_behaviors:
                mem_metrics = metrics.get('memory', {})
                growth = mem_metrics.get('total_growth_kb', 0)
                explanation += (
                    f"Memory grew significantly ({growth/1024:.1f} MB). "
                )
            
            if 'HIGH_IO_SYSCALL_RATE' in detected_behaviors:
                io_metrics = metrics.get('io', {})
                rate = io_metrics.get('syscalls_per_100ms', 0)
                explanation += (
                    f"Abnormal I/O syscall rate ({rate:.1f} per 100ms). "
                )
            
            if multiplier > 1.0:
                explanation += f"(Risk amplified {multiplier:.1f}x due to compounding factors.)"
        
        # ====================================================================
        # BUILD RESULT
        # ====================================================================
        result = {
            'pid': pid,
            'score': final_score,
            'risk_level': risk_level,
            'threshold_normal': self.THRESHOLDS['normal'],
            'threshold_suspicious': self.THRESHOLDS['suspicious'],
            'threshold_malicious': self.THRESHOLDS['malicious'],
            'base_score': base_score,
            'multiplier': multiplier,
            'contributions': contributions,
            'explanation': explanation,
            'scoring_methodology': self._get_methodology()
        }
        
        self.score_cache[pid] = result
        return result
    
    def _get_methodology(self) -> str:
        """Return explanation of scoring methodology"""
        return (
            "SCORING METHODOLOGY:\n"
            "1. Base Score: Each detected behavior adds fixed weight\n"
            f"   - SUSTAINED_HIGH_CPU: +{self.BEHAVIOR_WEIGHTS['SUSTAINED_HIGH_CPU']} points\n"
            f"   - MONOTONIC_MEMORY_GROWTH: +{self.BEHAVIOR_WEIGHTS['MONOTONIC_MEMORY_GROWTH']} points\n"
            f"   - HIGH_IO_SYSCALL_RATE: +{self.BEHAVIOR_WEIGHTS['HIGH_IO_SYSCALL_RATE']} points\n"
            f"   - POLICY_VIOLATION: +{self.BEHAVIOR_WEIGHTS['POLICY_VIOLATION']} points\n"
            "\n2. Multipliers (amplify risk for compounding factors)\n"
            f"   - Policy violation in STRICT: ×{self.MULTIPLIERS['policy_violation_high_severity']}\n"
            f"   - 2+ behaviors: ×{self.MULTIPLIERS['combined_behaviors']}\n"
            f"   - 3+ behaviors: ×{self.MULTIPLIERS['multi_combined_behaviors']}\n"
            "\n3. Final Score: (Base Score × Multiplier) clamped to 0-100\n"
            "\n4. Classification:\n"
            f"   - 0–{self.THRESHOLDS['normal']}: NORMAL\n"
            f"   - {self.THRESHOLDS['normal']+1}–{self.THRESHOLDS['suspicious']}: SUSPICIOUS\n"
            f"   - {self.THRESHOLDS['suspicious']+1}–100: MALICIOUS"
        )
    
    def get_risk_profile_comparison(self, profile_scores: Dict[str, List[int]]) -> Dict[str, Any]:
        """
        Compare risk profiles across multiple executions.
        
        Input: {profile_name: [score1, score2, ...], ...}
        Returns aggregated statistics
        """
        import numpy as np
        
        comparison = {}
        for profile, scores in profile_scores.items():
            if scores:
                comparison[profile] = {
                    'count': len(scores),
                    'avg_score': float(np.mean(scores)),
                    'max_score': int(np.max(scores)),
                    'min_score': int(np.min(scores)),
                    'median_score': float(np.median(scores)),
                    'std_dev': float(np.std(scores)) if len(scores) > 1 else 0.0,
                    'high_risk_count': sum(1 for s in scores if s > self.THRESHOLDS['suspicious']),
                    'suspicious_count': sum(1 for s in scores if self.THRESHOLDS['normal'] < s <= self.THRESHOLDS['suspicious']),
                    'normal_count': sum(1 for s in scores if s <= self.THRESHOLDS['normal']),
                }
        
        return comparison


class RiskScoringService:
    """High-level service for risk scoring integrated with analytics"""
    
    def __init__(self):
        self.scorer = RiskScorer()
    
    def score_execution(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single execution"""
        return self.scorer.compute_risk_score(analysis)
    
    def score_batch(self, analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple executions"""
        return [self.scorer.compute_risk_score(a) for a in analyses]
    
    def compare_profile_risk(self, analyses_by_profile: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Compare risk across profiles"""
        profile_scores = {}
        
        for profile, analyses in analyses_by_profile.items():
            scores = []
            for analysis in analyses:
                score_result = self.scorer.compute_risk_score(analysis)
                scores.append(score_result['score'])
            profile_scores[profile] = scores
        
        return self.scorer.get_risk_profile_comparison(profile_scores)
    
    def get_risk_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get distribution of risk across executions"""
        scores = []
        for analysis in analyses:
            score_result = self.scorer.compute_risk_score(analysis)
            scores.append(score_result['score'])
        
        import numpy as np
        if not scores:
            return {'error': 'No scores to analyze'}
        
        return {
            'total_executions': len(scores),
            'avg_risk': float(np.mean(scores)),
            'median_risk': float(np.median(scores)),
            'max_risk': int(np.max(scores)),
            'min_risk': int(np.min(scores)),
            'risk_distribution': {
                'normal': sum(1 for s in scores if s <= RiskScorer.THRESHOLDS['normal']),
                'suspicious': sum(1 for s in scores if RiskScorer.THRESHOLDS['normal'] < s <= RiskScorer.THRESHOLDS['suspicious']),
                'malicious': sum(1 for s in scores if s > RiskScorer.THRESHOLDS['suspicious']),
            }
        }

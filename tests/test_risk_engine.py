"""
Unit tests for core ThreatSense-AI Risk Engine components.
Run with: python -m pytest tests/test_risk_engine.py -v
"""

import unittest
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.threat_classifier import ThreatClassifier
from engine.behavior_fusion import BehaviorFusion
from engine.risk_calculator import RiskCalculator
from memory.person_memory import PersonMemory
from alerts.alert_rules import AlertRules


class TestThreatClassifier(unittest.TestCase):
    """Tests for threat level classification."""
    
    def setUp(self):
        self.classifier = ThreatClassifier()
    
    def test_normal_score(self):
        self.assertEqual(self.classifier.classify(10), "NORMAL")
    
    def test_low_score(self):
        self.assertEqual(self.classifier.classify(25), "LOW")
        
    def test_suspicious_score(self):
        self.assertEqual(self.classifier.classify(55), "SUSPICIOUS")
    
    def test_high_risk_score(self):
        self.assertEqual(self.classifier.classify(85), "HIGH_RISK")
    
    def test_critical_score(self):
        self.assertEqual(self.classifier.classify(150), "CRITICAL")
    
    def test_boundary_normal_low(self):
        self.assertEqual(self.classifier.classify(19), "NORMAL")
        self.assertEqual(self.classifier.classify(20), "LOW")
    
    def test_boundary_high_critical(self):
        self.assertEqual(self.classifier.classify(99), "HIGH_RISK")
        self.assertEqual(self.classifier.classify(100), "CRITICAL")


class TestBehaviorFusion(unittest.TestCase):
    """Tests for behavior fusion logic."""
    
    def setUp(self):
        self.fusion = BehaviorFusion()
    
    def test_loitering_plus_intrusion(self):
        bonus, reasons = self.fusion.apply_fusion(["loitering", "zone_intrusion"], 55)
        self.assertGreater(bonus, 0)
        self.assertTrue(any("Synergy" in r for r in reasons))
    
    def test_weapon_plus_intrusion_forces_critical(self):
        bonus, reasons = self.fusion.apply_fusion(["zone_intrusion", "weapon_detected"], 50)
        self.assertGreaterEqual(50 + bonus, 100)
    
    def test_no_fusion_single_behavior(self):
        bonus, reasons = self.fusion.apply_fusion(["loitering"], 20)
        self.assertEqual(bonus, 0)
        self.assertEqual(len(reasons), 0)


class TestRiskCalculator(unittest.TestCase):
    """Tests for risk score computation."""
    
    def setUp(self):
        self.calculator = RiskCalculator()
    
    def test_single_behavior_loitering(self):
        memory = PersonMemory(person_id=1)
        behaviors = {"loitering": True, "zone_intrusion": False, "weapon_detected": False}
        score, reasons, active = self.calculator.compute_score(behaviors, memory)
        self.assertEqual(score, 20)
        self.assertIn("loitering", active)
    
    def test_no_behaviors(self):
        memory = PersonMemory(person_id=2)
        behaviors = {"loitering": False, "zone_intrusion": False, "weapon_detected": False}
        score, reasons, active = self.calculator.compute_score(behaviors, memory)
        self.assertEqual(score, 0)
        self.assertEqual(len(active), 0)
    
    def test_history_penalty(self):
        memory = PersonMemory(person_id=3, loiter_count=3, zone_intrusions=1)
        behaviors = {"loitering": True, "zone_intrusion": False, "weapon_detected": False}
        score, reasons, active = self.calculator.compute_score(behaviors, memory)
        # Should be base 20 + history penalties
        self.assertGreater(score, 20)


class TestAlertRules(unittest.TestCase):
    """Tests for alert triggering rules."""
    
    def setUp(self):
        self.rules = AlertRules()
    
    def test_weapon_always_alerts(self):
        decision = {"risk_score": 10, "behaviors": ["weapon_detected"]}
        self.assertTrue(self.rules.should_alert(decision))
    
    def test_high_score_alerts(self):
        decision = {"risk_score": 75, "behaviors": ["zone_intrusion"]}
        self.assertTrue(self.rules.should_alert(decision))
    
    def test_low_score_no_alert(self):
        decision = {"risk_score": 15, "behaviors": ["loitering"]}
        self.assertFalse(self.rules.should_alert(decision))
    
    def test_critical_priority(self):
        decision = {"risk_score": 110, "behaviors": ["weapon_detected"]}
        self.assertEqual(self.rules.get_alert_priority(decision), "CRITICAL_ALARM")


if __name__ == "__main__":
    unittest.main()

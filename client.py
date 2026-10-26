# -*- coding: utf-8 -*-
"""
Glance Screen Zero Ambient Intent Scorer Client
Evaluates real-time user intent from ambient lock-screen micro-moments.
Zero external dependencies -- Python 3.9+ standard library only.
"""

import math
from typing import Dict, Any, List

class GlanceScreenZeroAmbientIntentScorer:
    """
    Evaluates lock-screen dwell attention, swipe physics, and circadian context
    to score zero-click purchase intent with zero user friction.
    """

    CIRCADIAN_HOURLY_BIAS = {
        0: 0.15, 1: 0.10, 2: 0.05, 3: 0.05, 4: 0.08, 5: 0.12,
        6: 0.25, 7: 0.45, 8: 0.70, 9: 0.65, 10: 0.60, 11: 0.65,
        12: 0.85, 13: 0.75, 14: 0.55, 15: 0.50, 16: 0.58, 17: 0.68,
        18: 0.78, 19: 0.82, 20: 0.88, 21: 0.95, 22: 0.90, 23: 0.40
    }

    def __init__(self, baseline_dwell_inflection: float = 1.8, idle_decay_threshold: float = 6.0):
        self.t0 = baseline_dwell_inflection
        self.idle_t = idle_decay_threshold

    def calculate_dwell_attention(self, dwell_sec: float) -> float:
        """Sigmoid engagement curve with idle timeout attenuation."""
        if dwell_sec <= 0.2:
            return 0.05
        # Sigmoidal growth
        k = 1.8
        growth = 1.0 / (1.0 + math.exp(-k * (dwell_sec - self.t0)))
        # Decay if prolonged without interaction (user set phone down while on lock screen)
        if dwell_sec > self.idle_t:
            decay = math.exp(-0.25 * (dwell_sec - self.idle_t))
            return max(0.1, growth * decay)
        return min(1.0, growth)

    def calculate_swipe_physics_intent(self, velocity_px_s: float, angle_deg: float) -> float:
        """
        Differentiates quick dismissals (rapid vertical swipe up)
        from horizontal glance browsing (slow horizontal drag).
        """
        rad = math.radians(angle_deg % 180)
        horizontal_intent = abs(math.cos(rad))  # 1.0 = purely horizontal (browsing), 0.0 = purely vertical (dismiss/unlock)
        velocity_damping = 1.0 / (1.0 + 0.0025 * max(0.0, velocity_px_s))
        return horizontal_intent * velocity_damping

    def score_ambient_intent(
        self,
        dwell_time_sec: float,
        swipe_velocity_px_s: float = 0.0,
        swipe_angle_deg: float = 0.0,
        wake_hour_of_day: int = 12,
        wake_frequency_last_hour: int = 3,
        historical_category_affinities: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Computes composite zero-click purchase intent score.
        """
        if historical_category_affinities is None:
            historical_category_affinities = {
                "Luxury Fashion": 0.5,
                "Beauty & Skincare": 0.5,
                "Consumer Tech": 0.5,
                "Home Living": 0.5
            }

        attention_score = self.calculate_dwell_attention(dwell_time_sec)
        swipe_intent = self.calculate_swipe_physics_intent(swipe_velocity_px_s, swipe_angle_deg)
        hour = max(0, min(23, int(wake_hour_of_day)))
        circadian_factor = self.CIRCADIAN_HOURLY_BIAS.get(hour, 0.5)

        # Frequent repetitive wakes indicate check-in mode or waiting/idling
        freq_factor = min(1.0, max(0.2, wake_frequency_last_hour / 8.0))

        # Composite Intent Model: 40% Attention + 25% Physics + 20% Circadian + 15% Wake Freq
        raw_composite = (
            0.40 * attention_score +
            0.25 * swipe_intent +
            0.20 * circadian_factor +
            0.15 * freq_factor
        )
        intent_index = round(min(100.0, max(0.0, raw_composite * 100.0)), 2)

        # Categorization & Action Recommendation
        if dwell_time_sec < 0.8:
            attention_grade = "MICRO_GLANCE"
            action = "PASSIVE_BACKGROUND"
        elif dwell_time_sec <= 2.5:
            attention_grade = "ACTIVE_INSPECT"
            action = "SURFACE_PRODUCT_TEASER"
        elif dwell_time_sec <= 6.0:
            attention_grade = "DEEP_ENGAGEMENT"
            action = "EXPAND_INTERACTIVE_TRAY"
        else:
            attention_grade = "IDLE_TIMEOUT"
            action = "DIM_LOCK_SCREEN"

        # Predict primary category by weighting affinities with circadian context
        scored_categories = {}
        for cat, base_aff in historical_category_affinities.items():
            category_score = round(base_aff * (0.6 + 0.4 * circadian_factor) * 100.0, 1)
            scored_categories[cat] = category_score

        primary_category = max(scored_categories, key=scored_categories.get)

        return {
            "composite_intent_score": intent_index,
            "intent_confidence_tier": "HIGH" if intent_index >= 70 else ("MODERATE" if intent_index >= 45 else "LOW"),
            "attention_grade": attention_grade,
            "recommended_screen_zero_action": action,
            "components": {
                "dwell_attention_score": round(attention_score, 4),
                "swipe_physics_score": round(swipe_intent, 4),
                "circadian_hourly_bias": round(circadian_factor, 4),
                "wake_frequency_factor": round(freq_factor, 4)
            },
            "top_predicted_category": primary_category,
            "category_affinity_distribution": scored_categories
        }

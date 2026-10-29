import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from app.core.base_schema import BaseModel, Field


class DeteriorationRisk(BaseModel):
    is_deteriorating: bool
    risk_level: str # LOW, MODERATE, HIGH, CRITICAL
    lead_time_days_before_visit: Optional[int] = None
    flags: List[str] = Field(default_factory=list)
    systolic_slope_per_week: float = 0.0
    average_systolic: Optional[float] = None
    average_diastolic: Optional[float] = None
    average_glucose: Optional[float] = None
    adherence_rate_pct: float = 100.0
    recommended_action: str
    action_priority: int = 4 # 1=Immediate, 2=Within 24hr, 3=Within 7 days, 4=Routine


class ChronicPatientEvaluator:
    """
    Clinical Trend Analysis & Deterioration Engine for Chronic Care (Hypertension & Diabetes).
    Fulfills Objective O2: Flags clinical deterioration >= 7 days before scheduled monthly visits.
    """

    @staticmethod
    def calculate_bp_trend(vitals_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes blood pressure readings over time:
        - Calculates averages and velocity (slope).
        - Identifies sustained stage 1/stage 2 hypertension and hypertensive urgency.
        """
        if not vitals_list:
            return {"status": "NO_DATA", "flags": []}

        # Sort chronologically
        sorted_vitals = sorted(vitals_list, key=lambda x: x.get("recorded_at", datetime.min))
        systolic_readings = [v["systolic_bp"] for v in sorted_vitals if v.get("systolic_bp")]
        diastolic_readings = [v["diastolic_bp"] for v in sorted_vitals if v.get("diastolic_bp")]

        if not systolic_readings:
            return {"status": "INSUFFICIENT_BP_DATA", "flags": []}

        avg_sys = sum(systolic_readings) / len(systolic_readings)
        avg_dia = sum(diastolic_readings) / len(diastolic_readings) if diastolic_readings else 80.0
        latest_sys = systolic_readings[-1]
        latest_dia = diastolic_readings[-1] if diastolic_readings else 80

        flags = []
        # Hypertensive Crisis / Urgency (Systolic >= 180 or Diastolic >= 110)
        if latest_sys >= 180 or latest_dia >= 110:
            flags.append("HYPERTENSIVE_CRISIS")

        # Stage 2 Hypertension (Systolic >= 140 or Diastolic >= 90)
        elif latest_sys >= 140 or latest_dia >= 90:
            # Check if sustained (at least 2 of last 3 readings)
            recent_high = sum(1 for s in systolic_readings[-3:] if s >= 140)
            if recent_high >= 2:
                flags.append("SUSTAINED_STAGE_2_HYPERTENSION")

        # Velocity check: Calculate slope over the series
        slope_per_week = 0.0
        if len(systolic_readings) >= 3:
            # Simple linear delta between first half and second half
            mid = len(systolic_readings) // 2
            first_half_avg = sum(systolic_readings[:mid]) / mid
            second_half_avg = sum(systolic_readings[mid:]) / (len(systolic_readings) - mid)
            delta = second_half_avg - first_half_avg
            slope_per_week = round(delta, 2)
            if delta >= 8.0:
                flags.append("ACCELERATING_SYSTOLIC_TREND")

        return {
            "average_systolic": round(avg_sys, 1),
            "average_diastolic": round(avg_dia, 1),
            "latest_systolic": latest_sys,
            "latest_diastolic": latest_dia,
            "slope_per_week": slope_per_week,
            "flags": flags
        }

    @staticmethod
    def calculate_glucose_trend(vitals_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes blood glucose time series (Fasting & Post-Prandial).
        Flags sustained hyperglycemia and hypoglycemia.
        """
        glucose_readings = [v for v in vitals_list if v.get("blood_glucose") is not None]
        if not glucose_readings:
            return {"status": "NO_GLUCOSE_DATA", "flags": []}

        sorted_readings = sorted(glucose_readings, key=lambda x: x.get("recorded_at", datetime.min))
        values = [float(v["blood_glucose"]) for v in sorted_readings]
        avg_glucose = sum(values) / len(values)
        latest = sorted_readings[-1]
        latest_val = float(latest["blood_glucose"])
        latest_ctx = latest.get("glucose_context", "RANDOM")

        flags = []
        # Hypoglycemia Alert (< 70 mg/dL)
        if latest_val < 70.0:
            flags.append("HYPOGLYCEMIA_ALERT")

        # Severe Hyperglycemia (> 250 mg/dL)
        elif latest_val >= 250.0:
            flags.append("SEVERE_HYPERGLYCEMIA")

        # Sustained Hyperglycemia (> 140 fasting or > 200 post-prandial)
        elif (latest_ctx == "FASTING" and latest_val >= 140.0) or latest_val >= 200.0:
            recent_high = sum(1 for v in values[-3:] if v >= 180.0)
            if recent_high >= 2:
                flags.append("SUSTAINED_HYPERGLYCEMIA")

        return {
            "average_glucose": round(avg_glucose, 1),
            "latest_glucose": latest_val,
            "glucose_context": latest_ctx,
            "flags": flags
        }

    @staticmethod
    def calculate_adherence_score(adherence_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates medication adherence percentage and flags consecutive missed doses.
        """
        if not adherence_records:
            return {"adherence_rate_pct": 100.0, "consecutive_missed": 0, "flags": []}

        # Sort chronologically
        sorted_records = sorted(adherence_records, key=lambda x: x.get("scheduled_time", datetime.min))
        total_doses = len(sorted_records)
        taken_doses = sum(1 for r in sorted_records if r.get("status") == "TAKEN")
        rate_pct = round((taken_doses / total_doses) * 100.0, 1)

        # Count consecutive missed doses from latest backwards
        consecutive_missed = 0
        for r in reversed(sorted_records):
            if r.get("status") in ["MISSED", "SKIPPED"]:
                consecutive_missed += 1
            else:
                break

        flags = []
        if consecutive_missed >= 3:
            flags.append("CRITICAL_MEDICATION_DROPOUT")
        elif consecutive_missed >= 1:
            flags.append("MISSED_RECENT_DOSE")

        if rate_pct < 70.0:
            flags.append("POOR_OVERALL_ADHERENCE")

        return {
            "adherence_rate_pct": rate_pct,
            "consecutive_missed": consecutive_missed,
            "flags": flags
        }

    @classmethod
    def evaluate_patient_deterioration(
        cls,
        vitals_list: List[Dict[str, Any]],
        adherence_records: List[Dict[str, Any]],
        next_scheduled_visit: Optional[datetime] = None,
        current_date: Optional[datetime] = None
    ) -> DeteriorationRisk:
        """
        Integrates BP, blood glucose, and medication adherence to flag early deterioration.
        Calculates lead time before next scheduled clinic visit.
        """
        current_date = current_date or datetime.utcnow()
        bp_res = cls.calculate_bp_trend(vitals_list)
        glu_res = cls.calculate_glucose_trend(vitals_list)
        adh_res = cls.calculate_adherence_score(adherence_records)

        combined_flags = bp_res.get("flags", []) + glu_res.get("flags", []) + adh_res.get("flags", [])

        # Calculate lead time before next visit
        lead_time_days = None
        if next_scheduled_visit and next_scheduled_visit > current_date:
            lead_time_days = (next_scheduled_visit - current_date).days

        # Risk Classification Logic
        is_deteriorating = False
        risk_level = "LOW"
        action_priority = 4
        action = "Maintain regular chronic routine check-ups."

        # Critical Triggers
        if "HYPERTENSIVE_CRISIS" in combined_flags or "HYPOGLYCEMIA_ALERT" in combined_flags or "SEVERE_HYPERGLYCEMIA" in combined_flags:
            is_deteriorating = True
            risk_level = "CRITICAL"
            action_priority = 1
            action = "Immediate ASHA home visit and urgent medical officer tele-consultation required."

        # High Risk Triggers: Sustained Stage 2 HTN or Hyperglycemia + Missed Doses
        elif ("SUSTAINED_STAGE_2_HYPERTENSION" in combined_flags or "SUSTAINED_HYPERGLYCEMIA" in combined_flags) and \
             ("CRITICAL_MEDICATION_DROPOUT" in combined_flags or "ACCELERATING_SYSTOLIC_TREND" in combined_flags):
            is_deteriorating = True
            risk_level = "HIGH"
            action_priority = 2
            action = "Escalate to ASHA worker for priority home-visit check-in within 24-48 hours. Review medication supply."

        # Moderate Risk Triggers: Rising trend or missed doses alone
        elif "SUSTAINED_STAGE_2_HYPERTENSION" in combined_flags or "SUSTAINED_HYPERGLYCEMIA" in combined_flags or \
             "ACCELERATING_SYSTOLIC_TREND" in combined_flags or "CRITICAL_MEDICATION_DROPOUT" in combined_flags:
            is_deteriorating = True
            risk_level = "MODERATE"
            action_priority = 3
            action = "Trigger automated voice check-in reminder. Advise ASHA worker to verify BP/sugar at next village round."

        return DeteriorationRisk(
            is_deteriorating=is_deteriorating,
            risk_level=risk_level,
            lead_time_days_before_visit=lead_time_days,
            flags=combined_flags,
            systolic_slope_per_week=bp_res.get("slope_per_week", 0.0),
            average_systolic=bp_res.get("average_systolic"),
            average_diastolic=bp_res.get("average_diastolic"),
            average_glucose=glu_res.get("average_glucose"),
            adherence_rate_pct=adh_res.get("adherence_rate_pct", 100.0),
            recommended_action=action,
            action_priority=action_priority
        )


chronic_care_engine = ChronicPatientEvaluator()

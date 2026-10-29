import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app.services.chronic_care import chronic_care_engine, DeteriorationRisk


class SyntheticCohortBenchmark:
    """
    Synthea-style longitudinal chronic care simulator for Hypertension and Diabetes cohorts.
    Evaluates Objective O2: Deterioration flagged >= 7 days before next scheduled clinic visit.
    """

    @staticmethod
    def generate_patient_history(
        patient_id: str,
        is_deteriorating: bool = False,
        deterioration_start_day: int = 14,
        total_days: int = 30
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], datetime, datetime]:
        """
        Generates simulated daily BP, blood glucose, and medication adherence records.
        """
        base_date = datetime(2026, 1, 1, 9, 0, 0)
        scheduled_visit = base_date + timedelta(days=total_days)

        vitals_list = []
        adherence_records = []

        baseline_sys = 124.0
        baseline_dia = 80.0
        baseline_glu = 110.0

        for day in range(1, total_days + 1):
            curr_time = base_date + timedelta(days=day)

            # Determine trajectory
            if is_deteriorating and day >= deterioration_start_day:
                # Progressive deterioration
                days_since = day - deterioration_start_day
                sys = baseline_sys + (days_since * 2.5) + random.uniform(-2, 3)
                dia = baseline_dia + (days_since * 1.2) + random.uniform(-1, 2)
                glu = baseline_glu + (days_since * 4.0) + random.uniform(-3, 5)

                # Missed doses begin 2 days after deterioration start
                status = "MISSED" if day >= (deterioration_start_day + 2) else "TAKEN"
                reason = "FORGOTTEN_OR_STOCKOUT" if status == "MISSED" else None
            else:
                # Stable well-managed chronic profile
                sys = baseline_sys + random.uniform(-4, 4)
                dia = baseline_dia + random.uniform(-3, 3)
                glu = baseline_glu + random.uniform(-5, 5)
                status = "TAKEN"
                reason = None

            vitals_list.append({
                "recorded_at": curr_time,
                "systolic_bp": int(sys),
                "diastolic_bp": int(dia),
                "blood_glucose": round(glu, 1),
                "glucose_context": "FASTING",
                "pulse": 72 + random.randint(-4, 6)
            })

            adherence_records.append({
                "scheduled_time": curr_time,
                "status": status,
                "reason_for_miss": reason,
                "medication_name": "Amlodipine / Metformin"
            })

        return vitals_list, adherence_records, base_date, scheduled_visit

    @classmethod
    def run_objective_o2_benchmark(
        cls,
        num_patients: int = 50,
        scheduled_visit_day: int = 30,
        deterioration_start_day: int = 14
    ) -> Dict[str, Any]:
        """
        Backtests early deterioration detection across a simulated cohort.
        Verifies Objective O2 target: Deterioration flagged >= 7 days before next visit.
        """
        evaluated_cohort = []
        lead_times = []
        target_met_count = 0

        for idx in range(num_patients):
            pid = f"SYNTH-PATIENT-{idx+1:03d}"
            # 70% of cohort injected with deterioration, 30% stable controls
            will_deteriorate = (idx % 10) < 7

            vitals, adherence, base_date, scheduled_visit = cls.generate_patient_history(
                patient_id=pid,
                is_deteriorating=will_deteriorate,
                deterioration_start_day=deterioration_start_day,
                total_days=scheduled_visit_day
            )

            # Daily incremental evaluation
            flagged_day = None
            detected_risk: Optional[DeteriorationRisk] = None

            for day in range(1, scheduled_visit_day + 1):
                sub_vitals = vitals[:day]
                sub_adherence = adherence[:day]
                curr_eval_date = base_date + timedelta(days=day)

                risk = chronic_care_engine.evaluate_patient_deterioration(
                    vitals_list=sub_vitals,
                    adherence_records=sub_adherence,
                    next_scheduled_visit=scheduled_visit,
                    current_date=curr_eval_date
                )

                if risk.is_deteriorating and risk.risk_level in ["MODERATE", "HIGH", "CRITICAL"]:
                    flagged_day = day
                    detected_risk = risk
                    break

            if will_deteriorate:
                if flagged_day:
                    lead_time = scheduled_visit_day - flagged_day
                    lead_times.append(lead_time)
                    if lead_time >= 7:
                        target_met_count += 1
                else:
                    lead_times.append(0)

            evaluated_cohort.append({
                "patient_id": pid,
                "is_deteriorating_ground_truth": will_deteriorate,
                "flagged_at_day": flagged_day,
                "lead_time_days": (scheduled_visit_day - flagged_day) if flagged_day else None,
                "risk_level": detected_risk.risk_level if detected_risk else "LOW",
                "flags": detected_risk.flags if detected_risk else []
            })

        total_deteriorating = sum(1 for p in evaluated_cohort if p["is_deteriorating_ground_truth"])
        compliance_pct = round((target_met_count / total_deteriorating) * 100.0, 1) if total_deteriorating else 100.0
        avg_lead_time = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

        return {
            "objective": "O2 - Chronic Care Deterioration Early Warning",
            "target": "Deterioration flagged >= 7 days before next scheduled visit",
            "total_simulated_cohort": num_patients,
            "deteriorating_cohort_size": total_deteriorating,
            "successful_early_detections_ge_7_days": target_met_count,
            "compliance_percentage": compliance_pct,
            "average_lead_time_days": avg_lead_time,
            "objective_o2_passed": compliance_pct >= 95.0,
            "cohort_sample_results": evaluated_cohort[:5]
        }


cohort_benchmark = SyntheticCohortBenchmark()

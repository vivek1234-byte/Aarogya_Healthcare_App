import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app.services.surveillance_engine import surveillance_engine, AnomalyResult, OutbreakAlertPayload
from app.services.geo_clustering import VILLAGE_GEOMETRIES


class SyntheticOutbreakBenchmark:
    """
    Simulates multi-source syndromic streams and injects waterborne/vector-borne outbreaks.
    Benchmarks Objective O4: Early warning >= 3 days earlier than baseline with <= 1 false alarm/month.
    """

    @classmethod
    def generate_block_60day_stream(
        cls,
        outbreak_start_day: int = 25,
        target_villages: List[str] = None
    ) -> Dict[str, Dict[str, List[int]]]:
        """
        Generates 60 days of multi-source syndromic streams across villages in a block.
        Injects an acute diarrheal outbreak at outbreak_start_day.
        Streams: CLINIC_DIARRHEA, PHARMACY_ORS_SALES, SCHOOL_ABSENTEEISM.
        """
        target_villages = target_villages or ["VILL-UP-RAMPUR-01", "VILL-UP-SHIVPUR-02"]
        all_villages = list(VILLAGE_GEOMETRIES.keys())

        # village_id -> stream_name -> list of 60 daily integers
        dataset: Dict[str, Dict[str, List[int]]] = {
            vid: {"ACUTE_DIARRHEA": [], "PHARMACY_ORS_SALES": [], "SCHOOL_ABSENTEEISM": []}
            for vid in all_villages
        }

        random.seed(42) # Deterministic benchmark repeatability

        for day in range(1, 61):
            for vid in all_villages:
                # Normal baseline with Poisson/Poisson-like noise
                clinic_base = random.randint(0, 2)
                pharmacy_base = random.randint(2, 5)
                school_base = random.randint(3, 6)

                # Injected outbreak dynamics
                if vid in target_villages and day >= outbreak_start_day:
                    days_into_outbreak = day - outbreak_start_day
                    
                    # 1. Pharmacy OTC sales react FIRST (Day 0-2): Families buy ORS/anti-diarrheals before seeing doctor
                    pharmacy_surge = int(12 + (days_into_outbreak * 6) + random.randint(0, 4))
                    
                    # 2. School absenteeism rises immediately (Day 1-3)
                    school_surge = int(8 + (days_into_outbreak * 4) + random.randint(0, 3))
                    
                    # 3. Clinic formal visits LAG behind (peak at Day 4-7)
                    clinic_lag = int(2 + (days_into_outbreak * 2.2) + random.randint(0, 2))

                    dataset[vid]["ACUTE_DIARRHEA"].append(clinic_base + clinic_lag)
                    dataset[vid]["PHARMACY_ORS_SALES"].append(pharmacy_base + pharmacy_surge)
                    dataset[vid]["SCHOOL_ABSENTEEISM"].append(school_base + school_surge)
                else:
                    dataset[vid]["ACUTE_DIARRHEA"].append(clinic_base)
                    dataset[vid]["PHARMACY_ORS_SALES"].append(pharmacy_base)
                    dataset[vid]["SCHOOL_ABSENTEEISM"].append(school_base)

        return dataset

    @classmethod
    def run_objective_o4_benchmark(
        cls,
        outbreak_injection_day: int = 25,
        baseline_fixed_threshold: int = 10 # Conventional single-stream clinic threshold
    ) -> Dict[str, Any]:
        """
        Runs detection benchmark comparing ArogyaSaathi multi-signal fused anomaly detection
        against conventional single-stream public health clinic threshold.
        """
        data_streams = cls.generate_block_60day_stream(outbreak_start_day=outbreak_injection_day)
        base_date = datetime(2026, 6, 1)

        arogya_flagged_day = None
        conventional_flagged_day = None
        first_alert_payload: Optional[OutbreakAlertPayload] = None
        false_alarm_count_month1 = 0

        # Run day-by-day sliding window detection
        for day in range(15, 61): # Start at day 15 to establish 14-day baseline
            curr_date = base_date + timedelta(days=day)
            daily_evaluations: List[AnomalyResult] = []

            for vid, streams in data_streams.items():
                curr_signals = {
                    "ACUTE_DIARRHEA": streams["ACUTE_DIARRHEA"][day - 1],
                    "PHARMACY_ORS_SALES": streams["PHARMACY_ORS_SALES"][day - 1],
                    "SCHOOL_ABSENTEEISM": streams["SCHOOL_ABSENTEEISM"][day - 1]
                }
                historical_signals = {
                    "ACUTE_DIARRHEA": streams["ACUTE_DIARRHEA"][max(0, day - 15): day - 1],
                    "PHARMACY_ORS_SALES": streams["PHARMACY_ORS_SALES"][max(0, day - 15): day - 1],
                    "SCHOOL_ABSENTEEISM": streams["SCHOOL_ABSENTEEISM"][max(0, day - 15): day - 1]
                }

                eval_res = surveillance_engine.evaluate_village_day(
                    village_id=vid,
                    eval_date=curr_date,
                    current_signals=curr_signals,
                    historical_signals=historical_signals,
                    syndrome="ACUTE_DIARRHEAL_OUTBREAK"
                )
                daily_evaluations.append(eval_res)

            # Check for False Alarms prior to injection (Day 15 to 24)
            if day < outbreak_injection_day:
                cluster_test = surveillance_engine.detect_block_outbreak_cluster(daily_evaluations)
                if cluster_test:
                    false_alarm_count_month1 += 1

            # ArogyaSaathi Multi-Signal Detection Check
            if day >= outbreak_injection_day and arogya_flagged_day is None:
                alert = surveillance_engine.detect_block_outbreak_cluster(daily_evaluations)
                if alert:
                    arogya_flagged_day = day
                    first_alert_payload = alert

            # Conventional Baseline Check (Relies solely on clinic encounters > baseline_fixed_threshold)
            if day >= outbreak_injection_day and conventional_flagged_day is None:
                max_clinic_cases = max(streams["ACUTE_DIARRHEA"][day - 1] for streams in data_streams.values())
                if max_clinic_cases >= baseline_fixed_threshold:
                    conventional_flagged_day = day

        lead_time_days = (conventional_flagged_day - arogya_flagged_day) if (arogya_flagged_day and conventional_flagged_day) else 0
        objective_passed = (lead_time_days >= 3) and (false_alarm_count_month1 <= 1)

        return {
            "objective": "O4 - Community Outbreak Early Warning",
            "target": "Detect injected outbreaks >= 3 days earlier than baseline; false alarms <= 1 per month per block",
            "outbreak_injection_day": outbreak_injection_day,
            "arogyasaathi_detected_day": arogya_flagged_day,
            "conventional_baseline_detected_day": conventional_flagged_day,
            "lead_time_days_earlier": lead_time_days,
            "false_alarms_per_month_per_block": false_alarm_count_month1,
            "objective_o4_passed": objective_passed,
            "first_outbreak_alert": first_alert_payload.dict() if first_alert_payload else None
        }


outbreak_benchmark = SyntheticOutbreakBenchmark()

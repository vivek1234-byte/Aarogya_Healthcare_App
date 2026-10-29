import sys
import os
from datetime import datetime, timedelta

# Add backend directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.services.chronic_care import chronic_care_engine, ChronicPatientEvaluator
from app.services.voice_checkin import voice_checkin_parser
from app.services.synthetic_cohort import cohort_benchmark


def test_hypertension_trend_analysis():
    print("Testing Hypertension Trend & Velocity Analytics...")

    # 1. Stable patient profile
    stable_vitals = [
        {"recorded_at": datetime(2026, 1, 1), "systolic_bp": 122, "diastolic_bp": 78},
        {"recorded_at": datetime(2026, 1, 5), "systolic_bp": 125, "diastolic_bp": 80},
        {"recorded_at": datetime(2026, 1, 10), "systolic_bp": 120, "diastolic_bp": 82},
    ]
    res_stable = ChronicPatientEvaluator.calculate_bp_trend(stable_vitals)
    assert not res_stable["flags"], f"Stable profile should have no flags, got: {res_stable['flags']}"
    assert res_stable["average_systolic"] < 130

    # 2. Sustained Stage 2 Hypertension + Accelerating slope
    deteriorating_vitals = [
        {"recorded_at": datetime(2026, 1, 1), "systolic_bp": 128, "diastolic_bp": 82},
        {"recorded_at": datetime(2026, 1, 5), "systolic_bp": 134, "diastolic_bp": 85},
        {"recorded_at": datetime(2026, 1, 10), "systolic_bp": 144, "diastolic_bp": 92},
        {"recorded_at": datetime(2026, 1, 15), "systolic_bp": 152, "diastolic_bp": 96},
    ]
    res_det = ChronicPatientEvaluator.calculate_bp_trend(deteriorating_vitals)
    assert "SUSTAINED_STAGE_2_HYPERTENSION" in res_det["flags"]
    assert "ACCELERATING_SYSTOLIC_TREND" in res_det["flags"]
    assert res_det["slope_per_week"] > 0

    # 3. Hypertensive Crisis (>= 180 mmHg)
    crisis_vitals = [
        {"recorded_at": datetime(2026, 1, 1), "systolic_bp": 185, "diastolic_bp": 112}
    ]
    res_crisis = ChronicPatientEvaluator.calculate_bp_trend(crisis_vitals)
    assert "HYPERTENSIVE_CRISIS" in res_crisis["flags"]

    print("  [PASSED] Hypertension trends, velocity, and crisis detection verified.")


def test_diabetes_trend_analysis():
    print("Testing Diabetes Trend & Glycemic Analytics...")

    # 1. Hypoglycemia alert (< 70 mg/dL)
    hypo_vitals = [{"recorded_at": datetime(2026, 1, 1), "blood_glucose": 62.0, "glucose_context": "FASTING"}]
    res_hypo = ChronicPatientEvaluator.calculate_glucose_trend(hypo_vitals)
    assert "HYPOGLYCEMIA_ALERT" in res_hypo["flags"]

    # 2. Sustained hyperglycemia
    hyper_vitals = [
        {"recorded_at": datetime(2026, 1, 1), "blood_glucose": 185.0, "glucose_context": "FASTING"},
        {"recorded_at": datetime(2026, 1, 3), "blood_glucose": 192.0, "glucose_context": "FASTING"},
        {"recorded_at": datetime(2026, 1, 7), "blood_glucose": 210.0, "glucose_context": "FASTING"},
    ]
    res_hyper = ChronicPatientEvaluator.calculate_glucose_trend(hyper_vitals)
    assert "SUSTAINED_HYPERGLYCEMIA" in res_hyper["flags"]
    assert res_hyper["average_glucose"] > 190.0

    print("  [PASSED] Glycemic trends, hypoglycemia, and sustained hyperglycemia verified.")


def test_medication_adherence_scoring():
    print("Testing Medication Adherence Scoring & Dropout Detection...")

    # Profile with 3 consecutive missed doses
    records = [
        {"scheduled_time": datetime(2026, 1, 1), "status": "TAKEN"},
        {"scheduled_time": datetime(2026, 1, 2), "status": "TAKEN"},
        {"scheduled_time": datetime(2026, 1, 3), "status": "MISSED", "reason": "Forgot"},
        {"scheduled_time": datetime(2026, 1, 4), "status": "MISSED", "reason": "Side effect"},
        {"scheduled_time": datetime(2026, 1, 5), "status": "MISSED", "reason": "Ran out of pills"},
    ]
    res_adh = ChronicPatientEvaluator.calculate_adherence_score(records)
    assert res_adh["consecutive_missed"] == 3
    assert "CRITICAL_MEDICATION_DROPOUT" in res_adh["flags"]
    assert res_adh["adherence_rate_pct"] == 40.0

    print("  [PASSED] Adherence rate and critical medication dropout verified.")


def test_voice_checkin_speech_parser():
    print("Testing Conversational Voice Check-in Parser (Hindi & English)...")

    # Hindi sample: BP + Taken pill
    h1 = "आज सुबह बीपी 145 बटा 92 आया था और गोली ले ली थी"
    res1 = voice_checkin_parser.parse_checkin_speech(h1)
    assert res1.systolic_bp == 145
    assert res1.diastolic_bp == 92
    assert res1.adherence_status == "TAKEN"

    # Hindi sample: Sugar + Missed pill due to stockout
    h2 = "दवाई खत्म हो गई थी तो नहीं ली, खाली पेट शुगर 168 था"
    res2 = voice_checkin_parser.parse_checkin_speech(h2)
    assert res2.blood_glucose == 168.0
    assert res2.glucose_context == "FASTING"
    assert res2.adherence_status == "MISSED"
    assert res2.miss_reason == "STOCKOUT_OR_SUPPLY_GAP"

    # English sample: BP + Missed pill forgotten
    e1 = "Blood pressure was 155 by 95 today, forgot to take morning pill"
    res3 = voice_checkin_parser.parse_checkin_speech(e1)
    assert res3.systolic_bp == 155
    assert res3.diastolic_bp == 95
    assert res3.adherence_status == "MISSED"
    assert res3.miss_reason == "FORGOTTEN"

    print("  [PASSED] Conversational speech parsing for vitals and adherence verified.")


def test_synthetic_cohort_objective_o2():
    print("Testing Synthea-Style Simulated Cohort Benchmark (Objective O2)...")
    print("  Evaluating target: Deterioration flagged >= 7 days before next visit...")

    # Run benchmark on simulated cohort of 50 patients
    benchmark_result = cohort_benchmark.run_objective_o2_benchmark(
        num_patients=50,
        scheduled_visit_day=30,
        deterioration_start_day=14
    )

    compliance = benchmark_result["compliance_percentage"]
    avg_lead_time = benchmark_result["average_lead_time_days"]

    print(f"  Simulation Results:")
    print(f"    - Total Simulated Cohort: {benchmark_result['total_simulated_cohort']}")
    print(f"    - Deteriorating Cohort Size: {benchmark_result['deteriorating_cohort_size']}")
    print(f"    - Early Detections (>= 7 days lead time): {benchmark_result['successful_early_detections_ge_7_days']}")
    print(f"    - Compliance Percentage: {compliance}%")
    print(f"    - Average Early Warning Lead Time: {avg_lead_time} days before visit")

    assert benchmark_result["objective_o2_passed"] is True, f"Objective O2 failed: {compliance}% < 95%"
    assert avg_lead_time >= 7.0, f"Average lead time was {avg_lead_time} days (< 7 days target)"

    print("  [PASSED] Objective O2 mathematically verified on simulated chronic cohort.")


if __name__ == "__main__":
    print("=" * 65)
    print("ArogyaSaathi Backend Phase 3 Verification Suite")
    print("Chronic Care Engine, Trend Analytics & Objective O2 Benchmark")
    print("=" * 65)
    test_hypertension_trend_analysis()
    test_diabetes_trend_analysis()
    test_medication_adherence_scoring()
    test_voice_checkin_speech_parser()
    test_synthetic_cohort_objective_o2()
    print("=" * 65)
    print("ALL PHASE 3 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 65)

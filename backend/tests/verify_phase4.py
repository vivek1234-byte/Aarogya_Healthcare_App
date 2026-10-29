import sys
import os
from datetime import datetime, timedelta

# Add backend directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app.services.geo_clustering import geo_cluster_service, VILLAGE_GEOMETRIES
from app.services.surveillance_engine import surveillance_engine
from app.services.synthetic_outbreak import outbreak_benchmark


def test_geospatial_clustering_and_geojson():
    print("Testing Geospatial Clustering & GeoJSON Polygon Generation...")

    # 1. Verify village reference database
    villages = list(VILLAGE_GEOMETRIES.keys())
    assert len(villages) >= 5, "Expected at least 5 rural block villages"

    # 2. Compute bounding polygon across affected cluster (Rampur + Shivpur)
    cluster_villages = ["VILL-UP-RAMPUR-01", "VILL-UP-SHIVPUR-02"]
    geom = geo_cluster_service.compute_cluster_bounding_polygon(cluster_villages)
    assert geom["type"] == "Polygon"
    coords = geom["coordinates"][0]
    assert len(coords) == 5, "Bounding polygon must form a closed ring (5 coordinates)"
    assert coords[0] == coords[-1], "Polygon start coordinate must equal end coordinate"

    # 3. Generate GeoJSON village map feed
    sample_risks = {
        "VILL-UP-RAMPUR-01": "OUTBREAK",
        "VILL-UP-SHIVPUR-02": "WARNING",
        "VILL-UP-KALYANPUR-03": "WATCH"
    }
    feed = geo_cluster_service.generate_village_map_geojson(sample_risks)
    assert feed["type"] == "FeatureCollection"
    assert len(feed["features"]) >= 5

    rampur_feat = next(f for f in feed["features"] if f["id"] == "VILL-UP-RAMPUR-01")
    assert rampur_feat["properties"]["risk_level"] == "OUTBREAK"
    assert rampur_feat["properties"]["fill_color"] == "#F44336" # Red

    print("  [PASSED] Geospatial cluster polygon and GeoJSON map feed verified.")


def test_syndromic_anomaly_detection_engine():
    print("Testing Multi-Stream Syndromic Anomaly Detection Engine...")

    # 1. Normal baseline day (no outbreak)
    normal_signals = {"ACUTE_DIARRHEA": 1, "PHARMACY_ORS_SALES": 3, "SCHOOL_ABSENTEEISM": 4}
    normal_history = {
        "ACUTE_DIARRHEA": [1, 2, 0, 1, 2, 1, 0, 2, 1, 1],
        "PHARMACY_ORS_SALES": [3, 4, 2, 5, 3, 4, 3, 2, 4, 3],
        "SCHOOL_ABSENTEEISM": [4, 5, 3, 6, 4, 5, 4, 3, 5, 4]
    }
    res_normal = surveillance_engine.evaluate_village_day(
        village_id="VILL-UP-RAMPUR-01",
        eval_date=datetime(2026, 6, 15),
        current_signals=normal_signals,
        historical_signals=normal_history
    )
    assert res_normal.is_anomaly is False
    assert res_normal.risk_level == "NORMAL"
    assert res_normal.z_score < 1.5

    # 2. Outbreak day: Multi-stream concurrent spike (ORS sales x6, absenteeism x4, clinic diarrhea x5)
    outbreak_signals = {"ACUTE_DIARRHEA": 9, "PHARMACY_ORS_SALES": 24, "SCHOOL_ABSENTEEISM": 18}
    res_outbreak = surveillance_engine.evaluate_village_day(
        village_id="VILL-UP-RAMPUR-01",
        eval_date=datetime(2026, 6, 26),
        current_signals=outbreak_signals,
        historical_signals=normal_history
    )
    assert res_outbreak.is_anomaly is True
    assert res_outbreak.risk_level in ["WARNING", "OUTBREAK"]
    assert res_outbreak.z_score >= 2.5
    assert res_outbreak.confidence >= 0.65

    # 3. Detect block outbreak cluster
    cluster_alert = surveillance_engine.detect_block_outbreak_cluster([res_outbreak])
    assert cluster_alert is not None
    assert "VILL-UP-RAMPUR-01" in cluster_alert.affected_villages
    assert cluster_alert.cluster_geom["type"] == "Polygon"
    assert len(cluster_alert.recommended_interventions) >= 3

    print("  [PASSED] Multi-stream anomaly detection and cluster alert generation verified.")


def test_synthetic_outbreak_benchmark_objective_o4():
    print("Testing Synthea-Style Outbreak Injection Benchmark (Objective O4)...")
    print("  Evaluating target: Detect injected outbreaks >= 3 days earlier than baseline; false alarms <= 1/month/block...")

    benchmark_res = outbreak_benchmark.run_objective_o4_benchmark(
        outbreak_injection_day=25,
        baseline_fixed_threshold=10
    )

    injection_day = benchmark_res["outbreak_injection_day"]
    arogya_day = benchmark_res["arogyasaathi_detected_day"]
    base_day = benchmark_res["conventional_baseline_detected_day"]
    lead_time = benchmark_res["lead_time_days_earlier"]
    false_alarms = benchmark_res["false_alarms_per_month_per_block"]

    print("  Simulation Results:")
    print(f"    - Injected Outbreak Day: Day {injection_day}")
    print(f"    - ArogyaSaathi Multi-Signal Detection: Day {arogya_day}")
    print(f"    - Conventional Clinic Baseline Detection: Day {base_day}")
    print(f"    - Early Warning Lead Time: {lead_time} days earlier than conventional baseline")
    print(f"    - Pre-Outbreak False Alarms: {false_alarms} / month / block")
    print(f"    - Objective O4 Status: {'PASSED' if benchmark_res['objective_o4_passed'] else 'FAILED'}")

    assert benchmark_res["objective_o4_passed"] is True, "Objective O4 benchmark failed"
    assert lead_time >= 3, f"Lead time {lead_time} is less than required 3 days"
    assert false_alarms <= 1, f"False alarm rate {false_alarms} exceeded 1/month/block limit"
    assert benchmark_res["first_outbreak_alert"] is not None

    print("  [PASSED] Objective O4 mathematically verified on simulated village outbreak.")


if __name__ == "__main__":
    print("=" * 65)
    print("ArogyaSaathi Backend Phase 4 Verification Suite")
    print("Syndromic Surveillance, GeoJSON Mapping & Objective O4 Benchmark")
    print("=" * 65)
    test_geospatial_clustering_and_geojson()
    test_syndromic_anomaly_detection_engine()
    test_synthetic_outbreak_benchmark_objective_o4()
    print("=" * 65)
    print("ALL PHASE 4 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 65)
